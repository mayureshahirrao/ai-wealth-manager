"""
base_tool.py — Abstract base class for all AI tools.

Every portfolio tool, tax tool, planning tool, and RAG tool must inherit from
BaseTool. This enforces:
1. A consistent schema format Claude can understand
2. Automatic execution logging for SEBI audit trail
3. Standardized error handling
4. Timing instrumentation

Dependencies: claude_client.py, exceptions.py, logging_config.py (Tier 3)
Consumed by: All tool implementations (GetPortfolioSummaryTool, TaxCalculatorTool, etc.)
"""

import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Optional

from skills.backend.core.exceptions import AIToolExecutionError
from skills.backend.core.logging_config import get_logger, log_ai_call

logger = get_logger(__name__)


class BaseTool(ABC):
    """
    Abstract base for all AI-callable tools.

    Subclass example:
        class GetPortfolioSummaryTool(BaseTool):
            name = "get_portfolio_summary"
            description = "Get current portfolio holdings and allocation for a client"

            @property
            def tool_schema(self) -> dict:
                return {
                    "name": self.name,
                    "description": self.description,
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "client_id": {
                                "type": "string",
                                "description": "UUID of the client"
                            }
                        },
                        "required": ["client_id"]
                    }
                }

            async def _execute(self, client_id: str) -> dict:
                # fetch from DB
                portfolio = await portfolio_repo.get_by_client_id(client_id)
                return portfolio.to_summary_dict()
    """

    name: str           # Must match Anthropic tool name exactly
    description: str    # Shown to Claude — be specific about when to use this tool

    @property
    @abstractmethod
    def tool_schema(self) -> dict:
        """
        Return Anthropic tool schema dict.

        Required structure:
        {
            "name": str,
            "description": str,
            "input_schema": {
                "type": "object",
                "properties": { ... },
                "required": [...]
            }
        }
        """
        pass

    @abstractmethod
    async def _execute(self, **kwargs) -> dict[str, Any]:
        """
        Core tool logic. Override in each subclass.
        Must return a dict that will be serialized as JSON for Claude.
        """
        pass

    async def __call__(
        self,
        client_id: Optional[str] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Callable interface: validates, executes, logs, handles errors.
        Claude's tool_use response is routed here.
        """
        start = time.monotonic()
        call_id = str(uuid.uuid4())[:8]

        logger.debug(
            "tool_execution_start",
            tool=self.name,
            call_id=call_id,
            client_id=client_id,
            kwargs_keys=list(kwargs.keys()),
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

            logger.debug(
                "tool_execution_success",
                tool=self.name,
                call_id=call_id,
                duration_ms=duration_ms,
            )
            return result

        except AIToolExecutionError:
            raise  # Re-raise typed exceptions as-is

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.error(
                "tool_execution_failed",
                tool=self.name,
                call_id=call_id,
                error=str(exc),
                duration_ms=duration_ms,
            )
            raise AIToolExecutionError(
                tool_name=self.name,
                reason=str(exc),
                client_id=client_id,
            ) from exc

    @classmethod
    def get_error_response(cls, reason: str) -> dict:
        """
        Standard error dict returned to Claude when tool execution fails.
        Claude will incorporate this into its response gracefully.
        """
        return {
            "error": True,
            "message": f"Tool execution failed: {reason}",
            "tool": cls.name if hasattr(cls, 'name') else "unknown",
        }
