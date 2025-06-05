from typing import List
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.models.zone_model import ZonePublic
from app.services.zone_services import get_limit_zones, get_zone, get_zones
from app.utils.deps import check_company_payment_status, get_auth_user


router = APIRouter(
    prefix="/zone",
    tags=["Zone"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/")
async def get_all(
    request: Request, session: AsyncSession = Depends(get_db)
) -> List[ZonePublic]:

    match request.state.user.role:
        case 0:
            return await get_zones(session)

        case 1:
            return await get_zones(session)

        case 2:
            return await get_limit_zones(session, request.state.user.id)

        case 3:
            return await get_limit_zones(session, request.state.user.id)


@router.get("/{zone_id}")
async def get_one(
    zone_id: int,
    session: AsyncSession = Depends(get_db),
) -> ZonePublic:

    zone = await get_zone(session, zone_id)

    return zone
