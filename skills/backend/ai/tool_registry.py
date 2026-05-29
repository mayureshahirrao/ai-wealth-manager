"""
tool_registry.py — Central registry for all AI tools.

Register tools once at startup. The registry provides:
1. Tool schemas for Claude (passed in every API call)
2. Tool dispatch (route tool_use responses to the right handler)
3. Tool discovery for dynamic agent composition

Dependencies: base_tool.py (Tier 4)
Consumed by: base_agent.py, chat endpoint, financial plan generator
"""

from typing import Optional
from skills.backend.ai.base_tool import BaseTool
from skills.backend.core.exceptions import AIToolExecutionError
from skills.backend.core.logging_config import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """
    Singleton registry for all BaseTool instances.

    Usage at startup (in main.py or agent init):
        registry = ToolRegistry()
        registry.register(GetPortfolioSummaryTool(portfolio_repo))
        registry.register(CalculateTaxLiabilityTool(tax_repo))

    In agent:
        schemas = registry.get_schemas()           # → pass to Claude
        result = await registry.dispatch("get_portfolio_summary", client_id="x")
    """

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool instance. Tool name must be unique.

        Args:
            tool: An instantiated BaseTool subclass

        Raises:
            ValueError if a tool with the same name is already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool
        logger.info("tool_registered", tool_name=tool.name)

    def get_schemas(self, tool_names: Optional[list[str]] = None) -> list[dict]:
        """
        Get Anthropic-compatible tool schemas for Claude API calls.

        Args:
            tool_names: If provided, return schemas for only these tools.
                        If None, return all registered schemas.

        Returns:
            List of tool schema dicts ready for anthropic.messages.create(tools=...)
        """
        if tool_names:
            return [
                self._tools[name].tool_schema
                for name in tool_names
                if name in self._tools
            ]
        return [tool.tool_schema for tool in self._tools.values()]

    async def dispatch(self, tool_name: str, **kwargs) -> dict:
        """
        Execute a tool by name with given kwargs.

        This is called when Claude returns a tool_use block:
            for block in response.content:
                if block.type == "tool_use":
                    result = await registry.dispatch(block.name, **block.input)

        Raises:
            AIToolExecutionError if tool not found or execution fails
        """
        if tool_name not in self._tools:
            raise AIToolExecutionError(
                tool_name=tool_name,
                reason=f"Tool '{tool_name}' not found in registry. "
                       f"Registered tools: {list(self._tools.keys())}",
            )
        return await self._tools[tool_name](**kwargs)

    def list_tools(self) -> list[str]:
        """Return names of all registered tools."""
        return list(self._tools.keys())

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool instance by name."""
        return self._tools.get(name)

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, tool_name: str) -> bool:
        return tool_name in self._tools


# ─── Tool Name Constants (avoids magic strings) ───────────────────────────────
class ToolNames:
    """Use these constants instead of string literals when referencing tools."""
    GET_PORTFOLIO_SUMMARY = "get_portfolio_summary"
    GET_GOAL_PROGRESS = "get_goal_progress"
    RUN_RETIREMENT_PROJECTION = "run_retirement_projection"
    RUN_SCENARIO_ANALYSIS = "run_scenario_analysis"
    CALCULATE_TAX_LIABILITY = "calculate_tax_liability"
    QUERY_FINANCIAL_KNOWLEDGE = "query_financial_knowledge"
    GET_NEXT_BEST_ACTIONS = "get_next_best_actions"
    GENERATE_MEETING_PREP = "generate_meeting_prep"
    GET_MARKET_DATA = "get_market_data"
    CHECK_COMPLIANCE = "check_compliance"

    # Tool subsets used by different agents
    INVESTOR_TOOLS = [
        GET_PORTFOLIO_SUMMARY,
        GET_GOAL_PROGRESS,
        RUN_RETIREMENT_PROJECTION,
        RUN_SCENARIO_ANALYSIS,
        CALCULATE_TAX_LIABILITY,
        QUERY_FINANCIAL_KNOWLEDGE,
        GET_MARKET_DATA,
    ]

    RM_TOOLS = [
        GET_PORTFOLIO_SUMMARY,
        GET_NEXT_BEST_ACTIONS,
        GENERATE_MEETING_PREP,
        QUERY_FINANCIAL_KNOWLEDGE,
        CHECK_COMPLIANCE,
    ]

    PLANNING_TOOLS = [
        GET_PORTFOLIO_SUMMARY,
        GET_GOAL_PROGRESS,
        RUN_RETIREMENT_PROJECTION,
        CALCULATE_TAX_LIABILITY,
        QUERY_FINANCIAL_KNOWLEDGE,
    ]
