# shared/utils/deps.py
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from starlette.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.db import get_db
from shared.core.security import decode_token, decode_token_no_verify
from shared.models.user_model import UserPublic
from shared.services.payment_services import is_company_payment_valid
from shared.services.users_services import get_user_by_email


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_auth_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    session: AsyncSession = Depends(get_db),
) -> Optional[UserPublic]:
    """
    Dependencia que verifica el token JWT y retorna el usuario autenticado.
    También guarda el usuario en request.state.user para acceso posterior.
    """
    payload = decode_token_no_verify(token)
    email = payload.get("sub")

    user = await get_user_by_email(session, email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token inválido"
        )

    payload = decode_token(token)

    request.state.user = user

    return user


async def check_company_payment_status(
    user=Depends(get_auth_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Verifica que la compañía del usuario tenga el pago al día.
    """
    payment = await is_company_payment_valid(user.company_id, session)

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="El pago de la empresa ha expirado",
        )

    return True
