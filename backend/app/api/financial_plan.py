"""
financial_plan.py — Financial plan generation endpoints.
Stub — full implementation in Phase 7.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.role_guard import require_rm, CurrentUser
from app.core.base_response import success_response, APIResponse
from app.database.transaction import get_db

router = APIRouter(prefix="/api/financial-plan", tags=["financial-plan"])


@router.post("/generate")
async def generate_financial_plan(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_rm),
) -> APIResponse:
    return success_response(data={"message": "Financial plan generation — coming in Phase 7"})


@router.get("/{client_id}")
async def get_financial_plan(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_rm),
) -> APIResponse:
    return success_response(data={"client_id": client_id, "message": "Financial plan — coming in Phase 7"})
