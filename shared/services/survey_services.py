from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload

from app.models.survey_model import SurveySection
from app.utils.exeptions import NotFoundException


async def get_survey(session: AsyncSession) -> List[SurveySection]:
    query = (
        select(SurveySection)
        .options(selectinload(SurveySection.aspects))
        .order_by(SurveySection.order)
    )
    result = await session.execute(query)
    db_sections = result.scalars().all()

    if not db_sections:
        raise NotFoundException("Survey not found")

    for section in db_sections:
        section.aspects.sort(key=lambda a: a.order)

    return db_sections
