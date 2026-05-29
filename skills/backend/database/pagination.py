"""
pagination.py — Offset-based pagination for list endpoints.

Dependencies: repository.py (Tier 4)
Consumed by: All list endpoints (clients, holdings, audit log, risk alerts)
"""

from dataclasses import dataclass
from typing import TypeVar, Generic

from fastapi import Query

T = TypeVar("T")


@dataclass
class PaginationParams:
    """
    FastAPI dependency for extracting pagination query params.

    Usage in route:
        @router.get("/clients")
        async def list_clients(
            pagination: PaginationParams = Depends(get_pagination),
        ):
            items = await repo.get_all(skip=pagination.skip, limit=pagination.page_size)
            return paginated_response(items, total, pagination.page, pagination.page_size)
    """
    page: int
    page_size: int

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size


def get_pagination(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
) -> PaginationParams:
    """FastAPI dependency factory for pagination parameters."""
    return PaginationParams(page=page, page_size=page_size)
