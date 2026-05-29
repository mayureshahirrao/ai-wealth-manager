"""
agent_tester.py — Utilities for testing LangGraph agents deterministically.

Agent tests need to verify:
1. Correct tools are called with correct parameters
2. Agent handles tool failures gracefully
3. Response includes SEBI disclaimer
4. Multi-step graph completes all expected nodes

Dependencies: base_agent.py, tool_registry.py, mock_data.py (Tier 5)
Consumed by: test_wealth_assistant.py, test_financial_plan_agent.py
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

from skills.backend.ai.tool_registry import ToolRegistry
from skills.backend.ai.base_tool import BaseTool


class MockTool(BaseTool):
    """
    Test double for any BaseTool. Returns a fixed response when called.

    Usage:
        mock_portfolio_tool = MockTool(
            name="get_portfolio_summary",
            description="Mock portfolio tool",
            response={"total_value_lakhs": 42.0, "xirr_pct": 13.4}
        )
    """
    def __init__(self, name: str, description: str, response: dict):
        self.name = name
        self.description = description
        self._response = response
        self._call_count = 0
        self._last_kwargs = {}

    @property
    def tool_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "client_id": {"type": "string"}
                },
            }
        }

    async def _execute(self, **kwargs) -> dict:
        self._call_count += 1
        self._last_kwargs = kwargs
        return self._response

    def assert_called_once(self):
        assert self._call_count == 1, f"Expected 1 call, got {self._call_count}"

    def assert_called_with_client_id(self, client_id: str):
        assert self._last_kwargs.get("client_id") == client_id


class FailingMockTool(BaseTool):
    """Tool that always raises an error — for testing error recovery."""
    def __init__(self, name: str, error_message: str = "Simulated tool failure"):
        self.name = name
        self.description = f"Failing mock: {name}"
        self._error_message = error_message

    @property
    def tool_schema(self) -> dict:
        return {"name": self.name, "description": self.description,
                "input_schema": {"type": "object", "properties": {}}}

    async def _execute(self, **kwargs) -> dict:
        raise Exception(self._error_message)


def build_test_registry(*tools: BaseTool) -> ToolRegistry:
    """
    Build a ToolRegistry with the given mock tools.

    Usage:
        registry = build_test_registry(
            MockTool("get_portfolio_summary", "...", {"total_value_lakhs": 42}),
            MockTool("calculate_tax_liability", "...", {"recommended_regime": "Old Regime"}),
        )
    """
    registry = ToolRegistry()
    for tool in tools:
        registry.register(tool)
    return registry


def assert_response_has_sebi_disclaimer(response: str):
    """Assert that a response contains the SEBI disclaimer."""
    assert "sebi" in response.lower() or "investment adviser" in response.lower(), (
        "Response missing SEBI disclaimer. "
        "All AI responses must include compliance disclaimer."
    )


def assert_no_guaranteed_returns(response: str):
    """Assert that a response doesn't contain guaranteed return language."""
    prohibited = ["guaranteed return", "guaranteed profit", "risk-free return", "no risk"]
    for phrase in prohibited:
        assert phrase not in response.lower(), (
            f"Response contains prohibited phrase: '{phrase}'. "
            "AI must never promise guaranteed returns."
        )


async def run_agent_with_query(
    agent,
    client_id: str,
    query: str,
    initial_state: dict,
) -> dict:
    """
    Helper to run an agent and return final state.

    Usage:
        state = await run_agent_with_query(
            agent=wealth_assistant,
            client_id="cli-001",
            query="What is my portfolio XIRR?",
            initial_state={"client_id": "cli-001", "messages": [...]},
        )
        assert state["response"] is not None
        assert_response_has_sebi_disclaimer(state["response"])
    """
    return await agent.run(initial_state, run_id=f"test-{client_id}-{hash(query)}")
