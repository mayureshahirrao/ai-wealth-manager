"""
test_market_data.py — Tests for the live market data module and /api/market/* endpoint.
"""

import pytest
from unittest.mock import patch, AsyncMock

pytestmark = pytest.mark.asyncio


# ─── Unit tests for market_data module ───────────────────────────────────────

async def test_get_market_data_returns_expected_keys():
    """get_market_data() returns dict with expected top-level keys."""
    from app.ai.market_data import get_market_data

    data = await get_market_data()
    assert "indices" in data
    assert "debt_rates" in data
    assert "gold" in data
    assert "currency" in data
    assert "market_context" in data


async def test_get_market_data_contains_nifty():
    from app.ai.market_data import get_market_data

    data = await get_market_data()
    # Either live fetch succeeded or fallback was used — either way NIFTY_50 should be present
    assert "NIFTY_50" in data["indices"]
    nifty = data["indices"]["NIFTY_50"]
    assert "value" in nifty
    assert nifty["value"] > 0


async def test_get_market_data_indices_filter():
    from app.ai.market_data import get_market_data

    data = await get_market_data(indices_filter=["NIFTY_50"])
    assert "NIFTY_50" in data["indices"]
    # SENSEX should be filtered out
    assert "SENSEX" not in data["indices"]


async def test_get_market_data_fallback_on_error():
    """On yfinance failure, fallback data (or stale cache) is returned — never raises."""
    from app.ai import market_data as md

    # Patch _fetch_live_data to raise
    with patch.object(md, "_fetch_live_data", side_effect=Exception("network error")):
        # Clear cache to force a fetch attempt
        md._cache = None
        md._cache_timestamp = 0.0

        data = await md.get_market_data()
        # Should get fallback, not exception
        assert "indices" in data
        assert "NIFTY_50" in data["indices"]


async def test_market_data_cache_is_used():
    """Second call within TTL uses cache — _fetch_live_data called only once."""
    from app.ai import market_data as md
    import time

    call_count = 0

    def mock_fetch():
        nonlocal call_count
        call_count += 1
        return md._FALLBACK

    with patch.object(md, "_fetch_live_data", side_effect=mock_fetch):
        md._cache = None
        md._cache_timestamp = 0.0

        await md.get_market_data()  # First call — fetches
        await md.get_market_data()  # Second call — should use cache

    assert call_count == 1, "Cache should prevent second fetch within TTL"


async def test_debt_rates_contain_repo_rate():
    from app.ai.market_data import get_market_data

    data = await get_market_data()
    assert "repo_rate_pct" in data["debt_rates"]
    assert data["debt_rates"]["repo_rate_pct"] > 0
