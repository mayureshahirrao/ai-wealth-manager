"""
role_guard.py — FastAPI dependencies for role-based access control.
"""

from typing import Optional
import uuid

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.jwt_handler import decode_access_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.database.base_model import UserRole

security = HTTPBearer(auto_error=False)


class CurrentUser:
    def __init__(
        self,
        user_id: uuid.UUID,
        email: str,
        role: UserRole,
        client_id: Optional[uuid.UUID] = None,
    ):
        self.user_id = user_id
        self.email = email
        self.role = role
        self.client_id = client_id  # Set for investor role only

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
    if credentials is None:
        raise UnauthorizedException("No authentication token provided")
    payload = decode_access_token(credentials.credentials)
    client_id_str = payload.get("client_id")
    return CurrentUser(
        user_id=uuid.UUID(payload["sub"]),
        email=payload["email"],
        role=UserRole(payload["role"]),
        client_id=uuid.UUID(client_id_str) if client_id_str else None,
    )


async def require_investor(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not current_user.is_investor:
        raise ForbiddenException(role=current_user.role.value, resource="investor endpoints")
    return current_user


async def require_rm(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not current_user.is_rm:
        raise ForbiddenException(role=current_user.role.value, resource="RM endpoints")
    return current_user


async def require_compliance(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not current_user.is_compliance:
        raise ForbiddenException(role=current_user.role.value, resource="compliance endpoints")
    return current_user


async def require_rm_or_compliance(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not (current_user.is_rm or current_user.is_compliance):
        raise ForbiddenException(role=current_user.role.value, resource="RM/compliance endpoints")
    return current_user
