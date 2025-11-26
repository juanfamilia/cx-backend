from fastapi import APIRouter
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.db import get_db
from shared.models.campaign_goals_progress_model import CampaignGoalsProgress
from shared.services.campaign_goals_progress_services import get_campaign_goals_progress
from shared.utils.deps import check_company_payment_status, get_auth_user


router = APIRouter(
    prefix="/campaign-goals-progress",
    tags=["Campaign Goals Progress"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/by-evaluator")
async def get_all(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> list[CampaignGoalsProgress]:

    goals_progress = await get_campaign_goals_progress(session, request.state.user.id)

    return goals_progress
