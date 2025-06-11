from datetime import datetime
from typing import Optional
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_, func, or_, select
from sqlalchemy.orm import selectinload

from app.models.campaign_model import Campaign
from app.models.campaign_user_model import (
    CampaignUser,
    CampaignUserPublic,
    CampaignUsersPublic,
)
from app.models.campaign_zone_model import (
    CampaignZone,
    CampaignZonePublic,
    CampaignZonesPublic,
    currentAssignedCampaign,
)
from app.models.survey_forms_model import SurveyForm
from app.models.survey_model import SurveySection
from app.models.user_model import User
from app.models.user_zone_model import UserZone
from app.models.zone_model import Zone
from app.types.pagination import Pagination
from app.utils.exeptions import NotFoundException


async def get_assigments_by_user(
    session: AsyncSession,
    offset: int = 0,
    limit: int = Query(default=10, le=50),
    filter: Optional[str] = None,
    search: Optional[str] = None,
    company_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> CampaignUsersPublic:

    query = (
        select(CampaignUser, func.count().over().label("total"))
        .join(Campaign, CampaignUser.campaign_id == Campaign.id, isouter=True)
        .join(User, CampaignUser.user_id == User.id, isouter=True)
        .join(UserZone, User.id == UserZone.user_id)
        .where(CampaignUser.deleted_at == None)
        .options(selectinload(CampaignUser.user), selectinload(CampaignUser.campaign))
    )

    if company_id is not None:
        query = query.where(User.company_id == company_id)

    if user_id is not None:
        # Obtener las zonas asignadas al usuario que realiza la petición
        user_zones = await session.execute(
            select(UserZone.zone_id).where(
                UserZone.user_id == user_id, UserZone.deleted_at == None
            )
        )
        zone_ids = [row[0] for row in user_zones]

        if not zone_ids:
            raise NotFoundException("No zones assigned to user")

        # Filtrar las asignaciones de usuarios dentro de esas zonas
        query = query.where(UserZone.zone_id.in_(zone_ids))

    if filter and search:
        match filter:
            case "full_name":
                names = search.split()
                if len(names) == 1:
                    query = query.where(
                        or_(
                            User.first_name.ilike(f"%{names[0]}%"),
                            User.last_name.ilike(f"%{names[0]}%"),
                        )
                    )
                else:
                    query = query.where(
                        and_(
                            User.first_name.ilike(f"%{names[0]}%"),
                            User.last_name.ilike(f"%{' '.join(names[1:])}%"),
                        )
                    )

            case "campaign":
                query = query.where(Campaign.name.ilike(f"%{search}%"))

    query = query.order_by(CampaignUser.id).offset(offset).limit(limit)

    result = await session.execute(query)
    db_campaign_users = result.unique().all()

    if not db_campaign_users:
        raise NotFoundException("Campaign by users not found")

    campaign_users = [row[0] for row in db_campaign_users]
    total = db_campaign_users[0][1] if db_campaign_users else 0
    pagination = Pagination(first=offset, rows=limit, total=total)

    return CampaignUsersPublic(data=campaign_users, pagination=pagination)


async def get_campaign_user(
    session: AsyncSession, campaign_user_id: int, company_id: Optional[int] = None
) -> CampaignUserPublic:
    query = (
        select(CampaignUser)
        .join(Campaign, CampaignUser.campaign_id == Campaign.id, isouter=True)
        .where(CampaignUser.id == campaign_user_id, CampaignUser.deleted_at == None)
        .options(selectinload(CampaignUser.user), selectinload(CampaignUser.campaign))
    )

    if company_id is not None:
        query = query.where(Campaign.company_id == company_id)

    result = await session.execute(query)
    db_campaign_user = result.scalars().first()

    if not db_campaign_user:
        raise NotFoundException("Campaign user not found")

    return db_campaign_user


async def assign_users_to_campaign(
    session: AsyncSession, campaign_id: int, user_ids: list[int]
):
    # Crea nuevas asignaciones
    assignments = [
        CampaignUser(campaign_id=campaign_id, user_id=user_id) for user_id in user_ids
    ]
    session.add_all(assignments)
    await session.commit()


async def soft_delete_campaign_users(
    session: AsyncSession, asignment_id: int, company_id: Optional[int] = None
) -> CampaignUserPublic:

    db_campaign_user = await get_campaign_user(session, asignment_id, company_id)

    db_campaign_user.deleted_at = datetime.now()

    session.add(db_campaign_user)
    await session.commit()
    await session.refresh(db_campaign_user)

    return db_campaign_user


# Assign Campaign to Zones Service


async def get_assigments_by_zones(
    session: AsyncSession,
    offset: int = 0,
    limit: int = Query(default=10, le=50),
    filter: Optional[str] = None,
    search: Optional[str] = None,
    company_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> CampaignZonesPublic:

    query = (
        select(CampaignZone, func.count().over().label("total"))
        .join(Campaign, CampaignZone.campaign_id == Campaign.id, isouter=True)
        .join(Zone, CampaignZone.zone_id == Zone.id, isouter=True)
        .where(CampaignZone.deleted_at == None)
        .options(selectinload(CampaignZone.zone), selectinload(CampaignZone.campaign))
    )

    if company_id is not None:
        query = query.where(Campaign.company_id == company_id)

    if user_id is not None:
        user_zones = await session.execute(
            select(UserZone.zone_id).where(
                UserZone.user_id == user_id, UserZone.deleted_at == None
            )
        )
        zones_ids = [row[0] for row in user_zones]

        if not zones_ids:
            raise NotFoundException("No zones assigned to user")

        query = query.where(CampaignZone.zone_id.in_(zones_ids))

    if filter and search:
        match filter:
            case "zone":
                query = query.where(Zone.name.ilike(f"%{search}%"))

            case "campaign":
                query = query.where(Campaign.name.ilike(f"%{search}%"))

    query = query.order_by(CampaignZone.id).offset(offset).limit(limit)

    result = await session.execute(query)
    db_campaign_zones = result.unique().all()

    if not db_campaign_zones:
        raise NotFoundException("Campaign by zones not found")

    campaign_users = [row[0] for row in db_campaign_zones]
    total = db_campaign_zones[0][1] if db_campaign_zones else 0
    pagination = Pagination(first=offset, rows=limit, total=total)

    return CampaignZonesPublic(data=campaign_users, pagination=pagination)


async def get_campaign_zone(
    session: AsyncSession,
    campaign_zone_id: int,
    company_id: Optional[int] = None,
) -> CampaignZonePublic:
    query = (
        select(CampaignZone)
        .join(Campaign, CampaignZone.campaign_id == Campaign.id, isouter=True)
        .where(CampaignZone.id == campaign_zone_id, CampaignZone.deleted_at == None)
        .options(selectinload(CampaignZone.campaign), selectinload(CampaignZone.zone))
    )

    if company_id is not None:
        query = query.where(Campaign.company_id == company_id)

    result = await session.execute(query)
    db_campaign_zone = result.scalars().first()

    if not db_campaign_zone:
        raise NotFoundException("Campaign zone not found")

    return db_campaign_zone


async def assign_zones_to_campaign(
    session: AsyncSession, campaign_id: int, zone_ids: list[int]
):
    assignments = [
        CampaignZone(campaign_id=campaign_id, zone_id=zone_id) for zone_id in zone_ids
    ]
    session.add_all(assignments)
    await session.commit()


async def soft_delete_campaign_zone(
    session: AsyncSession,
    asignment_id: int,
    company_id: Optional[int] = None,
):

    db_campaign_zone = await get_campaign_zone(session, asignment_id, company_id)

    db_campaign_zone.deleted_at = datetime.now()

    session.add(db_campaign_zone)
    await session.commit()
    await session.refresh(db_campaign_zone)

    return {"message": "Campaign zone deleted"}


async def get_assiments_campaigns(
    session: AsyncSession,
    user_id: int,
    company_id: Optional[int] = None,
) -> currentAssignedCampaign:
    query_by_user = (
        select(CampaignUser)
        .join(Campaign, CampaignUser.campaign_id == Campaign.id, isouter=True)
        .where(
            CampaignUser.user_id == user_id,
            Campaign.date_end >= datetime.now(),
            CampaignUser.deleted_at == None,
        )
        .options(selectinload(CampaignUser.campaign))
        .order_by(CampaignUser.id)
    )
    result_by_user = await session.execute(query_by_user)
    db_campaigns = result_by_user.scalars().all()

    user_zones = await session.execute(
        select(UserZone.zone_id).where(
            UserZone.user_id == user_id, UserZone.deleted_at == None
        )
    )
    zone_ids = [row[0] for row in user_zones]

    if not zone_ids:
        raise NotFoundException("No zones assigned to user")

    query_by_zone = (
        select(CampaignZone)
        .join(Campaign, CampaignZone.campaign_id == Campaign.id, isouter=True)
        .where(
            CampaignZone.zone_id.in_(zone_ids),
            Campaign.date_end >= datetime.now(),
            CampaignZone.deleted_at == None,
        )
        .options(selectinload(CampaignZone.campaign), selectinload(CampaignZone.zone))
        .order_by(CampaignZone.id)
    )
    result_by_zone = await session.execute(query_by_zone)
    db_campaigns_zone = result_by_zone.scalars().all()

    if not db_campaigns and db_campaigns_zone:
        raise NotFoundException("Campaigns not found")

    return currentAssignedCampaign(by_user=db_campaigns, by_zone=db_campaigns_zone)
