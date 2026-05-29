"""
base_tool.py — Abstract base class for all AI tools.

Every tool must inherit from BaseTool. This enforces:
1. Consistent schema format Claude can understand
2. Automatic execution logging for SEBI audit trail
3. Standardized error handling + timing

Dependencies: exceptions.py, logging_config.py (Tier 3)
"""

import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Optional

from app.core.exceptions import AIToolExecutionError
from app.core.logging_config import get_logger, log_ai_call

logger = get_logger(__name__)


class BaseTool(ABC):
    """Abstract base for all AI-callable tools."""

    name: str           # Must match Anthropic tool name exactly
    description: str    # Shown to Claude — be specific about when to use

    @property
    @abstractmethod
    def tool_schema(self) -> dict:
        """
        Return Anthropic tool schema dict:
        {
            "name": str,
            "description": str,
            "input_schema": {"type": "object", "properties": {...}, "required": [...]}
        }
        """
        pass

    @abstractmethod
    async def _execute(self, **kwargs) -> dict[str, Any]:
        """Core tool logic. Must return a dict serializable as JSON for Claude."""
        pass

    async def __call__(
        self,
        client_id: Optional[str] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Callable interface: validates, executes, logs, handles errors."""
        start = time.monotonic()
        call_id = str(uuid.uuid4())[:8]

        logger.debug(
            "tool_execution_start",
            tool=self.name,
            call_id=call_id,
            client_id=client_id,
        )

        try:
            if client_id:
                result = await self._execute(client_id=client_id, **kwargs)
            else:
                result = await self._execute(**kwargs)

            duration_ms = int((time.monotonic() - start) * 1000)
            log_ai_call(
                tool_name=self.name,
                client_id=client_id or "N/A",
                input_summary=str(kwargs)[:200],
                output_summary=str(result)[:200],
                duration_ms=duration_ms,
            )
            logger.debug("tool_execution_success", tool=self.name, call_id=call_id, duration_ms=duration_ms)
            return result

        except AIToolExecutionError:
            raise

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.error("tool_execution_failed", tool=self.name, call_id=call_id, error=str(exc))
            raise AIToolExecutionError(tool_name=self.name, reason=str(exc), client_id=client_id) from exc

    @classmethod
    def get_error_response(cls, reason: str) -> dict:
        return {
            "error": True,
            "message": f"Tool execution failed: {reason}",
            "tool": getattr(cls, "name", "unknown"),
        }
