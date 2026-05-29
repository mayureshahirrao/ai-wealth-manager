"""
error_handler.py — FastAPI exception → structured JSON response conversion.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.base_response import error_response
from app.core.exceptions import WealthManagerException
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(WealthManagerException)
    async def handle_wealth_manager_exception(
        request: Request, exc: WealthManagerException
    ) -> JSONResponse:
        logger.warning(
            "application_error",
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            path=str(request.url.path),
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
        errors = [
            {"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
            for e in exc.errors()
        ]
        logger.warning("request_validation_error", path=str(request.url.path), errors=errors)
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
        logger.error("unhandled_value_error", error=str(exc), path=str(request.url.path))
        return JSONResponse(
            status_code=422,
            content=error_response(message=str(exc), error_code="INVALID_VALUE").model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
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
