"""
seed_data.py — Seed 5 Indian demo personas into the database.

Run once after DB init:
    python -m app.seed.seed_data

Creates:
- 3 User accounts (investor, rm, compliance) with hashed passwords
- 5 Client records with portfolios, holdings, goals, NAV history
- Sample alerts for compliance testing
"""

import asyncio
import uuid
from datetime import date, datetime, timezone
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import get_settings
from app.auth.password_utils import hash_password
from app.database.base_model import (
    UserRole, RiskProfile, TaxRegime, AssetClass,
    GoalType, TransactionType, AlertType, AlertPriority
)
from app.database.models import (
    User, Client, Portfolio, Holding, Goal,
    Transaction, Alert, NAVHistory, WealthBase
)

settings = get_settings()
DEMO_PASSWORD = hash_password("demo1234")


# ─── Client Personas ─────────────────────────────────────────────────────────

CLIENTS = [
    {
        "name": "Priya Sharma",
        "email": "priya.sharma@demo.com",
        "pan": "ABCPS1234F",
        "age": 34,
        "risk_profile": RiskProfile.MODERATE,
        "tax_regime": TaxRegime.NEW,
        "annual_income": 2_200_000,   # ₹22L
        "kyc_verified": True,
    },
    {
        "name": "Arjun Kapoor",
        "email": "arjun.kapoor@demo.com",
        "pan": "BCPAK5678G",
        "age": 42,
        "risk_profile": RiskProfile.AGGRESSIVE,
        "tax_regime": TaxRegime.OLD,
        "annual_income": 12_000_000,  # ₹1.2Cr
        "kyc_verified": True,
    },
    {
        "name": "Sunita Rao",
        "email": "sunita.rao@demo.com",
        "pan": "CDPSR9012H",
        "age": 58,
        "risk_profile": RiskProfile.CONSERVATIVE,
        "tax_regime": TaxRegime.OLD,
        "annual_income": 1_500_000,   # ₹15L
        "kyc_verified": True,
    },
    {
        "name": "Vikram Nair",
        "email": "vikram.nair@demo.com",
        "pan": "DEPVN3456I",
        "age": 28,
        "risk_profile": RiskProfile.MODERATELY_AGGRESSIVE,
        "tax_regime": TaxRegime.NEW,
        "annual_income": 1_800_000,   # ₹18L
        "kyc_verified": True,
    },
    {
        "name": "Meena Iyer",
        "email": "meena.iyer@demo.com",
        "pan": "EFPMI7890J",
        "age": 47,
        "risk_profile": RiskProfile.MODERATE,
        "tax_regime": TaxRegime.NEW,
        "annual_income": 3_500_000,   # ₹35L
        "kyc_verified": True,
    },
]


def _make_portfolio(client_id: uuid.UUID, multiplier: float = 1.0):
    base_invested = 2_400_000 * multiplier
    base_current = base_invested * 1.325  # ~32.5% gain
    return {
        "client_id": client_id,
        "total_invested": base_invested,
        "current_value": base_current,
        "xirr": 0.132 + (multiplier - 1) * 0.01,
        "benchmark_xirr": 0.118,
        "last_calculated_at": datetime.now(timezone.utc),
    }


def _make_holdings(portfolio_id: uuid.UUID, multiplier: float = 1.0):
    base = multiplier
    return [
        {
            "portfolio_id": portfolio_id,
            "scheme_name": "Mirae Asset Large Cap Fund - Direct Growth",
            "isin": "INF769K01DM8",
            "folio_number": f"F{portfolio_id.hex[:6].upper()}01",
            "asset_class": AssetClass.EQUITY,
            "units": 1250.45 * base,
            "nav": 89.4,
            "invested_amount": 800_000 * base,
            "current_value": 1_117_000 * base,
            "purchase_date": date(2021, 4, 1),
            "sip_amount": 15_000,
            "has_sip_active": True,
        },
        {
            "portfolio_id": portfolio_id,
            "scheme_name": "HDFC Short Duration Fund - Direct Growth",
            "isin": "INF179KB1BR0",
            "folio_number": f"F{portfolio_id.hex[:6].upper()}02",
            "asset_class": AssetClass.DEBT,
            "units": 5420.3 * base,
            "nav": 22.1,
            "invested_amount": 900_000 * base,
            "current_value": 1_197_000 * base,
            "purchase_date": date(2020, 10, 15),
            "has_sip_active": False,
        },
        {
            "portfolio_id": portfolio_id,
            "scheme_name": "SBI Gold ETF",
            "isin": "INF200KA1RC2",
            "folio_number": f"F{portfolio_id.hex[:6].upper()}03",
            "asset_class": AssetClass.GOLD,
            "units": 34.2 * base,
            "nav": 584.5,
            "invested_amount": 700_000 * base,
            "current_value": 866_000 * base,
            "purchase_date": date(2022, 1, 10),
            "has_sip_active": False,
        },
    ]


def _make_goals(client_id: uuid.UUID, client_age: int):
    years_to_retire = max(60 - client_age, 5)
    return [
        {
            "client_id": client_id,
            "goal_name": "Retirement Corpus",
            "goal_type": GoalType.RETIREMENT,
            "target_amount": 30_000_000,
            "current_corpus": 3_180_000,
            "monthly_sip": 25_000,
            "target_year": date.today().year + years_to_retire,
            "priority": 1,
        },
        {
            "client_id": client_id,
            "goal_name": "Children Education",
            "goal_type": GoalType.CHILD_EDUCATION,
            "target_amount": 5_000_000,
            "current_corpus": 1_200_000,
            "monthly_sip": 12_000,
            "target_year": date.today().year + 8,
            "priority": 2,
        },
    ]


