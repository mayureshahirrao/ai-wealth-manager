"""
streaming.py — Agentic Claude streaming loop with tool-use.

Implements an async generator that:
1. Sends messages to Claude with tool schemas
2. Handles tool_use responses (dispatches to ToolRegistry)
3. Streams text chunks as SSE events
4. Injects SEBI disclaimer and yields final `done` event

SSE Event format:
    data: {"type": "delta", "text": "..."}\n\n
    data: {"type": "tool_call", "tool": "...", "input": {...}}\n\n
    data: {"type": "tool_result", "tool": "...", "result": {...}}\n\n
    data: {"type": "done", "confidence": 0.85, "tools_used": [...]}\n\n
    data: {"type": "error", "message": "..."}\n\n

Dependencies: claude_client, tool_registry, compliance_injector, response_validator (Tier 4)
"""

import json
import time
from typing import AsyncGenerator, Optional

from app.ai.claude_client import get_claude_client
from app.ai.tool_registry import ToolRegistry
from app.ai.compliance_injector import (
    classify_query,
    inject_disclaimer,
    validate_response_compliance,
    estimate_confidence,
)
from app.ai.response_validator import run_full_validation
from app.core.logging_config import get_logger

logger = get_logger(__name__)

MAX_TOOL_ITERATIONS = 5  # Safety limit on the agentic loop


def sse_event(data: dict) -> str:
    """Format a dict as an SSE event string."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def stream_chat_response(
    messages: list[dict],
    system_prompt: str,
    tool_registry: ToolRegistry,
    tool_names: list[str],
    client_id: str,
    user_query: str,
) -> AsyncGenerator[str, None]:
    """
    Async generator implementing the agentic Claude tool-use loop.

    Args:
        messages: Conversation history in Claude format
        system_prompt: System prompt string for this agent role
        tool_registry: Per-request ToolRegistry with registered tools
        tool_names: Subset of tools to expose for this request
        client_id: UUID string of the client being queried
        user_query: The original user question (for compliance classification)

    Yields:
        SSE-formatted event strings
    """
    claude = get_claude_client()
    query_type = classify_query(user_query)
    tools_used: list[str] = []
    full_response_text = ""
    start_time = time.monotonic()
    iteration = 0

    # Working copy of messages (we append tool results here)
    conversation = list(messages)

    tool_schemas = tool_registry.get_schemas(tool_names)

    try:
        while iteration < MAX_TOOL_ITERATIONS:
            iteration += 1
            logger.debug(
                "agentic_loop_iteration",
                iteration=iteration,
                client_id=client_id,
                tools_available=len(tool_schemas),
            )

            response = await claude.complete_with_tools(
                messages=conversation,
                tools=tool_schemas,
                system=system_prompt,
            )

            # --- Stream text content blocks ---
            for block in response.content:
                if block.type == "text" and block.text:
                    full_response_text += block.text
                    yield sse_event({"type": "delta", "text": block.text})

            # --- Handle stop reasons ---
            if response.stop_reason == "end_turn":
                # No more tool calls — we're done
                break

            if response.stop_reason == "tool_use":
                # Collect all tool calls in this response
                tool_call_blocks = [b for b in response.content if b.type == "tool_use"]

                if not tool_call_blocks:
                    break

                # Append assistant turn with all content blocks
                conversation.append({
                    "role": "assistant",
                    "content": [
                        _block_to_dict(block) for block in response.content
                    ],
                })

                # Execute each tool and collect results
                tool_result_content = []

                for tool_block in tool_call_blocks:
                    tool_name = tool_block.name
                    tool_input = tool_block.input or {}

                    yield sse_event({
                        "type": "tool_call",
                        "tool": tool_name,
                        "input": tool_input,
                    })

                    try:
                        # Always inject client_id so tools can query the DB
                        if "client_id" not in tool_input:
                            tool_input["client_id"] = client_id

                        result = await tool_registry.dispatch(tool_name, **tool_input)

                        # Validate tool output
                        validation = run_full_validation(tool_name, result)
                        if not validation.is_valid:
                            result["_validation_warnings"] = validation.errors

                        tools_used.append(tool_name)

                        yield sse_event({
                            "type": "tool_result",
                            "tool": tool_name,
                            "result": result,
                        })

                    except Exception as exc:
                        logger.error(
                            "tool_dispatch_error",
                            tool=tool_name,
                            error=str(exc),
                            client_id=client_id,
                        )
                        result = {
                            "error": True,
                            "message": f"Tool '{tool_name}' failed: {str(exc)}",
                        }
                        yield sse_event({
                            "type": "tool_result",
                            "tool": tool_name,
                            "result": result,
                        })

                    tool_result_content.append({
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": json.dumps(result, default=str),
                    })

                # Append tool results as user turn
                conversation.append({
                    "role": "user",
                    "content": tool_result_content,
                })

            else:
                # Unexpected stop reason
                logger.warning(
                    "unexpected_stop_reason",
                    stop_reason=response.stop_reason,
                    client_id=client_id,
                )
                break

        # --- Post-loop: inject disclaimer + compute confidence ---
        if full_response_text:
            final_response = inject_disclaimer(full_response_text, query_type)

            # If disclaimer was appended, stream it as an extra delta
            appended = final_response[len(full_response_text):]
            if appended:
                yield sse_event({"type": "delta", "text": appended})
                full_response_text = final_response

        compliance = validate_response_compliance(full_response_text, query_type)
        confidence = estimate_confidence(full_response_text, tools_used)

        duration_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(
            "stream_complete",
            client_id=client_id,
            tools_used=tools_used,
            iterations=iteration,
            confidence=confidence,
            duration_ms=duration_ms,
            compliant=compliance["is_compliant"],
        )

        yield sse_event({
            "type": "done",
            "confidence": confidence,
            "tools_used": tools_used,
            "query_type": query_type,
            "compliant": compliance["is_compliant"],
            "duration_ms": duration_ms,
        })

    except Exception as exc:
        logger.error(
            "stream_fatal_error",
            error=str(exc),
            client_id=client_id,
        )
        yield sse_event({
            "type": "error",
            "message": "An error occurred while processing your request. Please try again.",
        })


def _block_to_dict(block) -> dict:
    """Convert an Anthropic content block to a serializable dict."""
    if block.type == "text":
        return {"type": "text", "text": block.text}
    elif block.type == "tool_use":
        return {
            "type": "tool_use",
            "id": block.id,
            "name": block.name,
            "input": block.input,
        }
    else:
        return {"type": block.type}


def build_investor_system_prompt(client_name: str, risk_profile: str) -> str:
    """
    Build the system prompt for an investor-facing chat session.

    Args:
        client_name: Client's full name
        risk_profile: Risk profile string (conservative/moderate/aggressive)

    Returns:
        System prompt string
    """
    return f"""You are an AI wealth management assistant for {client_name}, an investor with a {risk_profile} risk profile.

