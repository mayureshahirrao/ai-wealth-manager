"""
app/ai/tools/__init__.py — Tool factory for the AI module.

Use build_tool_registry() to create a per-request registry with all tools wired to the DB session.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.tool_registry import ToolRegistry, ToolNames
from app.ai.tools.get_portfolio_summary import GetPortfolioSummaryTool
from app.ai.tools.get_goal_progress import GetGoalProgressTool
from app.ai.tools.calculate_tax_liability import CalculateTaxLiabilityTool
from app.ai.tools.get_market_data import GetMarketDataTool
from app.ai.tools.run_retirement_projection import RunRetirementProjectionTool


def build_tool_registry(db: AsyncSession) -> ToolRegistry:
    """
    Create a per-request ToolRegistry with all 5 tools registered.

    The DB session is injected into each tool that needs it.
    GetMarketDataTool doesn't need DB access.

    Args:
        db: SQLAlchemy async session for this request

    Returns:
        ToolRegistry with all tools ready to dispatch
    """
    registry = ToolRegistry()
    registry.register(GetPortfolioSummaryTool(db))
    registry.register(GetGoalProgressTool(db))
    registry.register(CalculateTaxLiabilityTool(db))
    registry.register(GetMarketDataTool())
    registry.register(RunRetirementProjectionTool(db))
    return registry


__all__ = [
    "build_tool_registry",
    "GetPortfolioSummaryTool",
    "GetGoalProgressTool",
    "CalculateTaxLiabilityTool",
    "GetMarketDataTool",
    "RunRetirementProjectionTool",
]
