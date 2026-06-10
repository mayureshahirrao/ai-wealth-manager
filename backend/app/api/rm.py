"""
rm.py — Relationship Manager endpoints.

Implements:
- GET /api/rm/next-actions       — prioritised action queue across all clients
- GET /api/rm/meeting-prep/{id}  — AI-generated meeting brief via Claude
- GET /api/rm/alerts/{id}        — client-level alerts
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.role_guard import require_rm, require_rm_or_compliance, CurrentUser
from app.core.base_response import success_response, APIResponse
from app.core.logging_config import get_logger
from app.database.models import Client, Portfolio, Holding, Goal, Alert
from app.database.base_model import AlertPriority
from app.database.transaction import get_db
from app.financial.goal_engine import GoalAssessment
from app.financial.currency_formatter import format_inr
from app.ai.claude_client import get_claude_client

logger = get_logger(__name__)
router = APIRouter(prefix="/api/rm", tags=["rm"])

# Action priority order for sorting
_PRIORITY_ORDER = {
    AlertPriority.CRITICAL: 0,
    AlertPriority.HIGH: 1,
    AlertPriority.MEDIUM: 2,
    AlertPriority.LOW: 3,
}
REVIEW_OVERDUE_DAYS = 90   # Flag clients not reviewed in 90+ days


# ─── Next Best Actions ────────────────────────────────────────────────────────

@router.get("/next-actions")
async def get_next_actions(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_rm_or_compliance),
) -> APIResponse:
    """
    Returns a prioritised action queue across all clients.

    Sources:
    - Active compliance alerts (CONCENTRATION_RISK, REVIEW_OVERDUE, etc.)
    - Clients not reviewed in 90+ days (auto-generated action)
    - Goals with feasibility score < 40 (at-risk goals)
    """
    today = datetime.now(timezone.utc)
    review_threshold = today - timedelta(days=REVIEW_OVERDUE_DAYS)

    # Load all clients with their alerts and goals
    clients_result = await db.execute(
        select(Client)
        .options(
            selectinload(Client.alerts),
            selectinload(Client.goals),
        )
        .order_by(Client.name)
    )
    clients = clients_result.scalars().all()

    actions = []

    for client in clients:
        client_id_str = str(client.id)
        client_name = client.name

        # ── Active compliance alerts ──────────────────────────────────────────
        for alert in client.alerts:
            if alert.is_resolved:
                continue
            actions.append({
                "client_id": client_id_str,
                "client_name": client_name,
                "action_type": alert.alert_type.value if hasattr(alert.alert_type, "value") else str(alert.alert_type),
                "priority": alert.priority.value if hasattr(alert.priority, "value") else str(alert.priority),
                "priority_order": _PRIORITY_ORDER.get(alert.priority, 4),
                "message": alert.message,
                "recommended_action": _get_recommended_action(alert.alert_type),
                "source": "compliance_alert",
                "alert_id": str(alert.id),
            })

        # ── Overdue review check ──────────────────────────────────────────────
        if client.last_review_date is None or client.last_review_date < review_threshold:
            days_since = (
                (today - client.last_review_date).days
                if client.last_review_date else None
            )
            # Don't duplicate if already in alerts
            already_flagged = any(
                a["action_type"] == "REVIEW_OVERDUE" and a["client_id"] == client_id_str
                for a in actions
            )
            if not already_flagged:
                actions.append({
                    "client_id": client_id_str,
                    "client_name": client_name,
                    "action_type": "REVIEW_OVERDUE",
                    "priority": "high",
                    "priority_order": 1,
                    "message": (
                        f"Client not reviewed in {days_since} days."
                        if days_since else "Client has never been reviewed."
                    ),
                    "recommended_action": "Schedule annual review meeting. Discuss portfolio performance, goal progress, and risk profile suitability.",
                    "source": "auto_detected",
                    "alert_id": None,
                })

        # ── At-risk goals ─────────────────────────────────────────────────────
        from datetime import date
        today_date = date.today()
        for goal in client.goals:
            years_remaining = max(0, goal.target_year - today_date.year)
            if years_remaining == 0:
                continue
            assessment = GoalAssessment(
                goal_type=goal.goal_type.value if hasattr(goal.goal_type, "value") else str(goal.goal_type),
                target_amount=goal.target_amount,
                target_date=date(goal.target_year, 12, 31),
                current_corpus=goal.current_corpus,
                monthly_sip=goal.monthly_sip,
                years_remaining=years_remaining,
            )
            if assessment.feasibility_score < 40:
                actions.append({
                    "client_id": client_id_str,
                    "client_name": client_name,
                    "action_type": "GOAL_AT_RISK",
                    "priority": "high",
                    "priority_order": 1,
                    "message": (
                        f"Goal '{goal.goal_name}' is at risk — "
                        f"feasibility {assessment.feasibility_score}/100. "
                        f"Shortfall: {format_inr(assessment.shortfall)}."
                    ),
                    "recommended_action": (
                        f"Increase SIP by {format_inr(assessment.additional_sip_needed)}/month "
                        f"or extend timeline to meet {goal.goal_name} target."
                    ),
                    "source": "goal_analysis",
                    "alert_id": None,
                })

    # Sort by priority then client name
    actions.sort(key=lambda x: (x["priority_order"], x["client_name"]))

    # Remove internal sort key before returning
    for a in actions:
        a.pop("priority_order", None)

    return success_response(data={
        "total_actions": len(actions),
        "actions": actions,
        "generated_at": today.isoformat(),
    })


def _get_recommended_action(alert_type) -> str:
    """Map alert type to a human-readable recommended action."""
    type_val = alert_type.value if hasattr(alert_type, "value") else str(alert_type)
    recommendations = {
        "CONCENTRATION_RISK": "Review asset allocation. Rebalance portfolio to reduce single-asset concentration below 20%.",
        "CRYPTO_OVERWEIGHT": "Discuss crypto exposure limits. Recommend reducing VDA allocation to below 20%.",
        "NO_NOMINEE": "Assist client in adding nominee to all investment accounts and folios.",
        "KYC_EXPIRED": "Initiate KYC refresh process. SEBI requires renewal every 24 months.",
        "ESTATE_GAP": "Recommend client consult estate planning expert. Will and trust review required.",
        "REVIEW_OVERDUE": "Schedule annual review meeting. Discuss portfolio performance, goal progress, and risk profile.",
        "NPS_NOT_OPENED": "Recommend opening NPS Tier I account for additional ₹50,000 tax benefit (80CCD(1B)).",
        "FD_OVERWEIGHT": "Discuss inflation-adjusted returns on FDs. Consider partial shift to debt MFs or balanced funds.",
        "AI_LOW_CONFIDENCE": "AI recommendation confidence below threshold. Escalate to senior RM for manual review.",
        "GOAL_AT_RISK": "Review goal SIP amounts. Increase contributions or adjust timeline.",
    }
    return recommendations.get(type_val, "Review and take appropriate action.")


# ─── Meeting Prep ─────────────────────────────────────────────────────────────

@router.get("/meeting-prep/{client_id}")
async def get_meeting_prep(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_rm_or_compliance),
) -> APIResponse:
    """
    Generate an AI-powered meeting preparation brief for a client.

    Uses Claude to synthesise portfolio data, goal progress, alerts, and tax
    position into a structured meeting agenda and talking points.
    """
    try:
        cid = uuid.UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client_id")

    # Load full client data
    client_result = await db.execute(
        select(Client)
        .where(Client.id == cid)
        .options(
            selectinload(Client.goals),
            selectinload(Client.alerts),
        )
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

    # Build context for Claude
    context = _build_meeting_context(client, portfolio)

    # Generate meeting brief via Claude
    claude = get_claude_client()
    prompt = f"""You are a senior wealth management assistant preparing a relationship manager for a client meeting.

