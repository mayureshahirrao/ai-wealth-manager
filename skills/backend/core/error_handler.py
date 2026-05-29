"""
error_handler.py — FastAPI exception → structured JSON response conversion.

Register all handlers in main.py. This ensures every error — whether a custom
WealthManagerException, a Pydantic validation error, or an unexpected crash —
returns the standard APIResponse shape with appropriate HTTP status code.

Dependencies: base_response.py, exceptions.py, logging_config.py (Tier 2)
Consumed by: main.py (registration at startup)
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from skills.backend.core.base_response import error_response
from skills.backend.core.exceptions import WealthManagerException
from skills.backend.core.logging_config import get_logger

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers on the FastAPI app.

    Call once in main.py:
        from skills.backend.core.error_handler import register_exception_handlers
        register_exception_handlers(app)
    """

    @app.exception_handler(WealthManagerException)
    async def handle_wealth_manager_exception(
        request: Request, exc: WealthManagerException
    ) -> JSONResponse:
        """Handles all custom application exceptions."""
        logger.warning(
            "application_error",
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            path=str(request.url.path),
            details=exc.details,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(
                message=exc.message,
                error_code=exc.error_code,
                details=exc.details,
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handles Pydantic request body / query param validation failures."""
        errors = [
            {"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
            for e in exc.errors()
        ]
        logger.warning(
            "request_validation_error",
            path=str(request.url.path),
            errors=errors,
        )
        return JSONResponse(
            status_code=422,
            content=error_response(
                message="Request validation failed",
                error_code="VALIDATION_ERROR",
                details={"errors": errors},
            ).model_dump(),
        )

    @app.exception_handler(ValueError)
    async def handle_value_error(request: Request, exc: ValueError) -> JSONResponse:
        """Catches uncaught ValueError from financial calculations."""
        logger.error("unhandled_value_error", error=str(exc), path=str(request.url.path))
        return JSONResponse(
            status_code=422,
            content=error_response(
                message=str(exc),
                error_code="INVALID_VALUE",
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all for unexpected errors — never expose internal details."""
        logger.exception(
            "unhandled_exception",
            error=str(exc),
            error_type=type(exc).__name__,
            path=str(request.url.path),
        )
        return JSONResponse(
            status_code=500,
            content=error_response(
                message="An unexpected error occurred. Please try again.",
                error_code="INTERNAL_ERROR",
            ).model_dump(),
        )
