from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.db import get_db
from shared.core.security import create_access_token, verify_password
from shared.core.config import settings
from shared.models.user_model import UserPublic
from shared.services.users_services import get_user_by_email
from shared.services.onboarding_services import OnboardingService
from shared.utils.deps import check_company_payment_status
from shared.utils.exceptions import DisabledException, InvalidCredentialsException

# 🔴 ESTA PARTE ES LA QUE TE FALTA O ESTÁ MAL UBICADA
router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)

@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_by_email(session, form_data.username)

    if not user or not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise InvalidCredentialsException()

    if user.deleted_at:
        raise DisabledException("Usuario desactivado o eliminado")

    # Verificar pago SOLO si el usuario es válido
    await check_company_payment_status(user, session)

    # Asegurar onboarding (NO romper login si falla)
    try:
        await OnboardingService.ensure_exists(
            user_id=user.id,
            company_id=user.company_id,
            session=session,
        )
    except Exception:
        pass

    public_user = UserPublic.model_validate(user)

    access_token = create_access_token(
        user.email,
        timedelta(days=settings.JWT_EXPIRE),
    )

    return {
        "access_token": access_token,
        "user": public_user,
    }
