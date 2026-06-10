"""
test_health.py — Tests for /health and basic app startup.
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_health_returns_ok(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body


async def test_health_version_format(client: AsyncClient):
    resp = await client.get("/health")
    version = resp.json()["version"]
    parts = version.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


async def test_docs_accessible(client: AsyncClient):
    """Swagger UI should be served."""
    resp = await client.get("/docs")
    assert resp.status_code == 200


async def test_unknown_route_returns_404(client: AsyncClient):
    resp = await client.get("/api/nonexistent")
    assert resp.status_code == 404
