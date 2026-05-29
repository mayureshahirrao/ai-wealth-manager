"""
run_retirement_projection.py — AI tool for retirement readiness analysis.

Runs assess_retirement_readiness() from goal_engine with client's current
retirement corpus, SIP, and desired income.

Dependencies: base_tool.py, goal_engine, database models (Tier 4)
"""

import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.base_tool import BaseTool
from app.database.models import Client, Portfolio, Goal
from app.database.base_model import GoalType
from app.financial.goal_engine import assess_retirement_readiness
from app.financial.currency_formatter import format_inr
from app.core.logging_config import get_logger

logger = get_logger(__name__)

DEFAULT_RETIREMENT_AGE = 60
DEFAULT_MONTHLY_INCOME = 100_000  # ₹1L/month in today's ₹
DEFAULT_RETIREMENT_YEARS = 25


class RunRetirementProjectionTool(BaseTool):
    """Run comprehensive retirement readiness projection for a client."""

    name = "run_retirement_projection"
    description = (
        "Runs a comprehensive retirement readiness projection for the client. "
        "Calculates required corpus, projected corpus based on current savings and SIPs, "
        "shortfall analysis, and how much more they need to save monthly. "
        "Uses inflation-adjusted targets (6% CPI). "
        "Use this when the user asks about retirement planning, retirement corpus, "
        "whether they can retire at a certain age, or how much they need for retirement."
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
                    "target_retirement_age": {
                        "type": "integer",
                        "description": (
                            "Target age at retirement (default: 60). "
                            "Use if client specifies a different retirement age."
                        ),
                    },
                    "desired_monthly_income": {
                        "type": "number",
                        "description": (
                            "Desired monthly income in retirement in today's ₹ (default: ₹1,00,000). "
                            "Adjust based on client's lifestyle expectations."
                        ),
                    },
                },
                "required": ["client_id"],
            },
        }

    async def _execute(
        self,
        client_id: str,
        target_retirement_age: Optional[int] = None,
        desired_monthly_income: Optional[float] = None,
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

        current_age = client.age or 35
        retirement_age = target_retirement_age or DEFAULT_RETIREMENT_AGE
        monthly_income = desired_monthly_income or DEFAULT_MONTHLY_INCOME

        if retirement_age <= current_age:
            return {
                "error": True,
                "message": f"Target retirement age ({retirement_age}) must be greater than current age ({current_age})",
            }

        # Get retirement goal from DB (if any)
        goals_result = await self._db.execute(
            select(Goal).where(Goal.client_id == cid)
        )
        goals = goals_result.scalars().all()

        retirement_goal = next(
            (g for g in goals if g.goal_type == GoalType.RETIREMENT),
            None
        )

        current_corpus = retirement_goal.current_corpus if retirement_goal else 0.0
        monthly_sip = retirement_goal.monthly_sip if retirement_goal else 0.0

        # Fallback: estimate from portfolio
        if current_corpus == 0:
            port_result = await self._db.execute(
                select(Portfolio).where(Portfolio.client_id == cid)
            )
            portfolio = port_result.scalar_one_or_none()
            if portfolio:
                # Rough estimate: 40% of portfolio is retirement savings
                current_corpus = (portfolio.current_value or 0) * 0.40

        projection = assess_retirement_readiness(
            current_age=current_age,
            target_retirement_age=retirement_age,
            current_retirement_corpus=current_corpus,
            monthly_retirement_sip=monthly_sip,
            desired_monthly_income=monthly_income,
            expected_retirement_years=DEFAULT_RETIREMENT_YEARS,
        )

        if "error" in projection:
            return projection

        return {
            "client_name": client.name,
            "current_age": current_age,
            "target_retirement_age": retirement_age,
            "years_to_retirement": projection["years_to_retirement"],
            "desired_monthly_income_today": round(monthly_income),
            "desired_monthly_income_at_retirement": projection["monthly_income_at_retirement"],
            "desired_monthly_income_formatted": format_inr(monthly_income),
            "current_retirement_corpus": round(current_corpus),
            "current_retirement_corpus_formatted": format_inr(current_corpus),
            "current_monthly_retirement_sip": round(monthly_sip),
            "required_corpus_lakhs": projection["required_corpus_lakhs"],
            "required_corpus_formatted": format_inr(projection["required_corpus_lakhs"] * 100_000),
            "projected_corpus_lakhs": projection["projected_corpus_lakhs"],
            "projected_corpus_formatted": format_inr(projection["projected_corpus_lakhs"] * 100_000),
            "shortfall_lakhs": projection["shortfall_lakhs"],
            "shortfall_formatted": format_inr(projection["shortfall_lakhs"] * 100_000),
            "feasibility_score": projection["feasibility_score"],
            "on_track": projection["on_track"],
            "additional_monthly_sip_needed": projection["additional_monthly_sip_needed"],
            "additional_sip_formatted": format_inr(projection["additional_monthly_sip_needed"]),
            "recommendation": projection["recommendation"],
            "assumptions": {
                "inflation_rate_pct": 6.0,
                "expected_return_pct": 12.0,
                "post_retirement_return_pct": 6.0,
                "retirement_duration_years": DEFAULT_RETIREMENT_YEARS,
            },
        }
