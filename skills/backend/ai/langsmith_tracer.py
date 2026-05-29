"""
langsmith_tracer.py — LangSmith observability setup.

Configures LangChain/LangSmith tracing so every agent run and tool call
is visible in the LangSmith dashboard. Required environment variables:
  LANGCHAIN_API_KEY=lsv2_...
  LANGCHAIN_TRACING_V2=true
  LANGCHAIN_PROJECT=ai-wealth-manager-india

Dependencies: config.py (Tier 3)
Consumed by: main.py (setup at startup), base_agent.py
"""

import os
from skills.backend.core.config import get_settings
from skills.backend.core.logging_config import get_logger

logger = get_logger(__name__)


def setup_langsmith() -> bool:
    """
    Configure LangSmith tracing via environment variables.
    LangChain automatically reads these to enable tracing.

    Returns:
        True if LangSmith is configured, False if API key missing

    Call in main.py startup:
        from skills.backend.ai.langsmith_tracer import setup_langsmith
        langsmith_enabled = setup_langsmith()
    """
    settings = get_settings()

    if not settings.LANGCHAIN_API_KEY:
        logger.warning(
            "langsmith_not_configured",
            reason="LANGCHAIN_API_KEY not set — tracing disabled",
        )
        return False

    # LangChain reads these env vars automatically
    os.environ["LANGCHAIN_TRACING_V2"] = str(settings.LANGCHAIN_TRACING_V2).lower()
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
    os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT

    logger.info(
        "langsmith_configured",
        project=settings.LANGCHAIN_PROJECT,
        tracing=settings.LANGCHAIN_TRACING_V2,
    )
    return True


def get_trace_metadata(client_id: str, agent_name: str, user_query: str) -> dict:
    """
    Build metadata dict for LangSmith run tagging.
    Pass to graph.ainvoke(config={"metadata": get_trace_metadata(...)})

    Args:
        client_id: Client UUID for this interaction
        agent_name: Name of the agent being run
        user_query: The user's query (first 100 chars)

    Returns:
        Dict of LangSmith metadata tags
    """
    return {
        "client_id": client_id,
        "agent": agent_name,
        "query_preview": user_query[:100],
        "platform": "ai-wealth-manager-india",
        "environment": get_settings().APP_ENV,
    }
