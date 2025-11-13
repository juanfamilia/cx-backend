from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.campaign_model import (
    CampaignBase,
    CampaignPublic,
    CampaignUpdate,
    CampaignsPublic,
)
from app.services.campaign_services import (
    create_campaign,
    get_campaign,
    get_campaigns,
    soft_delete_campaign,
    update_campaign,
)
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException


router = APIRouter(
    prefix="/campaign",
    tags=["Campaign"],
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
) -> CampaignsPublic:
    if request.state.user.role not in [1, 2]:
        raise PermissionDeniedException(custom_message="retrieve campaigns")

    campaigns = await get_campaigns(
        session, offset, limit, filter, search, request.state.user.company_id
    )

    return campaigns


@router.get("/{campaign_id}")
async def get_one(
    campaign_id: int,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> CampaignPublic:

    if request.state.user.role not in [1, 2, 3]:
        raise PermissionDeniedException(custom_message="retrieve this campaign")

    campaign = await get_campaign(session, campaign_id)

    if campaign.company_id != request.state.user.company_id:
        raise PermissionDeniedException(custom_message="retrieve this campaign")

    return campaign


@router.post("/")
async def create(
    request: Request,
    campaign_create: CampaignBase,
    session: AsyncSession = Depends(get_db),
) -> CampaignPublic:

    if request.state.user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="create a campaign")

    campaign_create.company_id = request.state.user.company_id
    campaign_create.date_start = campaign_create.date_start.replace(tzinfo=None)
    campaign_create.date_end = campaign_create.date_end.replace(tzinfo=None)

    campaign = await create_campaign(session, campaign_create)

    return campaign


@router.put("/{campaign_id}")
async def update(
    campaign_id: int,
    campaign_update: CampaignUpdate,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> CampaignPublic:

    if request.state.user.role != 1:
        raise PermissionDeniedException(custom_message="update this campaign")

    campaign_db = await get_campaign(session, campaign_id)

    if campaign_db.company_id != request.state.user.company_id:
        raise PermissionDeniedException(custom_message="update this campaign")

    campaign_update.date_start = campaign_update.date_start.replace(tzinfo=None)
    campaign_update.date_end = campaign_update.date_end.replace(tzinfo=None)

    campaign = await update_campaign(session, campaign_id, campaign_update)

    return campaign


@router.delete("/{campaign_id}")
async def delete(
    request: Request,
    campaign_id: int,
    session: AsyncSession = Depends(get_db),
):

    if request.state.user.role != 1:
        raise PermissionDeniedException(custom_message="delete this campaign")

    campaign_db = await get_campaign(session, campaign_id)

    if campaign_db.company_id != request.state.user.company_id:
        raise PermissionDeniedException(custom_message="update this campaign")

    await soft_delete_campaign(session, campaign_id)

    return {"message": "Campaign deleted"}
