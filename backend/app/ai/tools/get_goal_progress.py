"""
get_goal_progress.py — AI tool to fetch goal feasibility and progress.

Queries Goals from DB and runs GoalAssessment for each goal.
Returns feasibility scores, shortfalls, and actionable recommendations.

Dependencies: base_tool.py, goal_engine, database models (Tier 4)
"""

import uuid
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base_tool import BaseTool
from app.database.models import Goal, Client
from app.financial.goal_engine import GoalAssessment
from app.financial.currency_formatter import format_inr
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class GetGoalProgressTool(BaseTool):
    """Fetch financial goal progress with feasibility analysis."""

    name = "get_goal_progress"
    description = (
        "Retrieves the client's financial goals (retirement, child education, home purchase, etc.) "
        "with feasibility scores (0-100), projected corpus, shortfall analysis, and recommendations. "
        "Use this when the user asks about their goals, whether they are on track, "
        "how much more they need to save, or goal-related SIP recommendations."
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
                        "description": "UUID of the client whose goals to retrieve",
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

        client_result = await self._db.execute(
            select(Client).where(Client.id == cid)
        )
        client = client_result.scalar_one_or_none()
        if not client:
            return {"error": True, "message": f"Client {client_id} not found"}

        goals_result = await self._db.execute(
            select(Goal).where(Goal.client_id == cid).order_by(Goal.priority)
        )
        goals = goals_result.scalars().all()

        if not goals:
            return {
                "client_name": client.name,
                "goals": [],
                "message": "No goals found for this client. Consider setting up financial goals.",
            }

        today = date.today()
        goal_assessments = []

        for goal in goals:
            years_remaining = max(0, goal.target_year - today.year)
            target_date = date(goal.target_year, 12, 31)

            assessment = GoalAssessment(
                goal_type=goal.goal_type.value if hasattr(goal.goal_type, "value") else str(goal.goal_type),
                target_amount=goal.target_amount,
                target_date=target_date,
                current_corpus=goal.current_corpus,
                monthly_sip=goal.monthly_sip,
                years_remaining=years_remaining,
            )

            data = assessment.to_dict()
            data["goal_name"] = goal.goal_name
            data["priority"] = goal.priority
            data["target_year"] = goal.target_year
            data["target_amount_formatted"] = format_inr(goal.target_amount)
            data["projected_corpus_formatted"] = format_inr(assessment.projected_corpus)
            data["shortfall_formatted"] = format_inr(assessment.shortfall) if assessment.shortfall > 0 else "₹0"
            goal_assessments.append(data)

        # Summary stats
        on_track = sum(1 for g in goal_assessments if g["status"] == "on_track")
        at_risk = sum(1 for g in goal_assessments if g["status"] == "at_risk")
        avg_score = sum(g["feasibility_score"] for g in goal_assessments) // len(goal_assessments)

        return {
            "client_name": client.name,
            "total_goals": len(goal_assessments),
            "goals_on_track": on_track,
            "goals_at_risk": at_risk,
            "average_feasibility_score": avg_score,
            "goals": goal_assessments,
        }
