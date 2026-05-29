"""
router.py — Auth endpoints: login, me.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import create_access_token
from app.auth.password_utils import verify_password
from app.auth.role_guard import get_current_user, CurrentUser
from app.core.base_response import success_response, APIResponse
from app.core.exceptions import UnauthorizedException
from app.core.logging_config import get_logger
from app.database.models import User, Client
from app.database.transaction import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = get_logger(__name__)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_name: str
    client_id: str | None = None


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> APIResponse:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise UnauthorizedException("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedException("Account is disabled")

    # Fetch client name if investor
    client_id = None
    user_name = user.email.split("@")[0]  # fallback

    if user.client_id:
        client_result = await db.execute(select(Client).where(Client.id == user.client_id))
        client = client_result.scalar_one_or_none()
        if client:
            user_name = client.name
            client_id = str(user.client_id)

    token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
        client_id=user.client_id,
    )

    logger.info("user_logged_in", email=user.email, role=user.role.value)

    return success_response(
        data=LoginResponse(
            access_token=token,
            role=user.role.value,
            user_name=user_name,
            client_id=client_id,
        )
    )


@router.get("/me")
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    name = current_user.email.split("@")[0]

    if current_user.client_id:
        client_result = await db.execute(
            select(Client).where(Client.id == current_user.client_id)
        )
        client = client_result.scalar_one_or_none()
        if client:
            name = client.name

    return success_response(
        data={
            "user_id": str(current_user.user_id),
            "email": current_user.email,
            "role": current_user.role.value,
            "name": name,
            "client_id": str(current_user.client_id) if current_user.client_id else None,
        }
    )
