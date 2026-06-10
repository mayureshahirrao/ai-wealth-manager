"""
conftest.py — pytest fixtures for AI Wealth Manager backend tests.

Uses an in-memory SQLite database (via aiosqlite) so tests run without
a running PostgreSQL instance. All fixtures are async-compatible via
pytest-asyncio (asyncio_mode = "auto" set in pytest.ini).

Key fixtures:
  - engine     : in-memory async SQLite engine
  - db_session : async session with rollback-per-test isolation
  - client     : httpx AsyncClient with the FastAPI app
  - auth_headers_investor / auth_headers_rm / auth_headers_compliance :
                 JWT Authorization headers for each role
"""

import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

from app.main import app
from app.database.base_model import WealthBase
from app.database.transaction import get_db

# ─── Patch JSONB → JSON so SQLite can create tables ──────────────────────────
# PostgreSQL JSONB is not supported by SQLite; remap for tests only.
JSONB.__init__ = lambda self, *a, **kw: super(JSONB, self).__init__(*a, **kw)

import sqlalchemy.dialects.sqlite.base as _sqlite_base  # noqa: E402

_orig_visit_JSONB = getattr(_sqlite_base.SQLiteTypeCompiler, "visit_JSONB", None)
if not _orig_visit_JSONB:
    _sqlite_base.SQLiteTypeCompiler.visit_JSONB = (
        lambda self, type_, **kw: "JSON"
    )

# ─── Test DB (SQLite in-memory) ───────────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Session-scoped in-memory SQLite engine."""
    eng = create_async_engine(TEST_DB_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(WealthBase.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Per-test async session — rolls back after each test."""
    TestSession = async_sessionmaker(engine, expire_on_commit=False)
    async with TestSession() as session:
        yield session
        await session.rollback()


# ─── App Client ───────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """httpx AsyncClient wired to the FastAPI app with test DB override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ─── Demo User Helpers ────────────────────────────────────────────────────────

async def _create_user_and_login(
    client: AsyncClient,
    db_session: AsyncSession,
    email: str,
    role: str,
    suffix: str = "",
) -> dict:
    """Create a user row and return auth headers."""
    from app.database.models import User
    from app.database.base_model import UserRole
    from app.auth.password_utils import hash_password

    # Make email unique per call to avoid UNIQUE constraint across tests
    unique_email = f"{uuid.uuid4().hex[:8]}_{email}" if not suffix else f"{suffix}_{email}"
    role_enum = UserRole(role)
    user = User(
        id=uuid.uuid4(),
        email=unique_email,
        hashed_password=hash_password("testpass123"),
        role=role_enum,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": "testpass123"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def auth_headers_investor(client: AsyncClient, db_session: AsyncSession) -> dict:
    return await _create_user_and_login(
        client, db_session, "test_investor@demo.com", "investor"
    )


@pytest_asyncio.fixture
async def auth_headers_rm(client: AsyncClient, db_session: AsyncSession) -> dict:
    return await _create_user_and_login(
        client, db_session, "test_rm@demo.com", "rm"
    )


@pytest_asyncio.fixture
async def auth_headers_compliance(
    client: AsyncClient, db_session: AsyncSession
) -> dict:
    return await _create_user_and_login(
        client, db_session, "test_compliance@demo.com", "compliance"
    )
