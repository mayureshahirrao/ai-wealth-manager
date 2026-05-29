"""
clients.py — Client and portfolio endpoints.

Phase 2: real data with XIRR, tax calculations, goal feasibility scores.
"""

import uuid
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.role_guard import get_current_user, CurrentUser
from app.core.base_response import success_response, APIResponse
from app.core.exceptions import ClientNotFoundException
from app.database.models import Client, Portfolio, Holding, Goal, NAVHistory, Alert, Transaction
from app.database.transaction import get_db
from app.financial import (
    compare_tax_regimes, calculate_ltcg_tax, ltcg_harvesting_opportunity, Deductions,
    GoalAssessment, assess_retirement_readiness,
    format_inr, xirr_to_display,
)

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("")
async def list_clients(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> APIResponse:
    """Client list with AUM, XIRR, days since review, alert counts — for RM dashboard."""
    result = await db.execute(select(Client).order_by(Client.name))
    clients = result.scalars().all()

    # Load portfolios and alert counts in bulk
    portfolio_result = await db.execute(select(Portfolio))
    portfolios = {p.client_id: p for p in portfolio_result.scalars().all()}

    alert_result = await db.execute(
        select(Alert.client_id, func.count(Alert.id).label("cnt"))
        .where(Alert.is_resolved == False)  # noqa: E712
        .group_by(Alert.client_id)
    )
    alert_counts = {row.client_id: row.cnt for row in alert_result}

    today = date.today()
    rows = []
    for c in clients:
        p = portfolios.get(c.id)
        days_since_review = None
        if c.last_review_date:
            review_date = c.last_review_date.date() if isinstance(c.last_review_date, datetime) else c.last_review_date
            days_since_review = (today - review_date).days

        rows.append({
            "client_id": str(c.id),
            "name": c.name,
            "email": c.email,
            "age": c.age,
            "risk_profile": c.risk_profile.value,
            "segment": _get_segment(c),
            "kyc_verified": c.kyc_verified,
            "aum": p.current_value if p else 0,
            "aum_display": format_inr(p.current_value) if p else "₹0",
            "total_invested": p.total_invested if p else 0,
            "xirr": p.xirr if p else None,
            "xirr_display": xirr_to_display(p.xirr) if p else "N/A",
            "benchmark_xirr": p.benchmark_xirr if p else None,
            "days_since_review": days_since_review,
            "review_due": days_since_review is None or days_since_review > 365,
            "active_alerts": alert_counts.get(c.id, 0),
        })
    return success_response(data=rows)


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
    """Goals with GoalAssessment feasibility scores and gap analysis."""
    client = await _fetch_client(client_id, db)
    result = await db.execute(select(Goal).where(Goal.client_id == client.id).order_by(Goal.priority))
    goals = result.scalars().all()

    this_year = date.today().year
    rows = []
    for g in goals:
        years_remaining = max(0, g.target_year - this_year)
        target_date = date(g.target_year, 12, 31)

        assessment = GoalAssessment(
            goal_type=g.goal_type.value,
            target_amount=g.target_amount,
            target_date=target_date,
            current_corpus=g.current_corpus,
            monthly_sip=g.monthly_sip,
            years_remaining=years_remaining,
        )
        a = assessment.to_dict()
        rows.append({
            "goal_id": str(g.id),
            "goal_name": g.goal_name,
            "priority": g.priority,
            **a,
        })

    return success_response(data=rows)


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
    """
    Tax regime comparison (Old vs New) + LTCG harvesting opportunity.
    Uses client's annual_income and portfolio unrealized gains.
    """
    client = await _fetch_client(client_id, db)

    gross_income = client.annual_income or 0
    age = client.age or 35

    # Regime comparison
    regime_result = compare_tax_regimes(gross_income=gross_income, age=age)

    # LTCG harvesting — compute unrealized gains on equity holdings
    portfolio_result = await db.execute(select(Portfolio).where(Portfolio.client_id == client.id))
    portfolio = portfolio_result.scalar_one_or_none()
    ltcg_data = None

    if portfolio:
        holdings_result = await db.execute(
            select(Holding).where(Holding.portfolio_id == portfolio.id)
        )
        holdings = holdings_result.scalars().all()
        today = date.today()
        unrealized_ltcg = sum(
            (h.current_value - h.invested_amount)
            for h in holdings
            if _is_ltcg_eligible(h) and h.current_value > h.invested_amount
        )
        ltcg_data = ltcg_harvesting_opportunity(unrealized_gains=unrealized_ltcg)

    return success_response(data={
        "client_id": client_id,
        "gross_income": gross_income,
        "gross_income_display": format_inr(gross_income),
        "tax_regime": client.tax_regime.value,
        "regime_comparison": regime_result,
        "ltcg_harvesting": ltcg_data,
        "current_fy": f"FY {date.today().year}-{str(date.today().year + 1)[2:]}",
    })


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
    if not holding.purchase_date:
        return False
    months = (date.today() - holding.purchase_date).days / 30
    if holding.asset_class.value == "equity":
        return months >= 12
    return months >= 36
