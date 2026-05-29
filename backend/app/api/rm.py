"""
rm.py — Relationship Manager endpoints.
Stub — full implementation in Phase 7.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.role_guard import require_rm, CurrentUser
from app.core.base_response import success_response, APIResponse
from app.database.transaction import get_db

router = APIRouter(prefix="/api/rm", tags=["rm"])


@router.get("/next-actions")
async def get_next_actions(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_rm),
) -> APIResponse:
    return success_response(data={"message": "RM Next Best Actions — coming in Phase 7", "actions": []})


@router.get("/meeting-prep/{client_id}")
async def get_meeting_prep(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_rm),
) -> APIResponse:
    return success_response(data={"client_id": client_id, "message": "Meeting Prep — coming in Phase 7"})


@router.get("/alerts/{client_id}")
async def get_client_alerts(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_rm),
) -> APIResponse:
    from sqlalchemy import select
    from app.database.models import Alert, Client
    import uuid

    client_result = await db.execute(select(Client).where(Client.id == uuid.UUID(client_id)))
    client = client_result.scalar_one_or_none()
    if not client:
        return success_response(data=[])

    result = await db.execute(
        select(Alert)
        .where(Alert.client_id == client.id, Alert.is_resolved == False)
        .order_by(Alert.created_at.desc())
    )
    alerts = result.scalars().all()
    return success_response(data=[
        {
            "alert_id": str(a.id),
            "alert_type": a.alert_type.value,
            "priority": a.priority.value,
            "message": a.message,
            "created_at": a.created_at.isoformat(),
        }
        for a in alerts
    ])
