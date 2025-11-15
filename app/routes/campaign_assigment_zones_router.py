from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.campaign_zone_model import (
    CampaignZonePublic,
    CampaignZonesPublic,
    createCampaignZone,
)
from app.services.campaign_assignment_services import (
    assign_zones_to_campaign,
    get_assigments_by_zones,
    get_campaign_zone,
    soft_delete_campaign_zone,
)
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException


router = APIRouter(
    prefix="/campaign-assignment-zones",
    tags=["Campaign Assigments Zones"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/")
async def get_all_by_zones(
    request: Request,
    session: AsyncSession = Depends(get_db),
    offset: int = 0,
    limit: int = Query(default=10, le=50),
    filter: Optional[str] = None,
    search: Optional[str] = None,
) -> CampaignZonesPublic:

    if request.state.user.role not in [1, 2]:
        raise PermissionDeniedException(custom_message="retrieve campaigns")

    match request.state.user.role:
        case 1:
            campaigns = await get_assigments_by_zones(
                session, offset, limit, filter, search, request.state.user.company_id
            )
        case 2:
            campaigns = await get_assigments_by_zones(
                session,
                offset,
                limit,
                filter,
                search,
                request.state.user.company_id,
                request.state.user.id,
            )

    return campaigns


@router.get("/{assignment_id}")
async def get_one_zone_assignment(
    assignment_id: int,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> CampaignZonePublic:
    if request.state.user.role not in [1, 2]:
        raise PermissionDeniedException(custom_message="retrieve this campaign zone")

    campaign_zone = await get_campaign_zone(
        session, assignment_id, request.state.user.company_id
    )

    return campaign_zone


@router.post("/")
async def assign_zones(
    request: Request,
    data: createCampaignZone,
    session: AsyncSession = Depends(get_db),
):
    if request.state.user.role not in [0,1]:
        raise PermissionDeniedException(custom_message="assign zones to campaign")

    await assign_zones_to_campaign(session, data.campaign_id, data.zone_ids)

    return {"message": "Campaign zones assigned"}


@router.delete("/{assignment_id}")
async def delete_zone(
    assignment_id: int,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    if request.state.user.role != 1:
        raise PermissionDeniedException(custom_message="delete this campaign zone")

    await soft_delete_campaign_zone(
        session, assignment_id, request.state.user.company_id
    )

    return {"message": "Campaign zone deleted"}
