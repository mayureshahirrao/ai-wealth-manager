"""
claude_client.py — Singleton Anthropic Claude client with retry and logging.

All AI calls in the application go through this client.
Never instantiate anthropic.Anthropic directly elsewhere.

Dependencies: config.py, exceptions.py (Tier 2)
"""

import time
from functools import lru_cache
from typing import Optional

import anthropic
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import get_settings
from app.core.exceptions import AIToolExecutionError
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ClaudeClient:
    """
    Singleton wrapper around the Anthropic Python SDK.

    Usage:
        client = get_claude_client()
        response = await client.complete_with_tools(messages, tools, system=system_prompt)
    """

    def __init__(self):
        settings = get_settings()
        self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._async_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._settings = settings
        logger.info("claude_client_initialized", model=settings.CLAUDE_PRIMARY_MODEL)

    @retry(
        retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIStatusError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    async def complete(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> anthropic.types.Message:
        """Async text completion (no tools)."""
        start = time.monotonic()
        chosen_model = model or self._settings.CLAUDE_PRIMARY_MODEL

        kwargs: dict = {
            "model": chosen_model,
            "messages": messages,
            "max_tokens": max_tokens or self._settings.CLAUDE_MAX_TOKENS,
        }
        if system:
            kwargs["system"] = system
        if temperature is not None:
            kwargs["temperature"] = temperature

        try:
            response = await self._async_client.messages.create(**kwargs)
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "claude_completion",
                model=chosen_model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                duration_ms=duration_ms,
            )
            return response
        except anthropic.AuthenticationError as e:
            raise AIToolExecutionError("ClaudeClient", "Invalid API key") from e
        except anthropic.BadRequestError as e:
            raise AIToolExecutionError("ClaudeClient", f"Bad request: {e}") from e

    @retry(
        retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIStatusError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    async def complete_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        model: Optional[str] = None,
        system: Optional[str] = None,
    ) -> anthropic.types.Message:
        """Async completion with tool-use (function calling)."""
        start = time.monotonic()
        chosen_model = model or self._settings.CLAUDE_PRIMARY_MODEL

        kwargs: dict = {
            "model": chosen_model,
            "messages": messages,
            "tools": tools,
            "max_tokens": self._settings.CLAUDE_MAX_TOKENS,
        }
        if system:
            kwargs["system"] = system

        try:
            response = await self._async_client.messages.create(**kwargs)
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "claude_tool_completion",
                model=chosen_model,
                stop_reason=response.stop_reason,
                tool_calls=len([b for b in response.content if b.type == "tool_use"]),
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                duration_ms=duration_ms,
            )
            return response
        except anthropic.AuthenticationError as e:
            raise AIToolExecutionError("ClaudeClient", "Invalid API key") from e
        except anthropic.BadRequestError as e:
            raise AIToolExecutionError("ClaudeClient", f"Bad request: {e}") from e


@lru_cache()
def get_claude_client() -> ClaudeClient:
    """
    Returns the singleton ClaudeClient instance.
    Thread-safe due to lru_cache.
    """
    return ClaudeClient()
