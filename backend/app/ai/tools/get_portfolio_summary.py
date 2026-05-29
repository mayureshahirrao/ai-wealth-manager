"""
get_portfolio_summary.py — AI tool to fetch a client's portfolio summary.

Queries Portfolio + Holdings from DB. Returns AUM, XIRR, asset allocation,
top holdings, and SIP details in a Claude-readable format.

Dependencies: base_tool.py, database models (Tier 4)
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.base_tool import BaseTool
from app.database.models import Portfolio, Holding, Client
from app.financial.currency_formatter import format_inr
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class GetPortfolioSummaryTool(BaseTool):
    """Fetch live portfolio data for a client from the database."""

    name = "get_portfolio_summary"
    description = (
        "Retrieves the client's current investment portfolio summary including: "
        "total invested amount, current value, XIRR (returns), asset allocation "
        "(equity/debt/gold), top holdings with scheme names and NAVs, and active SIPs. "
        "Use this when the user asks about their portfolio, investments, returns, or holdings."
    )

    def __init__(self, db: AsyncSession):
        self._db = db

    @property
    def tool_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "UUID of the client whose portfolio to retrieve",
                    }
                },
                "required": ["client_id"],
            },
        }

    async def _execute(self, client_id: str, **kwargs) -> dict[str, Any]:
        try:
            cid = uuid.UUID(client_id)
        except ValueError:
            return {"error": True, "message": f"Invalid client_id: {client_id}"}

        # Load client + portfolio + holdings in one query
        result = await self._db.execute(
            select(Client).where(Client.id == cid)
        )
        client = result.scalar_one_or_none()
        if not client:
            return {"error": True, "message": f"Client {client_id} not found"}

        port_result = await self._db.execute(
            select(Portfolio)
            .where(Portfolio.client_id == cid)
            .options(selectinload(Portfolio.holdings))
        )
        portfolio = port_result.scalar_one_or_none()
        if not portfolio:
            return {"error": True, "message": "No portfolio found for client"}

        holdings = portfolio.holdings

        # Asset allocation breakdown
        allocation: dict[str, float] = {}
        for h in holdings:
            asset_class = h.asset_class.value if hasattr(h.asset_class, "value") else str(h.asset_class)
            allocation[asset_class] = allocation.get(asset_class, 0) + h.current_value

        total_value = portfolio.current_value or sum(h.current_value for h in holdings)
        allocation_pct = {
            k: round(v / total_value * 100, 1) if total_value > 0 else 0
            for k, v in allocation.items()
        }

        # Unrealized gains for LTCG harvesting context
        total_invested = portfolio.total_invested or sum(h.invested_amount for h in holdings)
        unrealized_gain = total_value - total_invested

        # Active SIPs
        active_sips = [
            {
                "scheme": h.scheme_name,
                "monthly_sip": h.sip_amount,
            }
            for h in holdings if h.has_sip_active and h.sip_amount
        ]

        # Top holdings by current value
        sorted_holdings = sorted(holdings, key=lambda h: h.current_value, reverse=True)
        top_holdings = [
            {
                "scheme_name": h.scheme_name,
                "asset_class": h.asset_class.value if hasattr(h.asset_class, "value") else str(h.asset_class),
                "units": round(h.units, 2),
                "nav": h.nav,
                "invested_amount": round(h.invested_amount),
                "current_value": round(h.current_value),
                "gain_loss": round(h.current_value - h.invested_amount),
                "gain_loss_pct": round((h.current_value - h.invested_amount) / h.invested_amount * 100, 2)
                if h.invested_amount > 0 else 0,
            }
            for h in sorted_holdings[:5]
        ]

        return {
            "client_name": client.name,
            "risk_profile": client.risk_profile.value if hasattr(client.risk_profile, "value") else str(client.risk_profile),
            "total_invested": round(total_invested),
            "total_invested_formatted": format_inr(total_invested),
            "current_value": round(total_value),
            "current_value_formatted": format_inr(total_value),
            "unrealized_gain": round(unrealized_gain),
            "unrealized_gain_pct": round(unrealized_gain / total_invested * 100, 2) if total_invested > 0 else 0,
            "xirr_pct": round((portfolio.xirr or 0) * 100, 2),
            "benchmark_xirr_pct": round((portfolio.benchmark_xirr or 0) * 100, 2),
            "outperformance_pct": round(
                ((portfolio.xirr or 0) - (portfolio.benchmark_xirr or 0)) * 100, 2
            ),
            "asset_allocation_pct": allocation_pct,
            "top_holdings": top_holdings,
            "active_sips": active_sips,
            "total_sip_per_month": sum(h.sip_amount for h in holdings if h.has_sip_active and h.sip_amount),
        }
