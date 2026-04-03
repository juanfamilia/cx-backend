from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from starlette.requests import Request

from app.core.db import get_db
from app.core.security import decode_token, decode_token_no_verify
from app.models.user_model import UserPublic
from app.services.payment_services import is_company_payment_valid
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
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
        )

    payload = decode_token(token)

    request.state.user = user

    return user


async def check_company_payment_status(
    user=Depends(get_auth_user),
    session: AsyncSession = Depends(get_db),
):
    # Superadmin: no amarrar a pago de una sola empresa (puede no tener company_id).
    if user.role == 0:
        return True

    if user.company_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Tu cuenta no tiene una empresa asignada. "
                "Contacta al administrador para poder crear usuarios o usar el sistema."
            ),
        )

    payment = await is_company_payment_valid(user.company_id, session)

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"El pago de la empresa ha expirado",
        )

    return True
