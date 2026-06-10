"""
test_compliance.py — Tests for /api/compliance/* endpoints.
"""

import uuid
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


async def _seed_audit_log(db_session: AsyncSession, client_id: uuid.UUID, n: int = 3):
    from app.database.models import AIAuditLog

    for i in range(n):
        db_session.add(AIAuditLog(
            id=uuid.uuid4(),
            client_id=client_id,
            tool_name="get_portfolio_summary",
            user_query=f"Test query {i}",
            ai_response_summary="Test response",
            confidence_score=0.85,
            disclaimer_injected=True,
            sebi_compliant=True,
            duration_ms=1200,
        ))
    await db_session.commit()


async def _seed_client(db_session: AsyncSession) -> uuid.UUID:
    from app.database.models import Client
    from app.database.base_model import RiskProfile
    from datetime import date

    client_id = uuid.uuid4()
    db_session.add(Client(
        id=client_id,
        name="Compliance Test Client",
        email=f"ctest_{client_id.hex[:8]}@demo.com",
        risk_profile=RiskProfile.MODERATE,
        annual_income=900000.0,
        date_of_birth=date(1980, 1, 1),
    ))
    await db_session.commit()
    return client_id


# ─── /api/compliance/audit-log ────────────────────────────────────────────────

async def test_audit_log_investor_forbidden(
    client: AsyncClient,
    auth_headers_investor: dict,
):
    """Investor role should not access audit log (rm_or_compliance required)."""
    resp = await client.get("/api/compliance/audit-log", headers=auth_headers_investor)
    assert resp.status_code == 403


async def test_audit_log_rm_allowed(
    client: AsyncClient,
    auth_headers_rm: dict,
):
    """RM can view audit log (require_rm_or_compliance)."""
    resp = await client.get("/api/compliance/audit-log", headers=auth_headers_rm)
    assert resp.status_code == 200


async def test_audit_log_returns_paginated_data(
    client: AsyncClient,
    auth_headers_compliance: dict,
    db_session: AsyncSession,
):
    cid = await _seed_client(db_session)
    await _seed_audit_log(db_session, cid, n=3)

    resp = await client.get("/api/compliance/audit-log", headers=auth_headers_compliance)
    assert resp.status_code == 200
    data = resp.json()["data"]
    # Should have logs + pagination metadata
    assert "logs" in data or isinstance(data, list) or "items" in data


async def test_audit_log_requires_auth(client: AsyncClient):
    resp = await client.get("/api/compliance/audit-log")
    assert resp.status_code == 401


# ─── /api/compliance/risk-alerts ──────────────────────────────────────────────

async def test_risk_alerts_returns_list(
    client: AsyncClient,
    auth_headers_compliance: dict,
):
    resp = await client.get("/api/compliance/risk-alerts", headers=auth_headers_compliance)
    assert resp.status_code == 200
    data = resp.json()["data"]
    # Response shape: {alerts: [...], summary: {...}, total: N}  OR  list
    assert isinstance(data, (list, dict))


async def test_risk_alerts_investor_forbidden(
    client: AsyncClient,
    auth_headers_investor: dict,
):
    resp = await client.get("/api/compliance/risk-alerts", headers=auth_headers_investor)
    assert resp.status_code == 403


# ─── /api/compliance/ai-governance ───────────────────────────────────────────

async def test_ai_governance_returns_metrics(
    client: AsyncClient,
    auth_headers_compliance: dict,
):
    resp = await client.get("/api/compliance/ai-governance", headers=auth_headers_compliance)
    assert resp.status_code == 200
    data = resp.json()["data"]
    # Should have some metric fields
    assert isinstance(data, dict)
