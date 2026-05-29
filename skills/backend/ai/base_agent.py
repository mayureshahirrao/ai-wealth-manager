"""
base_agent.py — LangGraph-based multi-step agent template.

All agents (WealthAssistant, FinancialPlanGenerator, RMCopilot) extend this base.
Provides:
1. Standard LangGraph graph construction pattern
2. State management with typed TypedDict
3. LangSmith trace wrapping
4. SEBI compliance integration at output
5. Standardized error recovery

Dependencies: claude_client, tool_registry, langsmith_tracer, compliance_injector (Tier 4)
Consumed by: WealthAssistantAgent, FinancialPlanAgent, RMCopilotAgent

LangGraph concepts:
- StateGraph: Directed graph of nodes (functions) connected by edges
- State: TypedDict shared between all nodes
- Nodes: Async functions that read/write state
- Edges: Conditional or unconditional transitions between nodes
"""

import json
import uuid
from abc import ABC, abstractmethod
from typing import Any, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from skills.backend.ai.claude_client import get_claude_client
from skills.backend.ai.compliance_injector import inject_disclaimer, validate_response_compliance, classify_query, estimate_confidence
from skills.backend.ai.tool_registry import ToolRegistry
from skills.backend.core.config import get_settings
from skills.backend.core.exceptions import AgentExecutionError
from skills.backend.core.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


class BaseAgent(ABC):
    """
    Abstract base for all LangGraph agents.

    Subclass example:
        class WealthAssistantAgent(BaseAgent):
            def build_graph(self) -> StateGraph:
                graph = StateGraph(WealthAssistantState)
                graph.add_node("route_query", self._route_query)
                graph.add_node("execute_tools", self._execute_tools)
                graph.add_node("generate_response", self._generate_response)
                graph.add_edge("route_query", "execute_tools")
                graph.add_edge("execute_tools", "generate_response")
                graph.add_edge("generate_response", END)
                graph.set_entry_point("route_query")
                return graph
    """

    def __init__(self, tool_registry: ToolRegistry, tool_names: list[str]):
        self.registry = tool_registry
        self.tool_names = tool_names
        self.claude = get_claude_client()
        self.langchain_llm = ChatAnthropic(
            model=settings.CLAUDE_PRIMARY_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=settings.CLAUDE_TEMPERATURE,
        )
        self._compiled_graph = None
        logger.info("agent_initialized", agent=self.__class__.__name__, tools=tool_names)

    @abstractmethod
    def build_graph(self) -> StateGraph:
        """
        Build and return the LangGraph StateGraph.
        Called once and cached.
        """
        pass

    def get_compiled_graph(self):
        """
        Get or build the compiled LangGraph graph.
        Compiled graph is cached after first call.
        """
        if self._compiled_graph is None:
            graph = self.build_graph()
            self._compiled_graph = graph.compile()
        return self._compiled_graph

    async def run(
        self,
        initial_state: dict,
        run_id: Optional[str] = None,
    ) -> dict:
        """
        Execute the agent graph with given initial state.

        Args:
            initial_state: TypedDict matching the agent's state schema
            run_id: Optional trace ID for LangSmith (auto-generated if None)

        Returns:
            Final state dict after all graph nodes complete

        Raises:
            AgentExecutionError on graph execution failure
        """
        run_id = run_id or str(uuid.uuid4())
        graph = self.get_compiled_graph()

        logger.info(
            "agent_run_start",
            agent=self.__class__.__name__,
            run_id=run_id,
        )

        try:
            config = {"configurable": {"thread_id": run_id}}
            final_state = await graph.ainvoke(initial_state, config=config)

            logger.info(
                "agent_run_complete",
                agent=self.__class__.__name__,
                run_id=run_id,
            )
            return final_state

        except Exception as exc:
            logger.exception(
                "agent_run_failed",
                agent=self.__class__.__name__,
                run_id=run_id,
                error=str(exc),
            )
            raise AgentExecutionError(
                agent_name=self.__class__.__name__,
                step="unknown",
                reason=str(exc),
            ) from exc

    def get_system_prompt(self) -> str:
        """
        Base system prompt included in all agents.
        Override in subclasses to add domain-specific instructions.
        """
        return """You are an AI-powered financial assistant for an Indian wealth management platform.

You assist Indian investors with:
- Portfolio analysis and performance review
- Goal-based financial planning (retirement, home purchase, education)
- Indian tax optimization (Old vs New regime, 80C, LTCG/STCG)
- Mutual fund and investment recommendations
- Retirement planning using EPF, NPS, PPF

Critical rules:
1. Always ground your answers in actual client data — use available tools
2. All monetary values must be in Indian Rupees (₹), expressed in lakhs/crores
3. Never promise specific returns or guarantee outcomes
4. For tax advice, always recommend consulting a CA (Chartered Accountant)
5. Reference Indian regulations: SEBI, PMLA, Income Tax Act, PFRDA
6. Use Indian financial terminology: SIP, ELSS, NFO, XIRR, NAV, folio number
7. When uncertain, say so explicitly and recommend human advisor consultation
"""

    async def _dispatch_tool_calls(
        self,
        tool_use_blocks: list,
    ) -> list[dict]:
        """
        Dispatch all tool_use blocks from a Claude response.

        Args:
            tool_use_blocks: List of tool_use content blocks from Claude

        Returns:
            List of {"tool_use_id": str, "result": dict} for building tool_result messages
        """
        results = []
        for block in tool_use_blocks:
            if block.type == "tool_use":
                try:
                    result = await self.registry.dispatch(block.name, **block.input)
                    results.append({
                        "tool_use_id": block.id,
                        "name": block.name,
                        "result": result,
                        "is_error": False,
                    })
                except Exception as exc:
                    results.append({
                        "tool_use_id": block.id,
                        "name": block.name,
                        "result": {"error": str(exc)},
                        "is_error": True,
                    })
        return results

    @staticmethod
    def build_tool_result_message(tool_results: list[dict]) -> dict:
        """
        Build the Anthropic tool_result message from dispatched tool results.

        Args:
            tool_results: Output of _dispatch_tool_calls()

        Returns:
            Message dict to append to conversation history
        """
        return {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": r["tool_use_id"],
                    "content": json.dumps(r["result"]),
                    "is_error": r["is_error"],
                }
                for r in tool_results
            ],
        }
