"""
fixtures.py — Shared pytest fixtures for backend tests.

Import these fixtures in conftest.py. They provide:
- Async DB session (test database)
- Pre-seeded client data
- Auth tokens for each role
- Mock Claude client (no real API calls in tests)

Dependencies: mock_data.py, base_model.py, jwt_handler.py (Tier 5)
Consumed by: All backend test files
"""

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from skills.backend.database.base_model import WealthBase, UserRole
from skills.backend.auth.jwt_handler import create_access_token
from skills.backend.auth.password_utils import hash_password
from skills.backend.testing.mock_data import MOCK_CLIENTS, DEMO_CREDENTIALS
import uuid


# ─── Test Database Setup ──────────────────────────────────────────────────────

TEST_DB_URL = "postgresql+asyncpg://wealth:wealth@localhost:5432/wealth_manager_test"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    """Create all tables in test DB before tests, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(WealthBase.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(WealthBase.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an isolated async DB session per test.
    Rolls back all changes after each test.

    Usage:
        async def test_create_client(db_session):
            repo = ClientRepository(Client, db_session)
            client = await repo.create({...})
            assert client.id is not None
    """
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


# ─── Auth Token Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def investor_token() -> str:
    """JWT token for investor role (Priya Sharma)."""
    return create_access_token(
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email="priya.sharma@demo.com",
        role=UserRole.INVESTOR,
    )


@pytest.fixture
def rm_token() -> str:
    """JWT token for RM role."""
    return create_access_token(
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000010"),
        email="rm@demo.com",
        role=UserRole.RM,
    )


@pytest.fixture
def compliance_token() -> str:
    """JWT token for compliance role."""
    return create_access_token(
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000020"),
        email="compliance@demo.com",
        role=UserRole.COMPLIANCE,
    )


# ─── Auth Headers ─────────────────────────────────────────────────────────────

@pytest.fixture
def investor_headers(investor_token) -> dict:
    return {"Authorization": f"Bearer {investor_token}"}


@pytest.fixture
def rm_headers(rm_token) -> dict:
    return {"Authorization": f"Bearer {rm_token}"}


@pytest.fixture
def compliance_headers(compliance_token) -> dict:
    return {"Authorization": f"Bearer {compliance_token}"}


# ─── Mock Claude Client ───────────────────────────────────────────────────────

@pytest.fixture
def mock_claude_client():
    """
    Mock Claude client that returns predictable responses without API calls.

    Usage:
        def test_chat(mock_claude_client, monkeypatch):
            monkeypatch.setattr(
                "skills.backend.ai.claude_client.get_claude_client",
                lambda: mock_claude_client
            )
    """
    mock = MagicMock()
    mock.complete = AsyncMock(return_value=MagicMock(
        content=[MagicMock(text="Mock AI response", type="text")],
        stop_reason="end_turn",
        usage=MagicMock(input_tokens=100, output_tokens=50),
    ))
    mock.complete_with_tools = AsyncMock(return_value=MagicMock(
        content=[MagicMock(text="Mock AI response with tools", type="text")],
        stop_reason="end_turn",
        usage=MagicMock(input_tokens=150, output_tokens=75),
    ))
    return mock


# ─── Mock Portfolio Tool ──────────────────────────────────────────────────────

@pytest.fixture
def mock_portfolio_summary():
    """Standard portfolio summary for cli-001 (Priya Sharma)."""
    return {
        "client_id": "cli-001",
        "total_value": 4_200_000,
        "total_value_lakhs": 42.0,
        "xirr_pct": 13.4,
        "holdings_count": 5,
        "allocation_by_asset_class": {
            "equity": 0.60,
            "debt": 0.30,
            "gold": 0.10,
        },
    }
