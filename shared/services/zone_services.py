from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from shared.models.user_zone_model import UserZone
from shared.models.zone_model import Zone, ZoneBase, ZonePublic
from shared.utils.exceptions import NotFoundException

async def create_zone(session: AsyncSession, data: ZoneBase, user) -> ZonePublic:
    zone = Zone(**data.model_dump())
    session.add(zone)
    await session.commit()
    await session.refresh(zone)
    return zone

async def get_zones(session: AsyncSession) -> List[ZonePublic]:
    query = select(Zone).where(Zone.deleted_at == None).order_by(Zone.id)

    result = await session.execute(query)
    db_zones = result.scalars().all()

    if not db_zones:
        raise NotFoundException("Zones not found")

    return db_zones


async def get_limit_zones(session: AsyncSession, user_id: int) -> List[ZonePublic]:
    query = (
        select(Zone)
        .join(UserZone, Zone.id == UserZone.zone_id)
        .where(
            UserZone.user_id == user_id,
            Zone.deleted_at == None,
            UserZone.deleted_at == None,
        )
        .order_by(Zone.id)
    )

    result = await session.execute(query)
    db_zones = result.scalars().all()

    if not db_zones:
        raise NotFoundException("No zones assigned to user")

    return db_zones


async def get_zone(session: AsyncSession, zone_id: int) -> ZonePublic:
    db_zone = await session.get(Zone, zone_id)

    if not db_zone:
        raise NotFoundException("Zone not found")

    return db_zone
