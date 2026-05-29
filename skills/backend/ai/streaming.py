"""
streaming.py — Server-Sent Events (SSE) streaming for chat responses.

The chat interface streams Claude's response token-by-token using SSE.
This file provides the generator function used by FastAPI's StreamingResponse.

Protocol (client reads these event types):
  data: {"type": "delta", "text": "..."}       ← text chunk
  data: {"type": "tool_call", "name": "...", "status": "running"}
  data: {"type": "tool_result", "name": "...", "summary": "..."}
  data: {"type": "done", "confidence": 0.92}
  data: {"type": "error", "message": "..."}

Dependencies: claude_client, compliance_injector (Tier 4)
Consumed by: chat API endpoint
"""

import json
import asyncio
from typing import AsyncGenerator, Optional

from skills.backend.ai.claude_client import get_claude_client
from skills.backend.ai.compliance_injector import (
    classify_query,
    inject_disclaimer,
    validate_response_compliance,
    estimate_confidence,
    QueryType,
)
from skills.backend.ai.tool_registry import ToolRegistry
from skills.backend.core.logging_config import get_logger, log_ai_call

logger = get_logger(__name__)


def sse_event(data: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


async def stream_chat_response(
    messages: list[dict],
    system_prompt: str,
    tool_registry: ToolRegistry,
    tool_names: list[str],
    client_id: str,
    user_query: str,
) -> AsyncGenerator[str, None]:
    """
    Stream a Claude chat response with tool calling over SSE.

    Agentic loop:
    1. Send messages + tools to Claude
    2. If stop_reason == "tool_use": dispatch tools, yield tool events, loop
    3. If stop_reason == "end_turn": yield text deltas, inject disclaimer, yield done

    Args:
        messages: Full conversation history (user + assistant turns)
        system_prompt: System prompt for this conversation
        tool_registry: Initialized ToolRegistry with tools available
        tool_names: Subset of tool names to expose for this query
        client_id: For logging/audit
        user_query: Original user query text

    Yields:
        SSE-formatted strings (each ending with \n\n)
    """
    client = get_claude_client()
    query_type = classify_query(user_query)
    tools_used = []
    full_response_text = ""
    rag_sources = 0

    try:
        tool_schemas = tool_registry.get_schemas(tool_names)
        current_messages = list(messages)

        # Agentic loop: keep calling Claude until it stops using tools
        max_iterations = 5
        for iteration in range(max_iterations):

            response = await client.complete_with_tools(
                messages=current_messages,
                tools=tool_schemas,
                system=system_prompt,
            )

            if response.stop_reason == "tool_use":
                # Extract tool_use blocks
                tool_blocks = [b for b in response.content if b.type == "tool_use"]

                # Append assistant message with tool_use content
                current_messages.append({
                    "role": "assistant",
                    "content": response.content,
                })

                # Dispatch each tool and yield events
                tool_results = []
                for block in tool_blocks:
                    tools_used.append(block.name)
                    yield sse_event({
                        "type": "tool_call",
                        "name": block.name,
                        "status": "running",
                    })

                    try:
                        result = await tool_registry.dispatch(block.name, **block.input)
                        if block.name == "query_financial_knowledge":
                            rag_sources = result.get("sources_found", 0)

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })

                        yield sse_event({
                            "type": "tool_result",
                            "name": block.name,
                            "status": "done",
                            "summary": _summarize_tool_result(block.name, result),
                        })

                    except Exception as exc:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps({"error": str(exc)}),
                            "is_error": True,
                        })
                        yield sse_event({
                            "type": "tool_result",
                            "name": block.name,
                            "status": "error",
                            "summary": str(exc),
                        })

                # Append tool results and continue loop
                current_messages.append({
                    "role": "user",
                    "content": tool_results,
                })

            elif response.stop_reason == "end_turn":
                # Extract text from final response
                for block in response.content:
                    if hasattr(block, "text"):
                        full_response_text += block.text
                        # Stream text in chunks
                        for chunk in _split_into_chunks(block.text, chunk_size=50):
                            yield sse_event({"type": "delta", "text": chunk})
                            await asyncio.sleep(0)  # yield control to event loop
                break

        # Inject disclaimer and yield it
        disclaimer_text = inject_disclaimer("", query_type).strip()
        if disclaimer_text:
            yield sse_event({"type": "delta", "text": "\n" + disclaimer_text})
            full_response_text += "\n" + disclaimer_text

        # Calculate and yield confidence
        confidence = estimate_confidence(full_response_text, tools_used, rag_sources)

        yield sse_event({
            "type": "done",
            "confidence": confidence,
            "tools_used": tools_used,
            "query_type": query_type.value,
        })

        # SEBI audit log
        log_ai_call(
            tool_name="chat_stream",
            client_id=client_id,
            input_summary=user_query[:200],
            output_summary=full_response_text[:200],
            duration_ms=0,
            confidence=confidence,
        )

    except Exception as exc:
        logger.exception("streaming_error", error=str(exc), client_id=client_id)
        yield sse_event({"type": "error", "message": "An error occurred. Please try again."})


def _split_into_chunks(text: str, chunk_size: int = 50) -> list[str]:
    """Split text into word-boundary chunks for smooth streaming."""
    words = text.split(" ")
    chunks = []
    current = []
    for word in words:
        current.append(word)
        if len(" ".join(current)) >= chunk_size:
            chunks.append(" ".join(current) + " ")
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks


def _summarize_tool_result(tool_name: str, result: dict) -> str:
    """Generate a human-readable summary of a tool result for the UI."""
    summaries = {
        "get_portfolio_summary": lambda r: f"Portfolio: ₹{r.get('total_value_lakhs', 0):.1f}L, XIRR: {r.get('xirr_pct', 0):.1f}%",
        "get_goal_progress": lambda r: f"{r.get('goal_type', 'Goal')}: {r.get('progress_pct', 0):.0f}% complete",
        "run_retirement_projection": lambda r: f"Projected corpus: ₹{r.get('projected_corpus_cr', 0):.1f}Cr at age {r.get('target_age', 60)}",
        "calculate_tax_liability": lambda r: f"Tax liability: ₹{r.get('recommended_regime_tax_lakhs', 0):.1f}L ({r.get('recommended_regime', 'N/A')} regime)",
        "run_scenario_analysis": lambda r: f"Scenario impact: {r.get('portfolio_change_pct', 0):+.1f}%",
        "query_financial_knowledge": lambda r: f"Found {r.get('sources_found', 0)} relevant sources",
        "get_next_best_actions": lambda r: f"Found {len(r.get('actions', []))} priority actions",
    }
    summarizer = summaries.get(tool_name)
    if summarizer:
        try:
            return summarizer(result)
        except Exception:
            pass
    return f"Completed {tool_name}"
