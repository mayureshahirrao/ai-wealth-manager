"""
calculate_tax_liability.py — AI tool for Indian tax calculation and regime comparison.

Compares Old vs New regime, calculates LTCG, and identifies tax harvesting opportunities.

Dependencies: base_tool.py, tax_calculator, database models (Tier 4)
"""

import uuid
from datetime import date
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.base_tool import BaseTool
from app.database.models import Client, Portfolio, Holding
from app.database.base_model import AssetClass
from app.financial.tax_calculator import compare_tax_regimes, ltcg_harvesting_opportunity
from app.financial.currency_formatter import format_inr
from app.core.logging_config import get_logger

logger = get_logger(__name__)

LTCG_HOLDING_MONTHS = 12  # Equity LTCG qualifying period


class CalculateTaxLiabilityTool(BaseTool):
    """Calculate tax liability with Old/New regime comparison and LTCG analysis."""

    name = "calculate_tax_liability"
    description = (
        "Calculates Indian income tax liability comparing Old Regime vs New Regime (Budget 2024). "
        "Also computes LTCG tax on equity holdings, identifies tax harvesting opportunities "
        "(booking up to ₹1.25L LTCG annually tax-free), and recommends the better tax regime. "
        "Use this when the user asks about taxes, tax savings, which regime to choose, "
        "LTCG, STCG, or tax-loss harvesting."
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
                        "description": "UUID of the client",
                    },
                    "gross_income": {
                        "type": "number",
                        "description": (
                            "Annual gross income in ₹ (optional — uses client's income from DB if not provided)"
                        ),
                    },
                    "age": {
                        "type": "integer",
                        "description": "Client age in years (optional — uses DB age if not provided)",
                    },
                },
                "required": ["client_id"],
            },
        }

    async def _execute(
        self,
        client_id: str,
        gross_income: Optional[float] = None,
        age: Optional[int] = None,
        **kwargs,
    ) -> dict[str, Any]:
        try:
            cid = uuid.UUID(client_id)
        except ValueError:
            return {"error": True, "message": f"Invalid client_id: {client_id}"}

        client_result = await self._db.execute(
            select(Client).where(Client.id == cid)
        )
        client = client_result.scalar_one_or_none()
        if not client:
            return {"error": True, "message": f"Client {client_id} not found"}

        # Use provided values or fall back to DB
        income = gross_income or client.annual_income or 0
        client_age = age or client.age or 35

        if income <= 0:
            return {
                "error": True,
                "message": "No income data available. Please provide gross_income.",
            }

        # Tax regime comparison
        regime_comparison = compare_tax_regimes(
            gross_income=income,
            age=client_age,
        )

        # LTCG analysis from holdings
        port_result = await self._db.execute(
            select(Portfolio)
            .where(Portfolio.client_id == cid)
            .options(selectinload(Portfolio.holdings))
        )
        portfolio = port_result.scalar_one_or_none()

        ltcg_data = {}
        if portfolio and portfolio.holdings:
            today = date.today()
            unrealized_ltcg = 0.0

            for holding in portfolio.holdings:
                # Only equity holdings qualify for LTCG
                asset_class = holding.asset_class
                is_equity = (
                    asset_class == AssetClass.EQUITY or
                    (hasattr(asset_class, "value") and asset_class.value == "equity")
                )

                if not is_equity or not holding.purchase_date:
                    continue

                # Check if holding qualifies for LTCG (held > 12 months)
                months_held = (
                    (today.year - holding.purchase_date.year) * 12
                    + (today.month - holding.purchase_date.month)
                )

                if months_held >= LTCG_HOLDING_MONTHS:
                    gain = holding.current_value - holding.invested_amount
                    if gain > 0:
                        unrealized_ltcg += gain

            ltcg_data = ltcg_harvesting_opportunity(
                unrealized_gains=unrealized_ltcg,
                current_fy_realized_gains=0.0,  # Would need transaction history for accuracy
            )

        # Current regime from DB
        current_regime = client.tax_regime.value if hasattr(client.tax_regime, "value") else str(client.tax_regime)

        return {
            "client_name": client.name,
            "current_tax_regime": current_regime,
            "gross_income": round(income),
            "gross_income_formatted": format_inr(income),
            "age": client_age,
            "tax_comparison": regime_comparison,
            "ltcg_analysis": ltcg_data,
            "summary": (
                f"On ₹{format_inr(income)} income, {regime_comparison['recommended_regime']} "
                f"saves ₹{format_inr(regime_comparison['tax_savings_if_switching'])} vs the other regime."
            ),
        }
