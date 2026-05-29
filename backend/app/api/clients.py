"""
clients.py — Client and portfolio endpoints.
Stub implementations — full logic added in Phase 2/6.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.role_guard import get_current_user, CurrentUser
from app.core.base_response import success_response, APIResponse
from app.core.exceptions import ClientNotFoundException
from app.database.models import Client, Portfolio, Holding, Goal, NAVHistory
from app.database.transaction import get_db

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("")
async def list_clients(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> APIResponse:
    result = await db.execute(select(Client).order_by(Client.name))
    clients = result.scalars().all()
    return success_response(data=[
        {
            "client_id": str(c.id),
            "name": c.name,
            "email": c.email,
            "risk_profile": c.risk_profile.value,
            "segment": _get_segment(c),
        }
        for c in clients
    ])


@router.get("/{client_id}")
async def get_client(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> APIResponse:
    client = await _fetch_client(client_id, db)
    return success_response(data={
        "client_id": str(client.id),
        "name": client.name,
        "email": client.email,
        "age": client.age,
        "risk_profile": client.risk_profile.value,
        "tax_regime": client.tax_regime.value,
        "annual_income": client.annual_income,
        "kyc_verified": client.kyc_verified,
    })


@router.get("/{client_id}/portfolio")
async def get_portfolio(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> APIResponse:
    client = await _fetch_client(client_id, db)
    result = await db.execute(select(Portfolio).where(Portfolio.client_id == client.id))
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        return success_response(data={"client_id": client_id, "holdings": [], "total_invested": 0, "current_value": 0})

    holdings_result = await db.execute(select(Holding).where(Holding.portfolio_id == portfolio.id))
    holdings = holdings_result.scalars().all()

    return success_response(data={
        "client_id": client_id,
        "total_invested": portfolio.total_invested,
        "current_value": portfolio.current_value,
        "xirr": portfolio.xirr,
        "benchmark_xirr": portfolio.benchmark_xirr,
        "holdings": [
            {
                "scheme_name": h.scheme_name,
                "folio_number": h.folio_number,
                "asset_class": h.asset_class.value,
                "units": h.units,
                "nav": h.nav,
                "invested_amount": h.invested_amount,
                "current_value": h.current_value,
                "unrealized_pnl": h.current_value - h.invested_amount,
                "purchase_date": str(h.purchase_date) if h.purchase_date else None,
                "is_ltcg_eligible": _is_ltcg_eligible(h),
                "has_sip_active": h.has_sip_active,
            }
            for h in holdings
        ],
    })


@router.get("/{client_id}/goals")
async def get_goals(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> APIResponse:
    client = await _fetch_client(client_id, db)
    result = await db.execute(select(Goal).where(Goal.client_id == client.id).order_by(Goal.priority))
    goals = result.scalars().all()
    return success_response(data=[
        {
            "goal_id": str(g.id),
            "goal_name": g.goal_name,
            "goal_type": g.goal_type.value,
            "target_amount": g.target_amount,
            "current_corpus": g.current_corpus,
            "monthly_sip": g.monthly_sip,
            "target_year": g.target_year,
            "progress_pct": round(g.current_corpus / g.target_amount * 100, 1) if g.target_amount > 0 else 0,
        }
        for g in goals
    ])


@router.get("/{client_id}/nav-history")
async def get_nav_history(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> APIResponse:
    client = await _fetch_client(client_id, db)
    portfolio_result = await db.execute(select(Portfolio).where(Portfolio.client_id == client.id))
    portfolio = portfolio_result.scalar_one_or_none()
    if not portfolio:
        return success_response(data=[])

    result = await db.execute(
        select(NAVHistory)
        .where(NAVHistory.portfolio_id == portfolio.id)
        .order_by(NAVHistory.record_date)
    )
    history = result.scalars().all()
    return success_response(data=[
        {
            "date": str(h.record_date),
            "portfolio_value": h.portfolio_value,
            "benchmark_value": h.benchmark_value,
        }
        for h in history
    ])


@router.get("/{client_id}/tax-summary")
async def get_tax_summary(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> APIResponse:
    # Stub — full implementation in Phase 6 with tax_calculator
    return success_response(data={"client_id": client_id, "message": "Tax summary coming in Phase 6"})


@router.get("/{client_id}/performance")
async def get_performance(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> APIResponse:
    client = await _fetch_client(client_id, db)
    portfolio_result = await db.execute(select(Portfolio).where(Portfolio.client_id == client.id))
    portfolio = portfolio_result.scalar_one_or_none()
    if not portfolio:
        return success_response(data={"xirr": None, "benchmark_xirr": None})
    return success_response(data={
        "xirr": portfolio.xirr,
        "benchmark_xirr": portfolio.benchmark_xirr,
        "total_pnl": portfolio.current_value - portfolio.total_invested,
        "total_pnl_pct": (
            (portfolio.current_value - portfolio.total_invested) / portfolio.total_invested
            if portfolio.total_invested > 0 else 0
        ),
    })


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def _fetch_client(client_id: str, db: AsyncSession) -> Client:
    import uuid
    try:
        uid = uuid.UUID(client_id)
    except ValueError:
        raise ClientNotFoundException(client_id)
    result = await db.execute(select(Client).where(Client.id == uid))
    client = result.scalar_one_or_none()
    if not client:
        raise ClientNotFoundException(client_id)
    return client


def _get_segment(client: Client) -> str:
    if not client.annual_income:
        return "Mass_Affluent"
    income = client.annual_income
    if income >= 10_000_000:
        return "UHNI"
    if income >= 5_000_000:
        return "HNI"
    return "Mass_Affluent"


def _is_ltcg_eligible(holding: Holding) -> bool:
    from datetime import date
    if not holding.purchase_date:
        return False
    months = (date.today() - holding.purchase_date).days / 30
    if holding.asset_class.value == "equity":
        return months >= 12
    return months >= 36
