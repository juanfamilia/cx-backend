from datetime import datetime, timedelta, timezone
from numbers import Number
from typing import Annotated
from fastapi import APIRouter, Body, HTTPException, Request, Response, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    verify_password,
)
from app.core.config import settings
from app.models.users_model import UserPublic
from app.services.refresh_token_services import (
    create_refresh_token_db,
    get_refresh_token,
    revoke_refresh_token_db,
)
from app.services.users_services import get_user, get_user_by_email
from app.services.users_token_services import (
    get_or_create_user_key,
)
from app.utils.exeptions import (
    DisabledException,
    InvalidCredentialsException,
    InvalidRefreshTokenException,
)


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_by_email(session, form_data.username)
    public_user = UserPublic.model_validate(user)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise InvalidCredentialsException()

    if user.deleted_at:
        raise DisabledException("User disabled or deleted")

    user_token = await get_or_create_user_key(session, user.id)

    access_token = create_access_token(
        user.email,
        user_token.key,
        timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    )

    refresh_token = create_refresh_token(
        user.id, timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    )

    await create_refresh_token_db(session, user.id, refresh_token)

    # TODO: Crear un nuevo inicio de sesion en alguna tabla de registro
    # TODO: 2FA para el login de todos los usuarios

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        expires=datetime.now(timezone.utc) + timedelta(days=7),
    )
    return {
        "access_token": access_token,
        "user": public_user,
    }


@router.post("/refresh")
async def refresh_access_token(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    refresh_token = request.cookies.get("refresh_token")
    payload = decode_refresh_token(refresh_token)
    user_id: int = int(payload.get("sub"))

    if not user_id:
        raise InvalidRefreshTokenException()

    user = await get_user(session, user_id)

    if not user:
        raise InvalidRefreshTokenException()

    refresh_token_db = await get_refresh_token(session, refresh_token)

    if not refresh_token_db:
        raise InvalidRefreshTokenException()

    user_jwt_key = await get_or_create_user_key(session, refresh_token_db.user_id)

    access_token = create_access_token(
        user.email,
        user_jwt_key.key,
        timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    )

    return {
        "access_token": access_token,
    }


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
):
    refresh_token = request.cookies.get("refresh_token")
    result = await revoke_refresh_token_db(session, refresh_token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token already revoked or not found",
        )

    response.delete_cookie(key="refresh_token")

    return {"message": "Logout successful"}
