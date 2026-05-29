"""
langsmith_tracer.py — LangSmith tracing setup for AI call observability.

Enables end-to-end tracing of Claude tool calls, token usage, and latency
in LangSmith for debugging and performance analysis.

Call setup_langsmith() once at application startup.

Dependencies: config.py (Tier 2)
"""

import os
from typing import Optional

from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def setup_langsmith() -> bool:
    """
    Configure LangSmith tracing environment variables.

    Called once at app startup in main.py lifespan.

    Returns:
        True if LangSmith is configured and enabled, False otherwise.
    """
    settings = get_settings()

    if not settings.LANGCHAIN_API_KEY:
        logger.info("langsmith_disabled", reason="LANGCHAIN_API_KEY not set")
        return False

    if not settings.LANGCHAIN_TRACING_V2:
        logger.info("langsmith_disabled", reason="LANGCHAIN_TRACING_V2=false")
        return False

    # LangSmith reads from environment variables
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
    os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT

    logger.info(
        "langsmith_enabled",
        project=settings.LANGCHAIN_PROJECT,
        endpoint=settings.LANGCHAIN_ENDPOINT,
    )
    return True


def get_trace_metadata(
    client_id: Optional[str] = None,
    session_id: Optional[str] = None,
    tool_names: Optional[list[str]] = None,
) -> dict:
    """
    Build LangSmith-compatible metadata dict for tagging traces.

    Pass as `metadata` kwarg to LangChain/LangSmith traced functions.

    Returns:
        Dict with trace tags for filtering in LangSmith UI.
    """
    metadata: dict = {
        "app": "ai-wealth-manager-india",
        "environment": os.environ.get("APP_ENV", "development"),
    }

    if client_id:
        metadata["client_id"] = client_id

    if session_id:
        metadata["session_id"] = session_id

    if tool_names:
        metadata["tools_available"] = ",".join(tool_names)

    return metadata
