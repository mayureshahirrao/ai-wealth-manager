"""
me.py — Investor self-service endpoints.

Investors access their own data via JWT; no client_id needed in the URL.
All endpoints resolve the client from current_user.client_id.

Available:
  GET /api/me/portfolio        — holdings + AUM
  GET /api/me/goals            — goals with GoalAssessment feasibility
  GET /api/me/tax-summary      — regime comparison + LTCG harvesting
  GET /api/me/performance      — XIRR vs benchmark + P&L
  GET /api/me/nav-history      — portfolio value over time (for charts)
  GET /api/me/profile          — own client profile
"""

import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.role_guard import require_investor, CurrentUser
from app.core.base_response import success_response, APIResponse
from app.database.models import Client, Portfolio, Holding, Goal, NAVHistory, Alert
from app.database.transaction import get_db
from app.financial import (
    compare_tax_regimes, ltcg_harvesting_opportunity,
    GoalAssessment, assess_retirement_readiness,
    format_inr, xirr_to_display,
)

router = APIRouter(prefix="/api/me", tags=["me"])


async def _get_my_client(current_user: CurrentUser, db: AsyncSession) -> Client:
    """Resolve the Client record linked to the authenticated investor."""
    if not current_user.client_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No client profile linked to this account")
    result = await db.execute(select(Client).where(Client.id == current_user.client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client profile not found")
    return client


# ─── Profile ─────────────────────────────────────────────────────────────────

@router.get("/profile")
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_investor),
) -> APIResponse:
    """Return own client profile."""
    client = await _get_my_client(current_user, db)
    return success_response(data={
        "client_id": str(client.id),
        "name": client.name,
        "email": client.email,
        "age": client.age,
        "pan": client.pan,
        "risk_profile": client.risk_profile.value,
        "tax_regime": client.tax_regime.value,
        "annual_income": client.annual_income,
        "kyc_verified": client.kyc_verified,
        "segment": _get_segment(client),
    })


# ─── Portfolio ────────────────────────────────────────────────────────────────

@router.get("/portfolio")
async def get_my_portfolio(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_investor),
) -> APIResponse:
    """Holdings, AUM, XIRR for the authenticated investor."""
    client = await _get_my_client(current_user, db)

    p_result = await db.execute(select(Portfolio).where(Portfolio.client_id == client.id))
    portfolio = p_result.scalar_one_or_none()

    if not portfolio:
        return success_response(data={
            "client_id": str(client.id),
            "holdings": [],
            "total_invested": 0,
            "current_value": 0,
            "xirr": None,
        })

    h_result = await db.execute(select(Holding).where(Holding.portfolio_id == portfolio.id))
    holdings = h_result.scalars().all()

    total_unrealized = portfolio.current_value - portfolio.total_invested
    total_unrealized_pct = (
        total_unrealized / portfolio.total_invested * 100
        if portfolio.total_invested > 0 else 0
    )

    return success_response(data={
        "client_id": str(client.id),
        "total_invested": portfolio.total_invested,
        "total_invested_display": format_inr(portfolio.total_invested),
        "current_value": portfolio.current_value,
        "current_value_display": format_inr(portfolio.current_value),
        "total_unrealized_pnl": round(total_unrealized, 2),
        "total_unrealized_pnl_pct": round(total_unrealized_pct, 2),
        "xirr": portfolio.xirr,
        "xirr_display": xirr_to_display(portfolio.xirr),
        "benchmark_xirr": portfolio.benchmark_xirr,
        "benchmark_xirr_display": xirr_to_display(portfolio.benchmark_xirr),
        "last_calculated_at": portfolio.last_calculated_at.isoformat() if portfolio.last_calculated_at else None,
        "holdings": [
            {
                "scheme_name": h.scheme_name,
                "folio_number": h.folio_number,
                "asset_class": h.asset_class.value,
                "units": h.units,
                "nav": h.nav,
                "invested_amount": h.invested_amount,
                "current_value": h.current_value,
                "unrealized_pnl": round(h.current_value - h.invested_amount, 2),
                "unrealized_pnl_pct": round(
                    (h.current_value - h.invested_amount) / h.invested_amount * 100, 2
                ) if h.invested_amount > 0 else 0,
                "purchase_date": str(h.purchase_date) if h.purchase_date else None,
                "is_ltcg_eligible": _is_ltcg_eligible(h),
                "has_sip_active": h.has_sip_active,
                "sip_amount": h.sip_amount,
                "weight_pct": round(h.current_value / portfolio.current_value * 100, 2) if portfolio.current_value > 0 else 0,
            }
            for h in holdings
        ],
    })


# ─── Performance ──────────────────────────────────────────────────────────────

