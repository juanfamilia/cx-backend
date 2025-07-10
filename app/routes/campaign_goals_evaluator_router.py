from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.campaign_goals_evaluator_model import (
    CampaignGoalsEvaluatorBase,
    CampaignGoalsEvaluatorPublic,
    CampaignGoalsEvaluatorUpdate,
    CampaignGoalsEvaluatorsPublic,
)
from app.services.campaign_goals_evaluator_services import (
    create_campaign_goals_evaluator,
    get_campaign_goals_evaluator,
    get_campaign_goals_evaluator_by_id,
    soft_delete_campaign_goals_evaluator,
    update_campaign_goals_evaluator,
)
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException


router = APIRouter(
    prefix="/campaign-goals-evaluator",
    tags=["Campaign Goals by Evaluator"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/")
async def get_all(
    request: Request,
    session: AsyncSession = Depends(get_db),
    offset: int = 0,
    limit: int = Query(default=10, le=50),
    filter: Optional[str] = None,
    search: Optional[str] = None,
) -> CampaignGoalsEvaluatorsPublic:
    if request.state.user.role not in [1, 2]:
        raise PermissionDeniedException(custom_message="retrieve campaigns goals")

    campaign_goals = await get_campaign_goals_evaluator(
        session, offset, limit, filter, search, request.state.user.company_id
    )

    return campaign_goals


@router.get("/{id}")
async def get_one(
    request: Request,
    id: int,
    session: AsyncSession = Depends(get_db),
) -> CampaignGoalsEvaluatorPublic:

    if request.state.user.role not in [1, 2]:
        raise PermissionDeniedException(custom_message="retrieve this campaign goals")

    campaign_goal = await get_campaign_goals_evaluator_by_id(session, id)

    return campaign_goal


@router.post("/")
async def create(
    request: Request,
    campaign_goals_evaluator: CampaignGoalsEvaluatorBase,
    session: AsyncSession = Depends(get_db),
) -> CampaignGoalsEvaluatorPublic:

    if request.state.user.role not in [1, 2]:
        raise PermissionDeniedException(custom_message="create a campaign goals")

    campaign_goals_evaluator = await create_campaign_goals_evaluator(
        session, campaign_goals_evaluator
    )

    return campaign_goals_evaluator


@router.put("/{id}")
async def update(
    request: Request,
    id: int,
    campaign_goals_evaluator: CampaignGoalsEvaluatorUpdate,
    session: AsyncSession = Depends(get_db),
) -> CampaignGoalsEvaluatorPublic:

    if request.state.user.role not in [1, 2]:
        raise PermissionDeniedException(custom_message="update this campaign goals")

    campaign_goals_evaluator = await update_campaign_goals_evaluator(
        session, id, campaign_goals_evaluator
    )

    return campaign_goals_evaluator


@router.delete("/{id}")
async def delete(
    request: Request,
    id: int,
    session: AsyncSession = Depends(get_db),
):

    if request.state.user.role not in [1, 2]:
        raise PermissionDeniedException(custom_message="delete this campaign goals")

    await soft_delete_campaign_goals_evaluator(session, id)

    return {"message": "Campaign goals deleted"}
