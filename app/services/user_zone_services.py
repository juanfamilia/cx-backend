from datetime import datetime
from typing import List, Optional
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select, update
from sqlalchemy.orm import selectinload

from app.models.user_model import User
from app.models.user_zone_model import (
    AssignZonesRequest,
    UserZone,
    UserZonePublic,
    UserZonesPublic,
)
from app.models.zone_model import Zone, ZonePublic
from app.services.users_services import get_user
from app.types.pagination import Pagination
from app.utils.exeptions import NotFoundException, PermissionDeniedException


async def get_users_zones(
    session: AsyncSession,
    offset: int = 0,
    limit: int = Query(default=10, le=50),
    filter: Optional[str] = None,
    search: Optional[str] = None,
    company_id: int | None = None,
) -> UserZonesPublic:

    query = (
        select(UserZone, func.count().over().label("total"))
        .join(Zone, UserZone.zone_id == Zone.id, isouter=True)
        .join(User, User.id == UserZone.user_id)
        .options(selectinload(UserZone.zone), selectinload(UserZone.user))
        .where(UserZone.deleted_at == None)
    )

    if company_id is not None:
        query = query.where(User.company_id == company_id)

    if filter and search:
        match filter:
            case "zone":
                query = query.where(Zone.name.ilike(f"%{search}%"))

    query = query.order_by(UserZone.id).offset(offset).limit(limit)

    result = await session.execute(query)
    db_user_zones = result.unique().all()

    if not db_user_zones:
        raise NotFoundException("User zones not found")

    user_zones = [row[0] for row in db_user_zones]
    total = db_user_zones[0][1] if db_user_zones else 0
    pagination = Pagination(first=offset, rows=limit, total=total)

    return UserZonesPublic(data=user_zones, pagination=pagination)


async def get_user_zone(session: AsyncSession, user_zone_id: int) -> UserZonePublic:
    query = (
        select(UserZone)
        .where(UserZone.id == user_zone_id, UserZone.deleted_at == None)
        .options(selectinload(UserZone.zone), selectinload(UserZone.user))
    )

    result = await session.execute(query)
    db_user_zone = result.scalars().first()

    if not db_user_zone:
        raise NotFoundException("User zone not found")

    return db_user_zone


async def create_zone_users(
    session: AsyncSession,
    data: AssignZonesRequest,
):

    await session.execute(
        update(UserZone)
        .where(UserZone.user_id == data.user_id)
        .where(UserZone.deleted_at.is_(None))
        .values(deleted_at=datetime.now())
    )

    for zone_id in data.zone_ids:
        user_zone = UserZone(user_id=data.user_id, zone_id=zone_id)
        session.add(user_zone)

    await session.commit()

    return {"message": "User zones created"}


async def update_user_zone(
    session: AsyncSession,
    user_zone_id: int,
    new_zone_id: int,
) -> UserZonePublic:
    db_user_zone = await get_user_zone(session, user_zone_id)

    db_user_zone.zone_id = new_zone_id

    await session.commit()
    await session.refresh(db_user_zone)

    return db_user_zone


async def soft_delete_user_zone(
    session: AsyncSession, user_zone_id: int
) -> UserZonePublic:
    db_user_zone = await get_user_zone(session, user_zone_id)

    db_user_zone.deleted_at = datetime.now()

    await session.commit()
    await session.refresh(db_user_zone)

    return db_user_zone
