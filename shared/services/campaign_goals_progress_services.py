from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.campaign_goals_progress_model import CampaignGoalsProgress
from app.utils.exeptions import NotFoundException


async def get_campaign_goals_progress(
    session: AsyncSession, user_id: int
) -> list[CampaignGoalsProgress]:
    today = date.today()

    query = (
        select(CampaignGoalsProgress)
        .where(CampaignGoalsProgress.evaluator_id == user_id)
        .where(CampaignGoalsProgress.date_start <= today)
        .where(CampaignGoalsProgress.date_end >= today)
    )

    result = await session.execute(query)
    goals_progress = result.scalars().all()

    if not goals_progress:
        raise NotFoundException("Goals progress not found")

    return goals_progress
