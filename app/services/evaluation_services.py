import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_, func, or_, select
from sqlalchemy.orm import selectinload

from app.models.campaign_model import Campaign
from app.models.evaluation_model import (
    Evaluation,
    EvaluationAnswer,
    EvaluationCreate,
    EvaluationPublic,
    EvaluationUpdate,
    EvaluationsPublic,
    StatusChangeRequest,
    StatusEnum,
)
from app.models.notification_model import NotificationBase
from app.models.survey_forms_model import SurveyForm
from app.models.survey_model import SurveySection
from app.models.user_model import User
from app.services.notification_services import create_notification
from app.types.pagination import Pagination
from app.utils.exeptions import NotFoundException


async def get_evaluations(
    session: AsyncSession,
    offset: int,
    limit: int,
    filter: Optional[str] = None,
    search: Optional[str] = None,
    company_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> EvaluationsPublic:

    query = (
        select(Evaluation, func.count().over().label("total"))
        .join(Campaign, Evaluation.campaigns_id == Campaign.id, isouter=True)
        .join(User, Evaluation.user_id == User.id, isouter=True)
        .options(selectinload(Evaluation.campaign), selectinload(Evaluation.user))
        .where(Evaluation.deleted_at == None)
    )

    if company_id is not None:
        query = query.where(Campaign.company_id == company_id)

    if user_id is not None:
        query = query.where(
            Evaluation.user_id == user_id, Evaluation.status == StatusEnum.EDIT
        )

    if filter and search:
        match filter:
            case "campaign":
                query = query.where(Campaign.name.ilike(f"%{search}%"))

            case "evaluator":
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

    query = query.order_by(Evaluation.id).offset(offset).limit(limit)

    result = await session.execute(query)
    db_evaluations = result.unique().all()

    if not db_evaluations:
        raise NotFoundException("Evaluations not found")

    evaluations = [row[0] for row in db_evaluations]
    total = db_evaluations[0][1] if db_evaluations else 0
    pagination = Pagination(first=offset, rows=limit, total=total)

    return EvaluationsPublic(data=evaluations, pagination=pagination)


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


async def change_evaluation_status(
    session: AsyncSession, evaluation_id: int, status: StatusChangeRequest
) -> EvaluationPublic:
    db_evaluation = await get_evaluation(session, evaluation_id)

    db_evaluation.status = status.status

    session.add(db_evaluation)
    await session.commit()
    await session.refresh(db_evaluation)

    notification = NotificationBase(
        user_id=db_evaluation.user_id,
        evaluation_id=db_evaluation.id,
        status=status.status,
        comment=status.comment,
    )
    await create_notification(session, notification)

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
