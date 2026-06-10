"""
test_portfolio.py — Tests for /api/me/* investor portfolio endpoints.
"""

import uuid
import pytest
from datetime import date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


async def _seed_investor_with_portfolio(
    db_session: AsyncSession,
) -> tuple[uuid.UUID, str, str]:
    """Seed a User + Client + Portfolio + 2 Holdings. Returns (client_id, email, password)."""
    from app.database.models import User, Client, Portfolio, Holding
    from app.database.base_model import UserRole, RiskProfile, AssetClass

    client_id = uuid.uuid4()
    user_id = uuid.uuid4()

    from app.auth.password_utils import hash_password

    email = f"portfolio_investor_{client_id.hex[:8]}@demo.com"
    user = User(
        id=user_id,
        email=email,
        hashed_password=hash_password("pass1234"),
        role=UserRole.INVESTOR,
        is_active=True,
        client_id=client_id,
    )

    client = Client(
        id=client_id,
        name="Test Investor",
        email=f"portfolio_investor_{client_id.hex[:8]}@demo.com",
        risk_profile=RiskProfile.MODERATE,
        annual_income=1200000.0,
        date_of_birth=date(1985, 6, 15),
    )

    portfolio = Portfolio(
        id=uuid.uuid4(),
        client_id=client_id,
        total_invested=500000.0,
        current_value=620000.0,
        xirr=12.5,
        benchmark_xirr=10.2,
    )

    holding1 = Holding(
        id=uuid.uuid4(),
        portfolio_id=portfolio.id,
        scheme_name="Axis Bluechip Fund",
        isin="INF846K01EW2",
        asset_class=AssetClass.EQUITY,
        units=150.5,
        nav=52.30,
        current_value=78721.0,
        invested_amount=60000.0,
    )

    holding2 = Holding(
        id=uuid.uuid4(),
        portfolio_id=portfolio.id,
        scheme_name="HDFC Short Term Debt Fund",
        isin="INF179KB1HQ3",
        asset_class=AssetClass.DEBT,
        units=500.0,
        nav=25.10,
        current_value=12550.0,
        invested_amount=11000.0,
    )

    db_session.add_all([user, client, portfolio, holding1, holding2])
    await db_session.commit()
    return client_id, "portfolio_investor@demo.com", "pass1234"


@pytest.fixture
async def investor_with_portfolio(client: AsyncClient, db_session: AsyncSession):
    client_id, email, password = await _seed_investor_with_portfolio(db_session)
    login_email = f"portfolio_investor_{client_id.hex[:8]}@demo.com"
    resp = await client.post("/api/auth/login", json={"email": login_email, "password": password})
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}, client_id


# ─── /api/me/portfolio ────────────────────────────────────────────────────────

async def test_portfolio_returns_data(
    client: AsyncClient,
    investor_with_portfolio,
):
    headers, _ = investor_with_portfolio
    resp = await client.get("/api/me/portfolio", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "current_value" in data
    assert "xirr" in data
    assert "holdings" in data
    assert len(data["holdings"]) == 2


async def test_portfolio_requires_auth(client: AsyncClient):
    resp = await client.get("/api/me/portfolio")
    assert resp.status_code == 401


async def test_portfolio_rm_cannot_use_me_endpoint(
    client: AsyncClient,
    auth_headers_rm: dict,
):
    """RM has no client_id — /api/me/portfolio should return 404 or 403."""
    resp = await client.get("/api/me/portfolio", headers=auth_headers_rm)
    # RM user has no linked Client row → expect 404
    assert resp.status_code in (403, 404)


# ─── /api/me/goals ────────────────────────────────────────────────────────────

async def test_goals_returns_data(
    client: AsyncClient,
    investor_with_portfolio,
):
    headers, _ = investor_with_portfolio
    resp = await client.get("/api/me/goals", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    # Response is either list or dict with 'goals' key
    assert isinstance(data, (list, dict))


# ─── /api/me/tax-summary ──────────────────────────────────────────────────────

async def test_tax_summary_returns_regimes(
    client: AsyncClient,
    investor_with_portfolio,
):
    headers, _ = investor_with_portfolio
    resp = await client.get("/api/me/tax-summary", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    # Tax summary response contains gross_income and regime comparison fields
    assert "gross_income" in data or "old_regime" in data or "current_tax_regime" in data
