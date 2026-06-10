"""
get_market_data.py — AI tool for Indian market data.

v0.9.0: Live data via Yahoo Finance (yfinance) with 15-minute TTL cache.
        Falls back to stale cache or demo values on Yahoo Finance errors.

Dependencies: app.ai.market_data (Tier 4)
"""

from typing import Any

from app.ai.base_tool import BaseTool
from app.ai.market_data import get_market_data
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class GetMarketDataTool(BaseTool):
    """Fetch current Indian market data — indices, rates, gold."""

    name = "get_market_data"
    description = (
        "Retrieves current live Indian market data including: Nifty 50 and Sensex index levels, "
        "1-day/1-week/1-month/1-year returns, 52-week high/low, P/E ratio, "
        "RBI repo rate, 10-year G-Sec yield, gold prices (GOLDBEES ETF), and USD/INR rate. "
        "Data is live via Yahoo Finance (15-minute cache). "
        "Use this when the user asks about market conditions, index performance, "
        "interest rates, gold prices, or whether it's a good time to invest."
    )

    def __init__(self):
        pass  # No DB needed — market data from Yahoo Finance

    @property
    def tool_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "indices": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Optional list of specific indices to return: "
                            "NIFTY_50, SENSEX, NIFTY_MIDCAP_100, NIFTY_SMALLCAP_100, INDIA_VIX. "
                            "If omitted, all indices are returned."
                        ),
                    }
                },
                "required": [],
            },
        }

    async def _execute(
        self,
        indices: list[str] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        return await get_market_data(indices_filter=indices)
