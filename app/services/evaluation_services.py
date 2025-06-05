import datetime
import uuid
import boto3
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.campaign_model import Campaign
from app.models.evaluation_model import (
    Evaluation,
    EvaluationAnswer,
    EvaluationCreate,
    EvaluationPublic,
    EvaluationUpdate,
    StatusEnum,
)
from app.models.survey_forms_model import SurveyForm
from app.models.survey_model import SurveySection
from app.models.video_model import Video
from app.utils.exeptions import NotFoundException
from app.utils.helpers.s3_get_url import get_s3_url


async def get_evaluation(session: AsyncSession, evaluation_id: int) -> EvaluationPublic:

    query = (
        select(Evaluation)
        .where(Evaluation.id == evaluation_id, Evaluation.deleted_at == None)
        .options(
            selectinload(Evaluation.evaluation_answers),
            selectinload(Evaluation.video),
            selectinload(Evaluation.campaign)
            .selectinload(Campaign.survey)
            .selectinload(SurveyForm.sections)
            .selectinload(SurveySection.aspects),
        )
    )

    result = await session.execute(query)
    db_evaluation = result.scalars().first()

    if not db_evaluation:
        raise NotFoundException("Evaluation not found")

    return db_evaluation


async def get_evaluation_answer(
    session: AsyncSession, evaluation_answer_id: int
) -> EvaluationAnswer:
    query = select(EvaluationAnswer).where(
        EvaluationAnswer.id == evaluation_answer_id,
        EvaluationAnswer.deleted_at == None,
    )

    result = await session.execute(query)
    db_evaluation_answer = result.scalars().first()

    if not db_evaluation_answer:
        raise NotFoundException("Evaluation answer not found")

    return db_evaluation_answer


async def create_evaluation(
    session: AsyncSession, evaluation: EvaluationCreate
) -> Evaluation:

    db_evaluation = Evaluation(**evaluation.model_dump(exclude={"evaluation_answers"}))

    session.add(db_evaluation)
    await session.commit()
    await session.refresh(db_evaluation)

    db_answers = []
    for answer in evaluation.evaluation_answers:
        db_answer = EvaluationAnswer(
            **answer.model_dump(exclude={"evaluation_id"}),
            evaluation_id=db_evaluation.id,
        )
        session.add(db_answer)
        db_answers.append(db_answer)

    await session.commit()

    return db_evaluation


async def update_evaluation(
    session: AsyncSession, evaluation_id: int, evaluation_update: EvaluationUpdate
) -> Evaluation:
    db_evaluation = await get_evaluation(session, evaluation_id)

    evaluation_update.status = StatusEnum.UPDATED

    evaluation_data = evaluation_update.model_dump(
        exclude={"evaluation_answers"}, exclude_unset=True
    )

    db_evaluation.sqlmodel_update(evaluation_data)
    session.add(db_evaluation)

    if evaluation_update.evaluation_answers:
        for answer in evaluation_update.evaluation_answers:
            db_answer = await get_evaluation_answer(session, answer.id)
            answer_data = answer.model_dump(exclude_unset=True)

            db_answer.sqlmodel_update(answer_data)
            session.add(db_answer)

    await session.commit()
    await session.refresh(db_evaluation)

    return db_evaluation


async def soft_delete_evaluation(
    session: AsyncSession, evaluation_id: int
) -> EvaluationPublic:
    db_evaluation = await get_evaluation(session, evaluation_id)

    db_evaluation.deleted_at = datetime.now()

    session.add(db_evaluation)
    await session.commit()
    await session.refresh(db_evaluation)

    return db_evaluation
