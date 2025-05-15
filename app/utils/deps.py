from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from starlette.requests import Request

from app.core.db import get_db
from app.core.security import decode_token, decode_token_no_verify
from app.models.user_model import UserPublic
from app.services.users_services import get_user_by_email
from sqlalchemy.ext.asyncio import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_auth_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    session: AsyncSession = Depends(get_db),
) -> Optional[UserPublic]:

    payload = decode_token_no_verify(token)
    email = payload.get("sub")

    user = await get_user_by_email(session, email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user token"
        )

    payload = decode_token(token)

    request.state.user = user

    return user
