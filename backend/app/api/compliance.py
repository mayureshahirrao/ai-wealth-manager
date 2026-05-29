"""
compliance.py — Compliance officer endpoints.
Stub — full implementation in Phase 8.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.role_guard import require_compliance, CurrentUser
from app.core.base_response import success_response, APIResponse
from app.database.models import AIAuditLog, Alert
from app.database.transaction import get_db

router = APIRouter(prefix="/api/compliance", tags=["compliance"])


@router.get("/audit-log")
async def get_audit_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_compliance),
) -> APIResponse:
    skip = (page - 1) * page_size
    result = await db.execute(
        select(AIAuditLog).order_by(AIAuditLog.created_at.desc()).offset(skip).limit(page_size)
    )
    logs = result.scalars().all()
    return success_response(data=[
        {
            "log_id": str(log.id),
            "client_id": str(log.client_id),
            "tool_name": log.tool_name,
            "user_query": log.user_query[:100],
            "confidence_score": log.confidence_score,
            "disclaimer_injected": log.disclaimer_injected,
            "sebi_compliant": log.sebi_compliant,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ])


@router.get("/risk-alerts")
async def get_risk_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_compliance),
) -> APIResponse:
    result = await db.execute(
        select(Alert).where(Alert.is_resolved == False).order_by(Alert.created_at.desc()).limit(50)
    )
    alerts = result.scalars().all()
    return success_response(data=[
        {
            "alert_id": str(a.id),
            "client_id": str(a.client_id),
            "alert_type": a.alert_type.value,
            "priority": a.priority.value,
            "message": a.message,
            "created_at": a.created_at.isoformat(),
        }
        for a in alerts
    ])


@router.post("/generate-doc")
async def generate_compliance_doc(
    current_user: CurrentUser = Depends(require_compliance),
) -> APIResponse:
    return success_response(data={"message": "Compliance doc generation — coming in Phase 8"})


@router.get("/ai-governance")
async def get_ai_governance(
    current_user: CurrentUser = Depends(require_compliance),
) -> APIResponse:
    return success_response(data={"message": "AI governance dashboard — coming in Phase 8"})