def _make_transactions(client_id: uuid.UUID, multiplier: float = 1.0):
    """24 months of monthly SIP transactions for XIRR computation."""
    transactions = []
    today = date.today()

    holdings_config = [
        ("Mirae Asset Large Cap Fund - Direct Growth", 15_000),
        ("HDFC Short Duration Fund - Direct Growth", 10_000),
    ]

    import calendar

    for month_offset in range(24, 0, -1):
        m = today.month - month_offset
        y = today.year + (m - 1) // 12
        m = ((m - 1) % 12) + 1
        last_day = calendar.monthrange(y, m)[1]
        txn_date = date(y, m, min(5, last_day))  # SIP on 5th of each month

        for scheme, sip_amount in holdings_config:
            transactions.append({
                "client_id": client_id,
                "scheme_name": scheme,
                "transaction_type": TransactionType.SIP,
                "amount": sip_amount * multiplier,
                "transaction_date": txn_date,
            })

    # Add initial lumpsum purchases (3 years ago)
    lumpsum_date = date(today.year - 3, today.month, 1)
    lumpsum_configs = [
        ("Mirae Asset Large Cap Fund - Direct Growth", 300_000),
        ("HDFC Short Duration Fund - Direct Growth", 500_000),
        ("SBI Gold ETF", 700_000),
    ]
    for scheme, amount in lumpsum_configs:
        transactions.append({
            "client_id": client_id,
            "scheme_name": scheme,
            "transaction_type": TransactionType.LUMPSUM_BUY,
            "amount": amount * multiplier,
            "transaction_date": lumpsum_date,
        })

    return transactions


def _make_nav_history(portfolio_id: uuid.UUID, base_value: float):
    history = []
    for i in range(24):
        m = i - 23
        from datetime import date as d_
        import calendar
        today = date.today()
        year = today.year + (today.month + m - 1) // 12
        month = (today.month + m - 1) % 12 + 1
        last_day = calendar.monthrange(year, month)[1]
        record_date = d_(year, month, min(today.day, last_day))
        growth = 1 + (i / 23) * 0.30
        bench_growth = 1 + (i / 23) * 0.24
        history.append({
            "portfolio_id": portfolio_id,
            "record_date": record_date,
            "portfolio_value": round(base_value * growth),
            "benchmark_value": round(base_value * bench_growth),
        })
    return history


async def seed(session: AsyncSession) -> None:
    print("Seeding demo data...")

    # ── Staff users ───────────────────────────────────────────────────────────
    rm_user = User(
        email="rm@wealthmanager.com",
        hashed_password=DEMO_PASSWORD,
        role=UserRole.RM,
        is_active=True,
    )
    compliance_user = User(
        email="compliance@wealthmanager.com",
        hashed_password=DEMO_PASSWORD,
        role=UserRole.COMPLIANCE,
        is_active=True,
    )
    session.add_all([rm_user, compliance_user])
    await session.flush()

    # ── Clients + investor users ───────────────────────────────────────────────
    client_objects = []
    for i, data in enumerate(CLIENTS):
        client = Client(**data)
        session.add(client)
        await session.flush()

        # Create investor user for first 3 clients (demo logins)
        if i < 3:
            investor_user = User(
                email=data["email"],
                hashed_password=DEMO_PASSWORD,
                role=UserRole.INVESTOR,
                is_active=True,
                client_id=client.id,
            )
            session.add(investor_user)

        client_objects.append(client)
        multiplier = 1.0 + i * 0.5

        # Portfolio
        portfolio = Portfolio(**_make_portfolio(client.id, multiplier))
        session.add(portfolio)
        await session.flush()

        # Holdings
        for h in _make_holdings(portfolio.id, multiplier):
            session.add(Holding(**h))

        # Goals
        for g in _make_goals(client.id, data["age"]):
            session.add(Goal(**g))

        # NAV History
        for nav in _make_nav_history(portfolio.id, portfolio.total_invested):
            session.add(NAVHistory(**nav))

        # Transactions (SIP + lumpsum history for XIRR)
        for txn in _make_transactions(client.id, multiplier):
            session.add(Transaction(**txn))

    await session.flush()

    # ── Alerts ────────────────────────────────────────────────────────────────
    # Sunita Rao (index 2) — review overdue
    sunita = client_objects[2]
    session.add(Alert(
        client_id=sunita.id,
        alert_type=AlertType.REVIEW_OVERDUE,
        priority=AlertPriority.HIGH,
        message="Client not reviewed in 120 days. SEBI IA Regulation requires annual review.",
    ))

    # Arjun Kapoor (index 1) — concentration risk
    arjun = client_objects[1]
    session.add(Alert(
        client_id=arjun.id,
        alert_type=AlertType.CONCENTRATION_RISK,
        priority=AlertPriority.MEDIUM,
        message="Equity allocation at 68% exceeds recommended 60% for aggressive profile.",
    ))

    await session.commit()
    total_txns = sum(len(_make_transactions(uuid.uuid4(), 1.0)) for _ in CLIENTS)
    print(f"Seeded {len(CLIENTS)} clients, 2 staff users, alerts, ~{len(CLIENTS) * 51} transactions.")


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(WealthBase.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        await seed(session)

    await engine.dispose()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
