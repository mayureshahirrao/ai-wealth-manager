"""
role_guard.py — FastAPI dependencies for role-based access control.

Usage pattern:
    @router.get("/rm/clients", dependencies=[Depends(require_rm)])
    async def get_rm_clients(): ...

    # Or for getting current user object:
    @router.get("/portfolio")
    async def get_portfolio(current_user = Depends(get_current_user)): ...

Dependencies: jwt_handler.py, exceptions.py (Tier 3)
Consumed by: All protected route handlers
"""

from typing import Optional
import uuid

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from skills.backend.auth.jwt_handler import decode_access_token
from skills.backend.core.exceptions import UnauthorizedException, ForbiddenException
from skills.backend.database.base_model import UserRole

security = HTTPBearer(auto_error=False)


class CurrentUser:
    """Lightweight user context extracted from JWT."""
    def __init__(self, user_id: uuid.UUID, email: str, role: UserRole):
        self.user_id = user_id
        self.email = email
        self.role = role

    @property
    def is_investor(self) -> bool:
        return self.role == UserRole.INVESTOR

    @property
    def is_rm(self) -> bool:
        return self.role == UserRole.RM

    @property
    def is_compliance(self) -> bool:
        return self.role == UserRole.COMPLIANCE


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> CurrentUser:
    """
    FastAPI dependency: extracts and validates the current user from JWT.

    Raises UnauthorizedException if token is missing or invalid.
    """
    if credentials is None:
        raise UnauthorizedException("No authentication token provided")

    payload = decode_access_token(credentials.credentials)
    return CurrentUser(
        user_id=uuid.UUID(payload["sub"]),
        email=payload["email"],
        role=UserRole(payload["role"]),
    )


async def require_investor(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Dependency: only allows investor role."""
    if not current_user.is_investor:
        raise ForbiddenException(role=current_user.role.value, resource="investor endpoints")
    return current_user


async def require_rm(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Dependency: only allows RM role."""
    if not current_user.is_rm:
        raise ForbiddenException(role=current_user.role.value, resource="RM endpoints")
    return current_user


async def require_compliance(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Dependency: only allows compliance role."""
    if not current_user.is_compliance:
        raise ForbiddenException(role=current_user.role.value, resource="compliance endpoints")
    return current_user


async def require_rm_or_compliance(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Dependency: allows RM or compliance role (shared resources)."""
    if not (current_user.is_rm or current_user.is_compliance):
        raise ForbiddenException(
            role=current_user.role.value,
            resource="RM/compliance endpoints",
        )
    return current_user
