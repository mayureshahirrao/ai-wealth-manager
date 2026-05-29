"""
app/ai/__init__.py — Public API for the AI module.
"""

from app.ai.claude_client import get_claude_client, ClaudeClient
from app.ai.base_tool import BaseTool
from app.ai.tool_registry import ToolRegistry, ToolNames
from app.ai.compliance_injector import (
    QueryType,
    classify_query,
    inject_disclaimer,
    validate_response_compliance,
    estimate_confidence,
)
from app.ai.langsmith_tracer import setup_langsmith, get_trace_metadata
from app.ai.streaming import (
    stream_chat_response,
    build_investor_system_prompt,
    build_rm_system_prompt,
)

__all__ = [
    # Client
    "get_claude_client",
    "ClaudeClient",
    # Tool base
    "BaseTool",
    "ToolRegistry",
    "ToolNames",
    # Compliance
    "QueryType",
    "classify_query",
    "inject_disclaimer",
    "validate_response_compliance",
    "estimate_confidence",
    # Tracing
    "setup_langsmith",
    "get_trace_metadata",
    # Streaming
    "stream_chat_response",
    "build_investor_system_prompt",
    "build_rm_system_prompt",
]
