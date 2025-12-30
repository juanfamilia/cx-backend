# shared/routes/onboarding_router.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.db import get_db
from shared.utils.deps import get_current_user
from shared.services.onboarding_services import OnboardingService
from shared.models.user_model import User

router = APIRouter(
    prefix="/onboarding",
    tags=["Onboarding"],
)


@router.get("/status")
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Retorna el estado de onboarding del usuario autenticado.
    El frontend decide si muestra o no el tour.
    """
    return await OnboardingService.get_status(
        user_id=current_user.id,
        session=session,
    )
