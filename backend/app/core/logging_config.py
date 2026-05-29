"""
logging_config.py — Structured logging setup for the entire backend.
"""

import logging
import sys
from contextvars import ContextVar
from typing import Optional
import structlog

request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
client_id_ctx: ContextVar[Optional[str]] = ContextVar("client_id", default=None)


def add_request_context(logger, method, event_dict):
    request_id = request_id_ctx.get()
    client_id = client_id_ctx.get()
    if request_id:
        event_dict["request_id"] = request_id
    if client_id:
        event_dict["client_id"] = client_id
    return event_dict


def setup_logging(log_level: str = "INFO", log_format: str = "text") -> None:
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

    for noisy in ["uvicorn.access", "httpx", "httpcore", "chromadb"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


def log_ai_call(
    tool_name: str,
    client_id: str,
    input_summary: str,
    output_summary: str,
    duration_ms: int,
    confidence: Optional[float] = None,
) -> None:
    logger = get_logger("ai.audit")
    logger.info(
        "ai_tool_called",
        tool_name=tool_name,
        client_id=client_id,
        input_summary=input_summary[:200],
        output_summary=output_summary[:200],
        duration_ms=duration_ms,
        confidence=confidence,
        audit_event=True,
    )
