"""
get_market_data.py — AI tool for Indian market data.

Returns Nifty 50, Sensex, and sector index data.
Phase 5 will integrate live NSE/BSE APIs — currently uses realistic demo data.

Dependencies: base_tool.py (Tier 4)
"""

from datetime import date
from typing import Any

from app.ai.base_tool import BaseTool
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# ─── Demo Market Data (Phase 5 will replace with live API) ───────────────────
_DEMO_MARKET_DATA = {
    "indices": {
        "NIFTY_50": {
            "name": "Nifty 50",
            "value": 24_198.0,
            "change_1d_pct": 0.42,
            "change_1w_pct": 1.15,
            "change_1m_pct": 2.80,
            "change_1y_pct": 14.6,
            "52w_high": 26_277.0,
            "52w_low": 19_550.0,
            "pe_ratio": 22.1,
        },
        "SENSEX": {
            "name": "BSE Sensex",
            "value": 79_468.0,
            "change_1d_pct": 0.38,
            "change_1w_pct": 1.05,
            "change_1m_pct": 2.60,
            "change_1y_pct": 14.2,
            "52w_high": 85_978.0,
            "52w_low": 64_082.0,
        },
        "NIFTY_MIDCAP_100": {
            "name": "Nifty Midcap 100",
            "value": 56_342.0,
            "change_1d_pct": 0.55,
            "change_1y_pct": 18.4,
        },
        "NIFTY_SMALLCAP_100": {
            "name": "Nifty Smallcap 100",
            "value": 18_156.0,
            "change_1d_pct": 0.71,
            "change_1y_pct": 22.1,
        },
        "INDIA_VIX": {
            "name": "India VIX (Volatility Index)",
            "value": 14.2,
            "change_1d_pct": -3.1,
            "note": "VIX < 15 = low volatility (favorable for equities)",
        },
    },
    "debt_rates": {
        "repo_rate_pct": 6.50,
        "10yr_gsec_yield_pct": 7.15,
        "liquid_fund_7d_yield_pct": 7.20,
        "corporate_bond_aaa_pct": 7.80,
    },
    "gold": {
        "mcx_gold_per_10g": 72_450.0,
        "change_1d_pct": 0.12,
        "change_1y_pct": 16.8,
        "note": "MCX Gold (domestic), includes import duty",
    },
    "currency": {
        "USD_INR": 83.42,
        "EUR_INR": 90.85,
    },
    "market_context": {
        "as_of_date": date.today().isoformat(),
        "market_sentiment": "cautiously_bullish",
        "key_events": [
            "RBI MPC — next meeting in 6 weeks",
            "Q4 FY25 earnings season in progress",
            "Union Budget 2025 — July expected",
        ],
        "note": "Demo data — Phase 5 will integrate live NSE/BSE API feeds",
    },
}


class GetMarketDataTool(BaseTool):
    """Fetch current Indian market data — indices, rates, gold."""

    name = "get_market_data"
    description = (
        "Retrieves current Indian market data including: Nifty 50 and Sensex index levels, "
        "1-day/1-week/1-month/1-year returns, 52-week high/low, P/E ratio, "
        "RBI repo rate, 10-year G-Sec yield, gold prices (MCX), and USD/INR rate. "
        "Use this when the user asks about market conditions, index performance, "
        "interest rates, gold prices, or whether it's a good time to invest."
    )

    def __init__(self):
        pass  # No DB needed — market data is from external source

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
        data = dict(_DEMO_MARKET_DATA)

        if indices:
            filtered_indices = {
                k: v for k, v in data["indices"].items()
                if k in [i.upper() for i in indices]
            }
            data = {**data, "indices": filtered_indices}

        return data