@router.get("/performance")
async def get_my_performance(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_investor),
) -> APIResponse:
    """XIRR vs Nifty 50 benchmark + absolute P&L."""
    client = await _get_my_client(current_user, db)
    p_result = await db.execute(select(Portfolio).where(Portfolio.client_id == client.id))
    portfolio = p_result.scalar_one_or_none()

    if not portfolio:
        return success_response(data={"xirr": None, "benchmark_xirr": None, "total_pnl": 0})

    total_pnl = portfolio.current_value - portfolio.total_invested
    alpha = (
        (portfolio.xirr - portfolio.benchmark_xirr) * 100
        if portfolio.xirr is not None and portfolio.benchmark_xirr is not None
        else None
    )

    return success_response(data={
        "total_invested": portfolio.total_invested,
        "current_value": portfolio.current_value,
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round(total_pnl / portfolio.total_invested * 100, 2) if portfolio.total_invested > 0 else 0,
        "xirr": portfolio.xirr,
        "xirr_display": xirr_to_display(portfolio.xirr),
        "xirr_pct": round(portfolio.xirr * 100, 2) if portfolio.xirr is not None else None,
        "benchmark_xirr": portfolio.benchmark_xirr,
        "benchmark_xirr_pct": round(portfolio.benchmark_xirr * 100, 2) if portfolio.benchmark_xirr is not None else None,
        "alpha_pct": round(alpha, 2) if alpha is not None else None,
        "outperforming": alpha > 0 if alpha is not None else None,
    })


# ─── NAV History ──────────────────────────────────────────────────────────────

@router.get("/nav-history")
async def get_my_nav_history(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_investor),
) -> APIResponse:
    """Portfolio value over time for line chart."""
    client = await _get_my_client(current_user, db)
    p_result = await db.execute(select(Portfolio).where(Portfolio.client_id == client.id))
    portfolio = p_result.scalar_one_or_none()
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


# ─── Goals ────────────────────────────────────────────────────────────────────

@router.get("/goals")
async def get_my_goals(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_investor),
) -> APIResponse:
    """Goals with GoalAssessment feasibility scores and gap analysis."""
    client = await _get_my_client(current_user, db)
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
        rows.append({
            "goal_id": str(g.id),
            "goal_name": g.goal_name,
            "priority": g.priority,
            **assessment.to_dict(),
        })

    # Retirement readiness (if retirement goal exists)
    retirement_readiness = None
    if client.age:
        retirement_goal = next(
            (g for g in goals if g.goal_type.value == "retirement"), None
        )
        if retirement_goal:
            retirement_readiness = assess_retirement_readiness(
                current_age=client.age,
                target_retirement_age=retirement_goal.target_year - (date.today().year - client.age),
                current_retirement_corpus=retirement_goal.current_corpus,
                monthly_retirement_sip=retirement_goal.monthly_sip,
                desired_monthly_income=round((client.annual_income or 600_000) / 12 * 0.7),
            )

    return success_response(data={
        "goals": rows,
        "retirement_readiness": retirement_readiness,
        "overall_on_track": all(r.get("status") in ("on_track", "slightly_off") for r in rows),
    })


# ─── Tax Summary ──────────────────────────────────────────────────────────────

@router.get("/tax-summary")
async def get_my_tax_summary(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_investor),
) -> APIResponse:
    """Tax regime comparison + LTCG harvesting opportunity."""
    client = await _get_my_client(current_user, db)

    gross_income = client.annual_income or 0
    age = client.age or 35

    regime_result = compare_tax_regimes(gross_income=gross_income, age=age)

    # LTCG harvesting opportunity
    p_result = await db.execute(select(Portfolio).where(Portfolio.client_id == client.id))
    portfolio = p_result.scalar_one_or_none()
    ltcg_data = None

    if portfolio:
        h_result = await db.execute(select(Holding).where(Holding.portfolio_id == portfolio.id))
        holdings = h_result.scalars().all()
        unrealized_ltcg = sum(
            (h.current_value - h.invested_amount)
            for h in holdings
            if _is_ltcg_eligible(h) and h.current_value > h.invested_amount
        )
        ltcg_data = ltcg_harvesting_opportunity(unrealized_gains=unrealized_ltcg)

    return success_response(data={
        "client_id": str(client.id),
        "gross_income": gross_income,
        "gross_income_display": format_inr(gross_income),
        "current_tax_regime": client.tax_regime.value,
        "regime_comparison": regime_result,
        "ltcg_harvesting": ltcg_data,
        "current_fy": f"FY {date.today().year}-{str(date.today().year + 1)[2:]}",
    })


# ─── Alerts ───────────────────────────────────────────────────────────────────

@router.get("/alerts")
async def get_my_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_investor),
) -> APIResponse:
    """Active alerts for the investor."""
    client = await _get_my_client(current_user, db)
    result = await db.execute(
        select(Alert)
        .where(Alert.client_id == client.id, Alert.is_resolved == False)  # noqa: E712
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


# ─── Helpers ─────────────────────────────────────────────────────────────────

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
