"""
test_auth.py — Tests for /api/auth/login and /api/auth/me.
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


async def _seed_user(db_session: AsyncSession, email: str, role: str) -> None:
    from app.database.models import User
    from app.database.base_model import UserRole
    from app.auth.password_utils import hash_password

    db_session.add(User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hash_password("pass1234"),
        role=UserRole(role),
        is_active=True,
    ))
    await db_session.commit()


# ─── Login ────────────────────────────────────────────────────────────────────

async def test_login_success(client: AsyncClient, db_session: AsyncSession):
    await _seed_user(db_session, "login_test@demo.com", "investor")
    resp = await client.post(
        "/api/auth/login",
        json={"email": "login_test@demo.com", "password": "pass1234"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body["data"]
    assert body["data"]["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, db_session: AsyncSession):
    await _seed_user(db_session, "wrongpass@demo.com", "investor")
    resp = await client.post(
        "/api/auth/login",
        json={"email": "wrongpass@demo.com", "password": "badpassword"},
    )
    assert resp.status_code == 401


async def test_login_unknown_user(client: AsyncClient):
    resp = await client.post(
        "/api/auth/login",
        json={"email": "nobody@demo.com", "password": "pass1234"},
    )
    assert resp.status_code == 401


async def test_login_missing_fields(client: AsyncClient):
    resp = await client.post("/api/auth/login", json={"email": "x@y.com"})
    assert resp.status_code == 422  # Validation error


# ─── /me ─────────────────────────────────────────────────────────────────────

async def test_me_returns_current_user(
    client: AsyncClient,
    auth_headers_investor: dict,
):
    resp = await client.get("/api/auth/me", headers=auth_headers_investor)
    assert resp.status_code == 200
    body = resp.json()
    assert "email" in body["data"]
    assert body["data"]["role"] == "investor"


async def test_me_requires_auth(client: AsyncClient):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


async def test_me_rm_role(client: AsyncClient, auth_headers_rm: dict):
    resp = await client.get("/api/auth/me", headers=auth_headers_rm)
    assert resp.status_code == 200
    assert resp.json()["data"]["role"] == "rm"


async def test_me_compliance_role(
    client: AsyncClient, auth_headers_compliance: dict
):
    resp = await client.get("/api/auth/me", headers=auth_headers_compliance)
    assert resp.status_code == 200
    assert resp.json()["data"]["role"] == "compliance"
