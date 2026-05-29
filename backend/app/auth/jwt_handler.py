"""
jwt_handler.py — JWT token creation and verification.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from jose import jwt, JWTError

from app.core.config import get_settings
from app.core.exceptions import InvalidTokenException
from app.database.base_model import UserRole

settings = get_settings()


def create_access_token(
    user_id: uuid.UUID,
    email: str,
    role: UserRole,
    client_id: Optional[uuid.UUID] = None,
) -> str:
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
    if client_id is not None:
        payload["client_id"] = str(client_id)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
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
    payload = decode_access_token(token)
    return uuid.UUID(payload["sub"])


def get_role_from_token(token: str) -> UserRole:
    payload = decode_access_token(token)
    return UserRole(payload["role"])
