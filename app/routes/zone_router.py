from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.models.zone_model import ZonePublic
from app.services.zone_services import get_zone, get_zones
from app.utils.deps import check_company_payment_status, get_auth_user


router = APIRouter(
    prefix="/zone",
    tags=["Zone"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/")
async def get_all(session: AsyncSession = Depends(get_db)) -> List[ZonePublic]:

    zones = await get_zones(session)

    return zones


@router.get("/{zone_id}")
async def get_one(
    zone_id: int,
    session: AsyncSession = Depends(get_db),
) -> ZonePublic:

    zone = await get_zone(session, zone_id)

    return zone
