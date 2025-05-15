from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import (
    create_access_token,
    verify_password,
)
from app.core.config import settings
from app.models.user_model import UserPublic
from app.services.users_services import get_user_by_email
from app.utils.exeptions import (
    DisabledException,
    InvalidCredentialsException,
)


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_by_email(session, form_data.username)
    public_user = UserPublic.model_validate(user)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise InvalidCredentialsException()

    if user.deleted_at:
        raise DisabledException("User disabled or deleted")

    access_token = create_access_token(
        user.email,
        timedelta(days=settings.JWT_EXPIRE),
    )

    return {
        "access_token": access_token,
        "user": public_user,
    }
