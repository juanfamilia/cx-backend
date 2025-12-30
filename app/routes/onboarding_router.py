from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.db import get_db
from shared.utils.deps import get_current_user
from shared.services.onboarding_services import OnboardingService
from shared.models.user_model import User
from shared.types.onboarding import CompleteTourRequest

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


@router.post(
    "/tour",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def complete_tour(
    payload: CompleteTourRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Registra la finalización o salto de un tour de onboarding.
    """
    await OnboardingService.complete_tour(
        user_id=current_user.id,
        tour=payload.tour,
        completion_type=payload.completion_type,
        session=session,
    )