You have access to tools that can retrieve:
- Portfolio summary and holdings
- Goal progress and feasibility
- Tax liability calculations (Indian tax law, Budget 2024)
- Market data (Nifty 50, Sensex)
- Retirement projections

Guidelines:
1. Always use tools to fetch live data before answering questions about portfolios, taxes, or goals
2. Provide specific numbers in Indian format (₹, Lakhs, Crores)
3. Reference Indian tax rules accurately (LTCG 12.5% above ₹1.25L, STCG 20%, Budget 2024)
4. Do not make specific buy/sell recommendations — provide analysis and let the client decide
5. For retirement planning, always mention the importance of inflation-adjusted targets
6. Be concise but thorough — clients want actionable insights
7. If a question is outside your tools' scope, say so clearly and suggest consulting their RM

Remember: You are providing financial information, not regulated investment advice."""


def build_rm_system_prompt(rm_name: str = "Relationship Manager") -> str:
    """
    Build the system prompt for an RM copilot session.

    Returns:
        System prompt string for RM-facing chat
    """
    return f"""You are an AI copilot assisting {rm_name}, a relationship manager at an SEBI-registered wealth management firm.

You have access to tools that can retrieve client portfolio data, goal progress, tax analysis, and retirement projections.

Guidelines:
1. Always use tools to fetch current client data before analysis
2. Provide professional, concise summaries suitable for client meetings
3. Flag compliance issues (concentration risk, overdue reviews, KYC expiry)
4. Reference SEBI IA Regulations 2013 where relevant
5. Suggest next best actions based on client data
6. Format numbers clearly in Indian convention (₹, Lakhs, Crores)
7. Maintain client confidentiality — only discuss the specific client being queried

You are assisting a SEBI-registered investment adviser. Your analysis supports (does not replace) the RM's professional judgment."""
