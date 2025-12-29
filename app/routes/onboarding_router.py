from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.db import get_db
from shared.utils.deps import get_current_user
from shared.services.onboarding_services import OnboardingService

router = APIRouter(
    prefix="/onboarding",
    tags=["Onboarding"],
)


@router.get("/status")
async def get_onboarding_status(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await OnboardingService.get_status(
        user_id=current_user.id,
        session=session,
    )
