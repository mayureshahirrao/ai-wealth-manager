"""
tool_registry.py — Central registry for all AI tools.

Register tools once per request. The registry provides:
1. Tool schemas for Claude (passed in every API call)
2. Tool dispatch (route tool_use responses to the right handler)

Dependencies: base_tool.py (Tier 4)
"""

from typing import Optional
from app.ai.base_tool import BaseTool
from app.core.exceptions import AIToolExecutionError
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """Per-request registry for BaseTool instances."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool
        logger.debug("tool_registered", tool_name=tool.name)

    def get_schemas(self, tool_names: Optional[list[str]] = None) -> list[dict]:
        """Get Anthropic-compatible tool schemas."""
        if tool_names:
            return [self._tools[n].tool_schema for n in tool_names if n in self._tools]
        return [t.tool_schema for t in self._tools.values()]

    async def dispatch(self, tool_name: str, **kwargs) -> dict:
        """Execute a tool by name."""
        if tool_name not in self._tools:
            raise AIToolExecutionError(
                tool_name=tool_name,
                reason=f"Tool '{tool_name}' not found. Available: {list(self._tools.keys())}",
            )
        return await self._tools[tool_name](**kwargs)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, tool_name: str) -> bool:
        return tool_name in self._tools


# ─── Tool Name Constants ───────────────────────────────────────────────────────
class ToolNames:
    GET_PORTFOLIO_SUMMARY = "get_portfolio_summary"
    GET_GOAL_PROGRESS = "get_goal_progress"
    CALCULATE_TAX_LIABILITY = "calculate_tax_liability"
    GET_MARKET_DATA = "get_market_data"
    RUN_RETIREMENT_PROJECTION = "run_retirement_projection"

    # Subsets by agent role
    INVESTOR_TOOLS = [
        GET_PORTFOLIO_SUMMARY,
        GET_GOAL_PROGRESS,
        CALCULATE_TAX_LIABILITY,
        GET_MARKET_DATA,
        RUN_RETIREMENT_PROJECTION,
    ]

    RM_TOOLS = [
        GET_PORTFOLIO_SUMMARY,
        GET_GOAL_PROGRESS,
        CALCULATE_TAX_LIABILITY,
        RUN_RETIREMENT_PROJECTION,
    ]
