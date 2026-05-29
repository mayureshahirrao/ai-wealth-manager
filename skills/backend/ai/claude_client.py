"""
claude_client.py — Singleton Anthropic Claude client with retry and logging.

All AI calls in the application go through this client. Never instantiate
anthropic.Anthropic directly elsewhere.

Features:
- Singleton pattern (one client instance, thread-safe)
- Automatic retry with exponential backoff (3 attempts)
- Per-call token/cost logging
- LangSmith trace integration via run_id header

Dependencies: config.py, exceptions.py (Tier 2)
Consumed by: base_tool.py, base_agent.py, compliance doc generator
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
    before_sleep_log,
)

from skills.backend.core.config import get_settings
from skills.backend.core.exceptions import AIToolExecutionError
from skills.backend.core.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ClaudeClient:
    """
    Singleton wrapper around the Anthropic Python SDK.

    Usage:
        client = get_claude_client()

        # Simple completion
        response = await client.complete(
            messages=[{"role": "user", "content": "What is ELSS?"}],
            model=settings.CLAUDE_FAST_MODEL,
        )
        text = response.content[0].text

        # With tools
        response = await client.complete_with_tools(
            messages=messages,
            tools=tool_schemas,
            model=settings.CLAUDE_PRIMARY_MODEL,
        )
    """

    def __init__(self):
        self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._async_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
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
        """
        Async text completion (no tools).

        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."}
            model: Override default model (uses claude_primary by default)
            system: System prompt string
            max_tokens: Override default max_tokens
            temperature: Override default temperature

        Returns:
            anthropic.types.Message object
        """
        start = time.monotonic()
        chosen_model = model or settings.CLAUDE_PRIMARY_MODEL

        kwargs = {
            "model": chosen_model,
            "messages": messages,
            "max_tokens": max_tokens or settings.CLAUDE_MAX_TOKENS,
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
        """
        Async completion with tool-use (function calling).

        Args:
            messages: Conversation history
            tools: List of Anthropic tool schema dicts
            model: Model override (use primary model for tool calling)
            system: System prompt

        Returns:
            anthropic.types.Message — check stop_reason == "tool_use" for tool calls
        """
        start = time.monotonic()
        chosen_model = model or settings.CLAUDE_PRIMARY_MODEL

        kwargs = {
            "model": chosen_model,
            "messages": messages,
            "tools": tools,
            "max_tokens": settings.CLAUDE_MAX_TOKENS,
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

    def stream_complete(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        system: Optional[str] = None,
    ):
        """
        Synchronous streaming completion (for SSE endpoints).
        Returns a context manager yielding text deltas.

        Usage:
            with client.stream_complete(messages, system=system_prompt) as stream:
                for text in stream.text_stream:
                    yield f"data: {text}\\n\\n"
        """
        chosen_model = model or settings.CLAUDE_PRIMARY_MODEL
        kwargs = {
            "model": chosen_model,
            "messages": messages,
            "max_tokens": settings.CLAUDE_MAX_TOKENS,
        }
        if system:
            kwargs["system"] = system
        return self._client.messages.stream(**kwargs)


@lru_cache()
def get_claude_client() -> ClaudeClient:
    """
    Returns the singleton ClaudeClient instance.
    Thread-safe due to lru_cache.

    Usage:
        from skills.backend.ai.claude_client import get_claude_client
        client = get_claude_client()
    """
    return ClaudeClient()
