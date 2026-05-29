"""
base_response.py — Standard API response envelope for all endpoints.
"""

from typing import TypeVar, Generic, Optional, Any, Dict
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


def success_response(data: Any = None, message: Optional[str] = None) -> APIResponse:
    return APIResponse(success=True, data=data, message=message)


def error_response(
    message: str,
    error_code: str = "INTERNAL_ERROR",
    details: Optional[Dict[str, Any]] = None,
) -> APIResponse:
    return APIResponse(success=False, message=message, error_code=error_code, details=details)


def paginated_response(items: list, total: int, page: int, page_size: int) -> PaginatedResponse:
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
        has_prev=page > 1,
    )
