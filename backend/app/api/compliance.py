"""
compliance.py — Compliance officer endpoints.

Implements:
- GET  /api/compliance/audit-log        — paginated AI audit log with filters
- GET  /api/compliance/risk-alerts      — unresolved alerts with client names
- PATCH /api/compliance/resolve-alert/{id} — mark alert resolved
- POST /api/compliance/generate-doc    — SEBI disclosure document via Claude
- GET  /api/compliance/ai-governance   — confidence, tool usage, compliance stats
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.role_guard import require_compliance, require_rm_or_compliance, CurrentUser
from app.core.base_response import success_response, APIResponse
from app.core.logging_config import get_logger
from app.database.models import AIAuditLog, Alert, Client, ComplianceDocument
from app.database.base_model import AlertPriority, ComplianceDocType
from app.database.transaction import get_db
from app.ai.claude_client import get_claude_client

logger = get_logger(__name__)
router = APIRouter(prefix="/api/compliance", tags=["compliance"])


# ─── Audit Log ────────────────────────────────────────────────────────────────

@router.get("/audit-log")
async def get_audit_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    client_id: Optional[str] = Query(None, description="Filter by client UUID"),
    tool_name: Optional[str] = Query(None, description="Filter by tool name"),
    sebi_compliant: Optional[bool] = Query(None, description="Filter by compliance status"),
    days: int = Query(30, ge=1, le=365, description="Look-back window in days"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_rm_or_compliance),
) -> APIResponse:
    """
    Paginated AI audit log with optional filters.
    Required by SEBI IA Regulations for 5-year record keeping.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Build filter conditions
    filters = [AIAuditLog.created_at >= since]

    if client_id:
        try:
            filters.append(AIAuditLog.client_id == uuid.UUID(client_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid client_id format")

    if tool_name:
        filters.append(AIAuditLog.tool_name == tool_name)

    if sebi_compliant is not None:
        filters.append(AIAuditLog.sebi_compliant == sebi_compliant)

    # Total count for pagination
    count_result = await db.execute(
        select(func.count()).select_from(AIAuditLog).where(and_(*filters))
    )
    total = count_result.scalar() or 0

    # Fetch page
    skip = (page - 1) * page_size
    result = await db.execute(
        select(AIAuditLog)
        .where(and_(*filters))
        .order_by(desc(AIAuditLog.created_at))
        .offset(skip)
        .limit(page_size)
    )
    logs = result.scalars().all()

    # Enrich with client names
    client_ids = list({log.client_id for log in logs})
    client_names: dict = {}
    if client_ids:
        clients_result = await db.execute(
            select(Client.id, Client.name).where(Client.id.in_(client_ids))
        )
        client_names = {row.id: row.name for row in clients_result.all()}

    # Distinct tool names for filter UI
    tools_result = await db.execute(
        select(AIAuditLog.tool_name).distinct().order_by(AIAuditLog.tool_name)
    )
    available_tools = [row[0] for row in tools_result.all()]

    return success_response(data={
        "logs": [
            {
                "log_id": str(log.id),
                "client_id": str(log.client_id),
                "client_name": client_names.get(log.client_id, "Unknown"),
                "tool_name": log.tool_name,
                "user_query": log.user_query[:200],
                "ai_response_summary": log.ai_response_summary[:200],
                "confidence_score": log.confidence_score,
                "disclaimer_injected": log.disclaimer_injected,
                "sebi_compliant": log.sebi_compliant,
                "duration_ms": log.duration_ms,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, -(-total // page_size)),  # Ceiling division
        },
        "filters": {
            "days": days,
            "available_tools": available_tools,
        },
    })


# ─── Risk Alerts ──────────────────────────────────────────────────────────────

@router.get("/risk-alerts")
async def get_risk_alerts(
    priority: Optional[str] = Query(None, description="Filter by priority: critical/high/medium/low"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_rm_or_compliance),
) -> APIResponse:
    """All unresolved risk alerts across all clients, enriched with client names."""
    filters = [Alert.is_resolved == False]

    if priority:
        try:
            filters.append(Alert.priority == AlertPriority(priority))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid priority: {priority}")

    result = await db.execute(
        select(Alert)
        .where(and_(*filters))
        .order_by(Alert.priority, desc(Alert.created_at))
    )
    alerts = result.scalars().all()

    # Enrich with client names
    client_ids = list({a.client_id for a in alerts})
    client_names: dict = {}
    if client_ids:
        clients_result = await db.execute(
            select(Client.id, Client.name, Client.email).where(Client.id.in_(client_ids))
        )
        client_names = {row.id: {"name": row.name, "email": row.email} for row in clients_result.all()}

    # Summary counts by priority
    priority_counts = {p.value: 0 for p in AlertPriority}
    for a in alerts:
        pv = a.priority.value if hasattr(a.priority, "value") else str(a.priority)
        priority_counts[pv] = priority_counts.get(pv, 0) + 1

    return success_response(data={
        "total": len(alerts),
        "summary": priority_counts,
        "alerts": [
            {
                "alert_id": str(a.id),
                "client_id": str(a.client_id),
                "client_name": client_names.get(a.client_id, {}).get("name", "Unknown"),
                "client_email": client_names.get(a.client_id, {}).get("email", ""),
                "alert_type": a.alert_type.value if hasattr(a.alert_type, "value") else str(a.alert_type),
                "priority": a.priority.value if hasattr(a.priority, "value") else str(a.priority),
                "message": a.message,
                "is_resolved": a.is_resolved,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ],
    })


# ─── Resolve Alert ────────────────────────────────────────────────────────────

@router.patch("/resolve-alert/{alert_id}")
async def resolve_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_rm_or_compliance),
) -> APIResponse:
    """Mark a compliance alert as resolved."""
    try:
        aid = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid alert_id")

    result = await db.execute(select(Alert).where(Alert.id == aid))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_resolved = True
    alert.resolved_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info("alert_resolved", alert_id=alert_id, resolved_by=current_user.email)

    return success_response(data={
        "alert_id": alert_id,
        "resolved": True,
        "resolved_at": alert.resolved_at.isoformat(),
        "resolved_by": current_user.email,
    })


# ─── Generate Compliance Document ────────────────────────────────────────────

class GenerateDocRequest(BaseModel):
    client_id: str
    doc_type: str = Field(
        default="sebi_disclosure",
        description="One of: sebi_disclosure, risk_profile, suitability_attestation, kyc_record, meeting_summary",
    )
    additional_context: str = Field(default="", max_length=500)


@router.post("/generate-doc")
async def generate_compliance_doc(
    payload: GenerateDocRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_compliance),
) -> APIResponse:
    """
    Generate a SEBI-compliant disclosure document via Claude.

    Supports: sebi_disclosure, risk_profile, suitability_attestation, kyc_record, meeting_summary.
    Saved to compliance_documents table for audit purposes.
    """
    try:
        cid = uuid.UUID(payload.client_id)
        doc_type_enum = ComplianceDocType(payload.doc_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    client_result = await db.execute(
        select(Client)
        .where(Client.id == cid)
        .options(selectinload(Client.goals), selectinload(Client.alerts))
    )
    client = client_result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    doc_prompts = {
        ComplianceDocType.SEBI_DISCLOSURE: _sebi_disclosure_prompt,
        ComplianceDocType.RISK_PROFILE: _risk_profile_prompt,
        ComplianceDocType.SUITABILITY_ATTESTATION: _suitability_prompt,
        ComplianceDocType.KYC_RECORD: _kyc_record_prompt,
        ComplianceDocType.MEETING_SUMMARY: _meeting_summary_prompt,
    }

    prompt_builder = doc_prompts.get(doc_type_enum)
    if not prompt_builder:
        raise HTTPException(status_code=400, detail=f"Unsupported doc_type: {payload.doc_type}")

    prompt = prompt_builder(client, payload.additional_context)
    claude = get_claude_client()

    response = await claude.complete(
        messages=[{"role": "user", "content": prompt}],
        system="You are a compliance officer at a SEBI-registered Investment Advisory firm. Generate formal, compliant documentation following SEBI IA Regulations 2013.",
        max_tokens=800,
        temperature=0.1,
    )

    doc_content = response.content[0].text if response.content else "Document generation failed."

    doc = ComplianceDocument(
        client_id=cid,
        doc_type=doc_type_enum,
        content=doc_content,
        generated_by=f"ai:claude:{current_user.email}",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    logger.info(
        "compliance_doc_generated",
        client_id=payload.client_id,
        doc_type=payload.doc_type,
        doc_id=str(doc.id),
        generated_by=current_user.email,
    )

    return success_response(data={
        "doc_id": str(doc.id),
        "client_id": payload.client_id,
        "client_name": client.name,
        "doc_type": payload.doc_type,
        "content": doc_content,
        "generated_at": doc.created_at.isoformat(),
        "generated_by": doc.generated_by,
    })


# ─── AI Governance Dashboard ──────────────────────────────────────────────────

@router.get("/ai-governance")
async def get_ai_governance(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_rm_or_compliance),
) -> APIResponse:
    """
    AI governance metrics for compliance monitoring.

    Returns: total interactions, average confidence, SEBI compliance rate,
    tool usage breakdown, confidence distribution, low-confidence interactions.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # All logs in window
    result = await db.execute(
        select(AIAuditLog).where(AIAuditLog.created_at >= since)
    )
    logs = result.scalars().all()

    if not logs:
        return success_response(data={
            "period_days": days,
            "total_interactions": 0,
            "message": "No AI interactions in this period.",
        })

    total = len(logs)
    compliant = sum(1 for l in logs if l.sebi_compliant)
    with_disclaimer = sum(1 for l in logs if l.disclaimer_injected)
    scores = [l.confidence_score for l in logs if l.confidence_score is not None]
    avg_confidence = round(sum(scores) / len(scores), 3) if scores else None
    avg_duration = round(sum(l.duration_ms for l in logs if l.duration_ms) / total) if total else None

    # Tool usage breakdown
    tool_counts: dict = {}
    for log in logs:
        tool_counts[log.tool_name] = tool_counts.get(log.tool_name, 0) + 1
    tool_usage = sorted(
        [{"tool": k, "count": v, "pct": round(v / total * 100, 1)} for k, v in tool_counts.items()],
        key=lambda x: x["count"], reverse=True
    )

    # Confidence distribution
    conf_dist = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
    for log in logs:
        s = log.confidence_score
        if s is None:
            conf_dist["unknown"] += 1
        elif s >= 0.75:
            conf_dist["high"] += 1
        elif s >= 0.50:
            conf_dist["medium"] += 1
        else:
            conf_dist["low"] += 1

    # Low-confidence interactions (potential escalation needed)
    low_conf_logs = [l for l in logs if l.confidence_score is not None and l.confidence_score < 0.50]
    low_conf_logs.sort(key=lambda x: x.confidence_score)

    # Enrich low-conf with client names
    lc_client_ids = list({l.client_id for l in low_conf_logs[:10]})
    lc_client_names: dict = {}
    if lc_client_ids:
        cr = await db.execute(select(Client.id, Client.name).where(Client.id.in_(lc_client_ids)))
        lc_client_names = {row.id: row.name for row in cr.all()}

    # Daily interaction counts (last 7 days for trend)
    daily: dict = {}
    for log in logs:
        day = log.created_at.strftime("%Y-%m-%d")
        daily[day] = daily.get(day, 0) + 1
    daily_trend = [{"date": k, "count": v} for k, v in sorted(daily.items())][-7:]

    return success_response(data={
        "period_days": days,
        "total_interactions": total,
        "sebi_compliance_rate_pct": round(compliant / total * 100, 1),
        "disclaimer_injection_rate_pct": round(with_disclaimer / total * 100, 1),
        "average_confidence": avg_confidence,
        "average_duration_ms": avg_duration,
        "confidence_distribution": {
            k: {"count": v, "pct": round(v / total * 100, 1)}
            for k, v in conf_dist.items()
        },
        "tool_usage": tool_usage,
        "low_confidence_interactions": [
            {
                "log_id": str(l.id),
                "client_name": lc_client_names.get(l.client_id, "Unknown"),
                "tool_name": l.tool_name,
                "confidence_score": l.confidence_score,
                "query": l.user_query[:100],
                "created_at": l.created_at.isoformat(),
            }
            for l in low_conf_logs[:10]
        ],
        "daily_trend": daily_trend,
        "flags": {
            "interactions_below_threshold": conf_dist["low"],
            "non_compliant_count": total - compliant,
            "missing_disclaimer_count": total - with_disclaimer,
        },
    })


# ─── Document Prompt Builders ─────────────────────────────────────────────────

def _sebi_disclosure_prompt(client, context: str) -> str:
    return f"""Generate a formal SEBI Investment Adviser Disclosure Document for:
Client: {client.name} | Age: {client.age} | Risk Profile: {client.risk_profile.value if hasattr(client.risk_profile, 'value') else client.risk_profile}
{f'Additional context: {context}' if context else ''}

Include:
1. Adviser details and SEBI registration reference
2. Nature of services provided
3. Fee structure disclosure
4. Conflicts of interest statement
5. Risk disclaimer
6. Client rights and complaint redressal (SEBI SCORES)
7. Use of AI tools disclosure
8. Data privacy statement
9. Client signature block

Follow SEBI IA Regulations 2013 Clause 21 format. Date: {datetime.now().strftime('%B %d, %Y')}"""


def _risk_profile_prompt(client, context: str) -> str:
    return f"""Generate a formal Risk Profile Assessment Document for:
Client: {client.name} | Age: {client.age} | Annual Income: ₹{client.annual_income or 0:,.0f}
Risk Profile Assessed: {client.risk_profile.value if hasattr(client.risk_profile, 'value') else client.risk_profile}
Tax Regime: {client.tax_regime.value if hasattr(client.tax_regime, 'value') else client.tax_regime}
{f'Notes: {context}' if context else ''}

Include:
1. Client identification
2. Risk assessment methodology (questionnaire summary)
3. Risk profile determination: {client.risk_profile.value if hasattr(client.risk_profile, 'value') else client.risk_profile}
4. Implications of this risk profile for asset allocation
5. Recommended equity-debt-gold allocation range
6. Annual review commitment
7. Client acknowledgement section

Per SEBI IA Reg. Clause 18. Date: {datetime.now().strftime('%B %d, %Y')}"""


def _suitability_prompt(client, context: str) -> str:
    goals_summary = ", ".join(g.goal_name for g in client.goals) if client.goals else "Not specified"
    return f"""Generate a Suitability Attestation Document for:
Client: {client.name} | Risk Profile: {client.risk_profile.value if hasattr(client.risk_profile, 'value') else client.risk_profile}
Goals: {goals_summary}
{f'Notes: {context}' if context else ''}

Include:
1. Client profile summary
2. Investment objectives stated
3. Suitability assessment rationale (SEBI Clause 19)
4. Recommended investment strategy
5. Specific instruments recommended and rationale for each
6. Risk warnings specific to recommendations
7. Adviser certification of suitability
8. Client acknowledgement

Date: {datetime.now().strftime('%B %d, %Y')}"""


def _kyc_record_prompt(client, context: str) -> str:
    return f"""Generate a KYC Record Summary for:
Client: {client.name} | Email: {client.email}
KYC Status: {'Verified' if client.kyc_verified else 'PENDING VERIFICATION'}
{f'Notes: {context}' if context else ''}

Include:
1. Client identification details
2. KYC verification status and date
3. PAN verification status
4. Address verification status
5. Politically Exposed Person (PEP) declaration
6. Source of funds declaration
7. Next KYC refresh due date (24 months from verification)
8. PMLA compliance statement

Date: {datetime.now().strftime('%B %d, %Y')}"""


def _meeting_summary_prompt(client, context: str) -> str:
    return f"""Generate a formal Meeting Summary/Minutes document for:
Client: {client.name} | Date: {datetime.now().strftime('%B %d, %Y')}
{f'Meeting notes: {context}' if context else ''}

Include:
1. Meeting details (date, participants, format: in-person/video/phone)
2. Portfolio review summary
3. Goal progress discussed
4. Recommendations made (with Clause 19 rationale)
5. Client queries and responses
6. Action items (with owner and deadline)
7. Next review date
8. Client acknowledgement

Per SEBI IA Regulations record-keeping requirements."""
