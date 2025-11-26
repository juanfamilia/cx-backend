from datetime import datetime
from typing import Optional
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select
from sqlalchemy.orm import selectinload

from app.models.campaign_model import (
    Campaign,
    CampaignBase,
    CampaignPublic,
    CampaignUpdate,
    CampaignsPublic,
)
from app.models.survey_forms_model import SurveyForm
from app.models.survey_model import SurveySection
from app.types.pagination import Pagination
from app.utils.exeptions import NotFoundException


async def get_campaigns(
    session: AsyncSession,
    offset: int = 0,
    limit: int = Query(default=10, le=50),
    filter: Optional[str] = None,
    search: Optional[str] = None,
    company_id: int | None = None,
) -> CampaignsPublic:

    query = (
        select(Campaign, func.count().over().label("total"))
        .options(selectinload(Campaign.survey))
        .where(Campaign.company_id == company_id, Campaign.deleted_at == None)
    )

    if filter and search:
        match filter:
            case "name":
                query = query.where(Campaign.name.ilike(f"%{search}%"))

            case "objective":
                query = query.where(Campaign.objective.ilike(f"%{search}%"))

            case "survey":
                query = query.where(SurveyForm.title.ilike(f"%{search}%"))

    query = query.order_by(Campaign.id).offset(offset).limit(limit)

    result = await session.execute(query)
    db_campaigns = result.unique().all()

    if not db_campaigns:
        raise NotFoundException("Campaigns not found")

    campaigns = [CampaignPublic.model_validate(row[0]) for row in db_campaigns]
    total = db_campaigns[0][1] if db_campaigns else 0
    pagination = Pagination(first=offset, rows=limit, total=total)

    return CampaignsPublic(data=campaigns, pagination=pagination)


async def get_campaign(session: AsyncSession, campaign_id: int) -> CampaignPublic:
    query = (
        select(Campaign)
        .options(
            selectinload(Campaign.survey)
            .selectinload(SurveyForm.sections)
            .selectinload(SurveySection.aspects)
        )
        .where(Campaign.id == campaign_id, Campaign.deleted_at == None)
    )

    result = await session.execute(query)
    db_campaign = result.scalars().first()

    if not db_campaign:
        raise NotFoundException("Campaign not found")

    return db_campaign


async def create_campaign(
    session: AsyncSession, campaign: CampaignBase
) -> CampaignPublic:
    db_campaign = Campaign(**campaign.model_dump())

    session.add(db_campaign)
    await session.commit()
    await session.refresh(db_campaign)

    return CampaignPublic.model_validate(db_campaign)


async def update_campaign(
    session: AsyncSession, campaign_id: int, campaign: CampaignUpdate
) -> CampaignPublic:
    db_campaign = await get_campaign(session, campaign_id)

    campaign_update = campaign.model_dump(exclude_unset=True)
    db_campaign.sqlmodel_update(campaign_update)

    session.add(db_campaign)
    await session.commit()
    await session.refresh(db_campaign)

    return CampaignPublic.model_validate(db_campaign)


async def soft_delete_campaign(
    session: AsyncSession, campaign_id: int
) -> CampaignPublic:
    db_campaign = await get_campaign(session, campaign_id)

    db_campaign.deleted_at = datetime.now()

    session.add(db_campaign)
    await session.commit()
    await session.refresh(db_campaign)

    return CampaignPublic.model_validate(db_campaign)
