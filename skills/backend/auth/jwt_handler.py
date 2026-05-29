"""
jwt_handler.py — JWT token creation and verification.

Tokens carry: user_id, email, role, exp (expiry).
Roles are: investor | rm | compliance

Dependencies: config.py, exceptions.py (Tier 2)
Consumed by: auth routes (login), role_guard.py
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from jose import jwt, JWTError

from skills.backend.core.config import get_settings
from skills.backend.core.exceptions import InvalidTokenException, UnauthorizedException
from skills.backend.database.base_model import UserRole

settings = get_settings()


def create_access_token(
    user_id: uuid.UUID,
    email: str,
    role: UserRole,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        user_id: UUID of the authenticated user
        email: User's email address
        role: UserRole enum value

    Returns:
        Signed JWT string

    Example:
        token = create_access_token(user.id, user.email, user.role)
        return {"access_token": token, "token_type": "bearer"}
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role.value,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT string (without "Bearer " prefix)

    Returns:
        Decoded payload dict with keys: sub, email, role, exp

    Raises:
        InvalidTokenException if token is expired or tampered
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("sub") is None:
            raise InvalidTokenException()
        return payload
    except JWTError:
        raise InvalidTokenException()


def get_user_id_from_token(token: str) -> uuid.UUID:
    """Extract user UUID from a valid token."""
    payload = decode_access_token(token)
    return uuid.UUID(payload["sub"])


def get_role_from_token(token: str) -> UserRole:
    """Extract user role from a valid token."""
    payload = decode_access_token(token)
    return UserRole(payload["role"])
