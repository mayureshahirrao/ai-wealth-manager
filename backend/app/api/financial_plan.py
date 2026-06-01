"""
financial_plan.py — Financial plan generation and retrieval endpoints.

Implements:
- POST /api/financial-plan/generate  — AI-generated comprehensive financial plan
- GET  /api/financial-plan/{id}      — Retrieve saved plan for a client
"""

import uuid
from datetime import datetime, timezone, date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.role_guard import require_rm, require_rm_or_compliance, CurrentUser
from app.core.base_response import success_response, APIResponse
from app.core.logging_config import get_logger
from app.database.models import Client, Portfolio, Goal, ComplianceDocument
from app.database.base_model import ComplianceDocType
from app.financial.goal_engine import GoalAssessment
from app.financial.tax_calculator import compare_tax_regimes
from app.financial.currency_formatter import format_inr
from app.ai.claude_client import get_claude_client
from app.database.transaction import get_db

logger = get_logger(__name__)
router = APIRouter(prefix="/api/financial-plan", tags=["financial-plan"])


class GeneratePlanRequest(BaseModel):
    client_id: str
    advisor_notes: str = Field(default="", max_length=1000,
                               description="Optional RM notes to include in the plan")
    target_retirement_age: int = Field(default=60, ge=50, le=80)
    desired_monthly_income: float = Field(default=100_000, ge=10_000,
                                          description="Desired monthly income at retirement in today's ₹")


# ─── Generate Financial Plan ──────────────────────────────────────────────────

