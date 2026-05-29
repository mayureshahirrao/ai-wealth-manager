"""
api_client.py — FastAPI TestClient wrapper for integration tests.

Provides:
- WealthManagerTestClient: pre-authenticated clients for each role
- Convenience methods for common test operations
- Response assertion helpers

Dependencies: fixtures.py, mock_data.py (Tier 5)
Usage:
    from skills.backend.testing.api_client import WealthManagerTestClient

    async def test_portfolio(investor_headers):
        client = WealthManagerTestClient(app, investor_headers)
        data = client.get_portfolio("C001")
        assert data["xirr"] > 0
"""

from typing import Any
from httpx import AsyncClient
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ─── Sync Test Client ─────────────────────────────────────────────────────────

class WealthManagerTestClient:
    """
    Thin wrapper around FastAPI TestClient with role-based auth headers
    and assertion helpers.
    """

    def __init__(self, app: FastAPI, headers: dict[str, str]):
        self._client = TestClient(app, raise_server_exceptions=False)
        self._headers = headers

    # ── Auth ──────────────────────────────────────────────────────────────────

    def post_login(self, email: str, password: str) -> dict:
        r = self._client.post("/api/auth/login", json={"email": email, "password": password})
        return r.json()

    # ── Portfolio ──────────────────────────────────────────────────────────────

    def get_portfolio(self, client_id: str) -> dict:
        r = self._client.get(f"/api/clients/{client_id}/portfolio", headers=self._headers)
        assert r.status_code == 200, f"Portfolio fetch failed: {r.text}"
        return r.json()

    def get_goals(self, client_id: str) -> list[dict]:
        r = self._client.get(f"/api/clients/{client_id}/goals", headers=self._headers)
        assert r.status_code == 200, f"Goals fetch failed: {r.text}"
        return r.json()

    def get_tax_summary(self, client_id: str) -> dict:
        r = self._client.get(f"/api/clients/{client_id}/tax-summary", headers=self._headers)
        assert r.status_code == 200, f"Tax summary failed: {r.text}"
        return r.json()

    def get_nav_history(self, client_id: str) -> list[dict]:
        r = self._client.get(f"/api/clients/{client_id}/nav-history", headers=self._headers)
        assert r.status_code == 200, f"NAV history failed: {r.text}"
        return r.json()

    # ── Chat ──────────────────────────────────────────────────────────────────

    def post_chat(self, client_id: str, query: str) -> Any:
        r = self._client.post(
            "/api/chat/message",
            json={"client_id": client_id, "query": query},
            headers=self._headers,
        )
        return r

    # ── RM ────────────────────────────────────────────────────────────────────

    def get_clients(self) -> list[dict]:
        r = self._client.get("/api/clients", headers=self._headers)
        assert r.status_code == 200, f"Clients list failed: {r.text}"
        return r.json()

    def get_next_actions(self) -> list[dict]:
        r = self._client.get("/api/rm/next-actions", headers=self._headers)
        assert r.status_code == 200, f"Next actions failed: {r.text}"
        return r.json()

    def get_meeting_prep(self, client_id: str) -> dict:
        r = self._client.get(f"/api/rm/meeting-prep/{client_id}", headers=self._headers)
        assert r.status_code == 200, f"Meeting prep failed: {r.text}"
        return r.json()

    # ── Compliance ────────────────────────────────────────────────────────────

    def get_audit_log(self, params: dict | None = None) -> dict:
        r = self._client.get("/api/compliance/audit-log", headers=self._headers, params=params)
        assert r.status_code == 200, f"Audit log failed: {r.text}"
        return r.json()

    def get_risk_alerts(self) -> list[dict]:
        r = self._client.get("/api/compliance/risk-alerts", headers=self._headers)
        assert r.status_code == 200, f"Risk alerts failed: {r.text}"
        return r.json()

    # ── Assertion Helpers ─────────────────────────────────────────────────────

    def assert_forbidden(self, response) -> None:
        assert response.status_code == 403, (
            f"Expected 403 Forbidden, got {response.status_code}: {response.text}"
        )

    def assert_unauthorized(self, response) -> None:
        assert response.status_code == 401, (
            f"Expected 401 Unauthorized, got {response.status_code}: {response.text}"
        )

    def assert_success(self, response) -> dict:
        assert response.status_code == 200, (
            f"Expected 200 OK, got {response.status_code}: {response.text}"
        )
        data = response.json()
        assert data.get("success") is True, f"API returned success=False: {data}"
        return data

    def assert_validation_error(self, response) -> None:
        assert response.status_code == 422, (
            f"Expected 422 Validation Error, got {response.status_code}: {response.text}"
        )

    # ── Raw Access ────────────────────────────────────────────────────────────

    def get(self, url: str, **kwargs):
        return self._client.get(url, headers=self._headers, **kwargs)

    def post(self, url: str, json: dict | None = None, **kwargs):
        return self._client.post(url, json=json, headers=self._headers, **kwargs)


# ─── Async Test Client Factory ────────────────────────────────────────────────

async def make_async_client(app: FastAPI, headers: dict[str, str]) -> AsyncClient:
    """
    Create an AsyncClient for tests that need async HTTP (e.g., SSE streaming tests).

    Usage:
        async with make_async_client(app, rm_headers) as client:
            r = await client.get("/api/rm/next-actions")
    """
    return AsyncClient(app=app, base_url="http://testserver", headers=headers)


# ─── Role-Based Client Factory ────────────────────────────────────────────────

def build_investor_client(app: FastAPI, investor_headers: dict) -> WealthManagerTestClient:
    return WealthManagerTestClient(app, investor_headers)

def build_rm_client(app: FastAPI, rm_headers: dict) -> WealthManagerTestClient:
    return WealthManagerTestClient(app, rm_headers)

def build_compliance_client(app: FastAPI, compliance_headers: dict) -> WealthManagerTestClient:
    return WealthManagerTestClient(app, compliance_headers)

def build_unauthenticated_client(app: FastAPI) -> WealthManagerTestClient:
    return WealthManagerTestClient(app, {})
