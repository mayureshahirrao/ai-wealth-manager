"""
logging_config.py — Structured logging setup for the entire backend.

Uses structlog for JSON-formatted logs. Every log entry includes:
- timestamp, log level, module, function name
- request_id (for tracing across a request lifecycle)
- client_id (when available, for AI audit trail)

Dependencies: None (Tier 1 — external libs only)
Consumed by: main.py (setup at startup), all modules
"""

import logging
import sys
from contextvars import ContextVar
from typing import Optional
import structlog

# Context variables — set per request in middleware
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
client_id_ctx: ContextVar[Optional[str]] = ContextVar("client_id", default=None)


def add_request_context(logger, method, event_dict):
    """structlog processor: inject request context into every log entry."""
    request_id = request_id_ctx.get()
    client_id = client_id_ctx.get()
    if request_id:
        event_dict["request_id"] = request_id
    if client_id:
        event_dict["client_id"] = client_id
    return event_dict


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """
    Configure structlog + stdlib logging at application startup.

    Call once in main.py:
        from skills.backend.core.logging_config import setup_logging
        setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)

    Args:
        log_level: "DEBUG" | "INFO" | "WARNING" | "ERROR"
        log_format: "json" (production) | "text" (development console)
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        add_request_context,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Silence noisy third-party loggers
    for noisy in ["uvicorn.access", "httpx", "httpcore", "chromadb"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a named logger. Use this everywhere instead of logging.getLogger().

    Usage:
        from skills.backend.core.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("portfolio_loaded", client_id="priya-001", holdings_count=8)
    """
    return structlog.get_logger(name)


def log_ai_call(
    tool_name: str,
    client_id: str,
    input_summary: str,
    output_summary: str,
    duration_ms: int,
    confidence: Optional[float] = None,
) -> None:
    """
    Structured log for every AI tool call — feeds into SEBI audit requirements.

    Usage:
        log_ai_call(
            tool_name="CalculateTaxLiability",
            client_id="priya-001",
            input_summary="FY 2024-25 income ₹18L",
            output_summary="Old regime saves ₹18K",
            duration_ms=340,
            confidence=0.92,
        )
    """
    logger = get_logger("ai.audit")
    logger.info(
        "ai_tool_called",
        tool_name=tool_name,
        client_id=client_id,
        input_summary=input_summary[:200],
        output_summary=output_summary[:200],
        duration_ms=duration_ms,
        confidence=confidence,
        audit_event=True,  # Flag for SEBI audit log filter
    )