@router.post("/generate")
async def generate_financial_plan(
    payload: GeneratePlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_rm),
) -> APIResponse:
    """
    Generate a comprehensive AI-powered financial plan for a client.

    Uses Claude to analyse the client's complete financial picture and produce
    a structured plan covering: portfolio review, goal roadmap, tax strategy,
    retirement projection, and next steps.

    The plan is saved to the compliance_documents table for audit purposes.
    """
    try:
        cid = uuid.UUID(payload.client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client_id")

    # Load client data
    client_result = await db.execute(
        select(Client)
        .where(Client.id == cid)
        .options(selectinload(Client.goals), selectinload(Client.alerts))
    )
    client = client_result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    portfolio_result = await db.execute(
        select(Portfolio)
        .where(Portfolio.client_id == cid)
        .options(selectinload(Portfolio.holdings))
    )
    portfolio = portfolio_result.scalar_one_or_none()

    # Build comprehensive context
    context = _build_plan_context(client, portfolio, payload)

    # Generate plan via Claude
    claude = get_claude_client()

    system = """You are a senior SEBI-registered investment adviser generating a formal financial plan.
The plan must be:
- Specific: use actual numbers from the client data provided
- Actionable: every recommendation has a concrete next step
- Compliant: follow SEBI IA Regulations 2013 Clause 19 (documented rationale for each recommendation)
- Indian context: use Indian tax laws (Budget 2024), instruments (MF, NPS, PPF, ELSS), and ₹ formatting"""

    prompt = f"""Generate a comprehensive financial plan for the following client:

{context}

Structure the plan with these sections:

# Financial Plan — {client.name}
*Generated: {datetime.now(timezone.utc).strftime('%B %d, %Y')}*

## 1. Executive Summary
Brief overview of the client's financial position and key recommendations.

## 2. Portfolio Review
Current portfolio performance, asset allocation assessment, and rebalancing recommendations.
Include XIRR vs benchmark comparison and specific holding-level observations.

## 3. Goal Roadmap
For each goal: current status, projected outcome, gap analysis, and specific SIP recommendation.
Include a priority-ordered action plan.

## 4. Tax Optimisation Strategy
Old vs New regime recommendation with calculated savings.
LTCG harvesting opportunity if applicable.
Specific deduction strategies for their income level.

## 5. Retirement Projection
Required corpus calculation (inflation-adjusted).
Current trajectory vs required trajectory.
Additional monthly savings needed.
Post-retirement income strategy (SWP, SCSS, NPS annuity).

## 6. Risk Assessment
Current risk profile suitability.
Asset allocation adequacy for their age and goals.
Insurance gap (term life and health) if identifiable from data.

## 7. Recommended Action Plan
Numbered list of specific actions, prioritised by urgency and impact.
Include timeframes for each action.

## 8. Important Disclosures
Include SEBI disclaimer and Clause 19 rationale statement.

Be specific with numbers. Use Indian currency format (₹ X.XX Lakh / ₹ X.XX Cr).
This plan should be ready to present to the client."""

    response = await claude.complete(
        messages=[{"role": "user", "content": prompt}],
        system=system,
        max_tokens=3000,
        temperature=0.1,
    )

    plan_text = response.content[0].text if response.content else "Plan generation failed."

    # Save to compliance_documents for audit trail
    doc = ComplianceDocument(
        client_id=cid,
        doc_type=ComplianceDocType.SUITABILITY_ATTESTATION,
        content=plan_text,
        generated_by=f"ai:claude:{current_user.email}",
        reviewed_by=None,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    logger.info(
        "financial_plan_generated",
        client_id=payload.client_id,
        doc_id=str(doc.id),
        tokens=response.usage.output_tokens,
        rm=current_user.email,
    )

    return success_response(data={
        "client_id": payload.client_id,
        "client_name": client.name,
        "plan_id": str(doc.id),
        "plan": plan_text,
        "generated_at": doc.created_at.isoformat(),
        "generated_by": doc.generated_by,
        "tokens_used": response.usage.output_tokens,
    })


# ─── Get Saved Plan ───────────────────────────────────────────────────────────

@router.get("/{client_id}")
async def get_financial_plan(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_rm_or_compliance),
) -> APIResponse:
    """Retrieve the most recent financial plan for a client."""
    try:
        cid = uuid.UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client_id")

    result = await db.execute(
        select(ComplianceDocument)
        .where(
            ComplianceDocument.client_id == cid,
            ComplianceDocument.doc_type == ComplianceDocType.SUITABILITY_ATTESTATION,
        )
        .order_by(ComplianceDocument.created_at.desc())
        .limit(1)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        return success_response(data={
            "client_id": client_id,
            "plan": None,
            "message": "No financial plan generated yet. Use POST /api/financial-plan/generate.",
        })

    return success_response(data={
        "client_id": client_id,
        "plan_id": str(doc.id),
        "plan": doc.content,
        "generated_at": doc.created_at.isoformat(),
        "generated_by": doc.generated_by,
        "reviewed_by": doc.reviewed_by,
    })


# ─── Context Builder ──────────────────────────────────────────────────────────

def _build_plan_context(client, portfolio, payload: GeneratePlanRequest) -> str:
    """Build a comprehensive context string for the financial plan prompt."""
    today = date.today()
    lines = [
        "=== CLIENT PROFILE ===",
        f"Name: {client.name}",
        f"Age: {client.age} | Risk Profile: {client.risk_profile.value if hasattr(client.risk_profile, 'value') else client.risk_profile}",
        f"Annual Income: {format_inr(client.annual_income or 0)} | Tax Regime: {client.tax_regime.value.upper() if hasattr(client.tax_regime, 'value') else client.tax_regime}",
        f"KYC Status: {'Verified ✓' if client.kyc_verified else 'NOT VERIFIED ⚠'}",
        f"Target Retirement Age: {payload.target_retirement_age} | Desired Monthly Income at Retirement: {format_inr(payload.desired_monthly_income)}",
    ]

    if payload.advisor_notes:
        lines += ["", f"RM Notes: {payload.advisor_notes}"]

    if portfolio:
        xirr_pct = (portfolio.xirr or 0) * 100
        bench_pct = (portfolio.benchmark_xirr or 0) * 100
        unrealised_gain = portfolio.current_value - portfolio.total_invested
        gain_pct = (unrealised_gain / portfolio.total_invested * 100) if portfolio.total_invested > 0 else 0

        lines += [
            "",
            "=== PORTFOLIO ===",
            f"Total Invested: {format_inr(portfolio.total_invested)}",
            f"Current Value: {format_inr(portfolio.current_value)} (Gain: {gain_pct:+.1f}%)",
            f"XIRR: {xirr_pct:.2f}% | Nifty 50 Benchmark: {bench_pct:.2f}% | Outperformance: {xirr_pct - bench_pct:+.2f}%",
        ]

        if portfolio.holdings:
            by_class: dict = {}
            for h in portfolio.holdings:
                ac = h.asset_class.value if hasattr(h.asset_class, "value") else str(h.asset_class)
                by_class[ac] = by_class.get(ac, 0) + h.current_value
            alloc = {k: f"{v / portfolio.current_value * 100:.1f}%" for k, v in by_class.items()}
            lines.append(f"Asset Allocation: {alloc}")

            lines.append("Holdings:")
            for h in sorted(portfolio.holdings, key=lambda x: x.current_value, reverse=True):
                gain = h.current_value - h.invested_amount
                gain_pct_h = (gain / h.invested_amount * 100) if h.invested_amount > 0 else 0
                sip_info = f" | SIP: {format_inr(h.sip_amount)}/month" if h.has_sip_active and h.sip_amount else ""
                lines.append(
                    f"  - {h.scheme_name}: {format_inr(h.current_value)} ({gain_pct_h:+.1f}%){sip_info}"
                )

    if client.goals:
        lines += ["", "=== GOALS ==="]
        for goal in client.goals:
            years = max(0, goal.target_year - today.year)
            if years > 0:
                assessment = GoalAssessment(
                    goal_type=goal.goal_type.value if hasattr(goal.goal_type, "value") else str(goal.goal_type),
                    target_amount=goal.target_amount,
                    target_date=date(goal.target_year, 12, 31),
                    current_corpus=goal.current_corpus,
                    monthly_sip=goal.monthly_sip,
                    years_remaining=years,
                )
                lines.append(
                    f"  {goal.goal_name} ({goal.target_year}):\n"
                    f"    Target: {format_inr(goal.target_amount)} | Corpus: {format_inr(goal.current_corpus)} | "
                    f"SIP: {format_inr(goal.monthly_sip)}/month\n"
                    f"    Projected: {format_inr(assessment.projected_corpus)} | "
                    f"Shortfall: {format_inr(assessment.shortfall)} | "
                    f"Feasibility: {assessment.feasibility_score}/100 ({assessment.status})"
                )

    if client.annual_income:
        tax_data = compare_tax_regimes(client.annual_income, age=client.age or 35)
        lines += [
            "",
            "=== TAX ANALYSIS ===",
            f"New Regime Tax: {format_inr(tax_data['new_regime']['total_tax'])} ({tax_data['new_regime']['effective_rate_pct']}%)",
            f"Old Regime Tax: {format_inr(tax_data['old_regime']['total_tax'])} ({tax_data['old_regime']['effective_rate_pct']}%)",
            f"Recommended Regime: {tax_data['recommended_regime']} (saves {format_inr(tax_data['tax_savings_if_switching'])})",
        ]

    active_alerts = [a for a in client.alerts if not a.is_resolved]
    if active_alerts:
        lines += ["", "=== ACTIVE COMPLIANCE ALERTS ==="]
        for alert in active_alerts:
            priority = alert.priority.value if hasattr(alert.priority, "value") else str(alert.priority)
            lines.append(f"  [{priority.upper()}] {alert.message}")

    return "\n".join(lines)