{context}

Generate a concise, professional meeting preparation brief with the following sections:

1. **Client Snapshot** — Key facts at a glance (age, risk profile, AUM, XIRR, tax regime)
2. **Portfolio Health** — Performance vs benchmark, asset allocation, top holdings
3. **Goal Progress** — Status of each goal with feasibility scores
4. **Compliance Alerts** — Any active alerts requiring discussion
5. **Meeting Agenda** — 4-5 bullet points, prioritised by urgency
6. **Talking Points** — Specific data-backed points to raise with the client
7. **Recommended Actions** — 2-3 concrete actions to propose in the meeting

Keep the tone professional and factual. Use Indian currency formatting (₹, Lakhs, Crores).
Be concise — this is a briefing document, not a report."""

    response = await claude.complete(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.2,
    )

    brief_text = response.content[0].text if response.content else "Unable to generate brief."

    logger.info(
        "meeting_prep_generated",
        client_id=client_id,
        tokens=response.usage.output_tokens,
    )

    return success_response(data={
        "client_id": client_id,
        "client_name": client.name,
        "brief": brief_text,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "context_summary": {
            "aum": round(portfolio.current_value) if portfolio else 0,
            "active_alerts": sum(1 for a in client.alerts if not a.is_resolved),
            "goals_count": len(client.goals),
        },
    })


def _build_meeting_context(client, portfolio) -> str:
    """Build a structured context string from client data for Claude."""
    from datetime import date
    today = date.today()
    lines = [
        f"CLIENT: {client.name}",
        f"Age: {client.age} | Risk Profile: {client.risk_profile.value if hasattr(client.risk_profile, 'value') else client.risk_profile}",
        f"Tax Regime: {client.tax_regime.value.upper() if hasattr(client.tax_regime, 'value') else client.tax_regime} | Annual Income: {format_inr(client.annual_income or 0)}",
        f"KYC: {'Verified' if client.kyc_verified else 'NOT VERIFIED'}",
        "",
    ]

    if portfolio:
        xirr = (portfolio.xirr or 0) * 100
        bench = (portfolio.benchmark_xirr or 0) * 100
        outperf = xirr - bench
        lines += [
            "PORTFOLIO:",
            f"  AUM: {format_inr(portfolio.current_value)} | Invested: {format_inr(portfolio.total_invested)}",
            f"  XIRR: {xirr:.1f}% | Benchmark: {bench:.1f}% | Outperformance: {outperf:+.1f}%",
        ]
        if portfolio.holdings:
            by_class: dict = {}
            for h in portfolio.holdings:
                ac = h.asset_class.value if hasattr(h.asset_class, "value") else str(h.asset_class)
                by_class[ac] = by_class.get(ac, 0) + h.current_value
            alloc = {k: round(v / portfolio.current_value * 100, 1) for k, v in by_class.items()}
            lines.append(f"  Allocation: {alloc}")
        lines.append("")

    if client.goals:
        lines.append("GOALS:")
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
                    f"  {goal.goal_name}: Target {format_inr(goal.target_amount)} in {years} years | "
                    f"Feasibility: {assessment.feasibility_score}/100 | Status: {assessment.status}"
                )
        lines.append("")

    active_alerts = [a for a in client.alerts if not a.is_resolved]
    if active_alerts:
        lines.append("ACTIVE ALERTS:")
        for alert in active_alerts:
            priority = alert.priority.value if hasattr(alert.priority, "value") else str(alert.priority)
            lines.append(f"  [{priority.upper()}] {alert.message}")
        lines.append("")

    return "\n".join(lines)


# ─── Client Alerts ────────────────────────────────────────────────────────────

@router.get("/alerts/{client_id}")
async def get_client_alerts(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_rm_or_compliance),
) -> APIResponse:
    """Get active alerts for a specific client."""
    try:
        cid = uuid.UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client_id")

    client_result = await db.execute(select(Client).where(Client.id == cid))
    client = client_result.scalar_one_or_none()
    if not client:
        return success_response(data=[])

    result = await db.execute(
        select(Alert)
        .where(Alert.client_id == cid, Alert.is_resolved == False)
        .order_by(Alert.created_at.desc())
    )
    alerts = result.scalars().all()

    return success_response(data=[
        {
            "alert_id": str(a.id),
            "alert_type": a.alert_type.value if hasattr(a.alert_type, "value") else str(a.alert_type),
            "priority": a.priority.value if hasattr(a.priority, "value") else str(a.priority),
            "message": a.message,
            "recommended_action": _get_recommended_action(a.alert_type),
            "created_at": a.created_at.isoformat(),
        }
        for a in alerts
    ])
