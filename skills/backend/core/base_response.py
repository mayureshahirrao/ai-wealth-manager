"""
base_response.py — Standard API response envelope for all endpoints.

Every route handler must return one of these shapes. This ensures the frontend
always knows exactly what structure to expect and error handling is uniform.

Dependencies: exceptions.py (Tier 1)
Consumed by: All route handlers, streaming.py
"""

from typing import TypeVar, Generic, Optional, Any, Dict
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """
    Standard response wrapper for all API endpoints.

    Success: {"success": true, "data": {...}, "message": "optional"}
    Failure: {"success": false, "error_code": "NOT_FOUND", "message": "..."}

    Usage:
        @router.get("/clients/{id}")
        async def get_client(id: str) -> APIResponse[ClientSchema]:
            client = await client_repo.get_by_id(id)
            return success_response(client)
    """
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Response wrapper for paginated list endpoints.

    Usage:
        return paginated_response(items=clients, total=100, page=1, page_size=20)
    """
    success: bool = True
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


# ─── Factory Functions ────────────────────────────────────────────────────────

def success_response(
    data: Any = None,
    message: Optional[str] = None,
) -> APIResponse:
    """
    Create a successful API response.

    Args:
        data: The response payload (any Pydantic model or dict)
        message: Optional human-readable message

    Example:
        return success_response(data=portfolio_dict, message="Portfolio loaded")
    """
    return APIResponse(success=True, data=data, message=message)


def error_response(
    message: str,
    error_code: str = "INTERNAL_ERROR",
    details: Optional[Dict[str, Any]] = None,
) -> APIResponse:
    """
    Create an error API response.

    Args:
        message: Human-readable error description
        error_code: Machine-readable error identifier (from exceptions.py)
        details: Optional structured debug info

    Example:
        return error_response("Client not found", error_code="NOT_FOUND")
    """
    return APIResponse(
        success=False,
        message=message,
        error_code=error_code,
        details=details,
    )


def paginated_response(
    items: list,
    total: int,
    page: int,
    page_size: int,
) -> PaginatedResponse:
    """
    Create a paginated list response.

    Example:
        return paginated_response(items=clients, total=42, page=1, page_size=20)
    """
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
        has_prev=page > 1,
    )
