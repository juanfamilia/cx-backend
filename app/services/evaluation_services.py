# app/services/evaluation_services.py

from datetime import datetime
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.evaluation_model import (
    Evaluation,
    EvaluationAnswer,
    EvaluationCreate,
    EvaluationPublic,
    EvaluationUpdate,
    EvaluationAnswerBase,
    EvaluationAnswerUpdate,
    StatusChangeRequest,
)
from app.utils.exeptions import NotFoundException
from app.services.scoring_services import calculate_evaluation_scores, ScoringError


# =========================================================
# HELPERS
# =========================================================

async def get_evaluation(session: AsyncSession, evaluation_id: int) -> Evaluation:
    q = select(Evaluation).where(
        Evaluation.id == evaluation_id,
        Evaluation.deleted_at.is_(None)
    )
    res = await session.execute(q)
    evaluation = res.scalars().first()

    if not evaluation:
        raise NotFoundException("Evaluation not found")

    return evaluation


async def get_evaluation_answer(session: AsyncSession, answer_id: int) -> EvaluationAnswer:
    q = select(EvaluationAnswer).where(
        EvaluationAnswer.id == answer_id,
        EvaluationAnswer.deleted_at.is_(None)
    )
    res = await session.execute(q)
    ans = res.scalars().first()

    if not ans:
        raise NotFoundException("Evaluation answer not found")

    return ans


# =========================================================
# GET LIST (get_evaluations)
# =========================================================

async def get_evaluations(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 10,
    filter: Optional[str] = None,
    search: Optional[str] = None,
    company_id: Optional[int] = None,
    user_id: Optional[int] = None,
):
    q = select(Evaluation).where(Evaluation.deleted_at.is_(None))

    # Company filter
    if company_id:
        q = q.where(Evaluation.company_id == company_id)

    # User filter (role 3)
    if user_id:
        q = q.where(Evaluation.user_id == user_id)

    # Status filter
    if filter:
        q = q.where(Evaluation.status == filter)

    # Simple search
    if search:
        search_term = f"%{search}%"
        q = q.where(
            Evaluation.location.ilike(search_term)
            | Evaluation.evaluated_collaborator.ilike(search_term)
        )

    q = q.order_by(Evaluation.created_at.desc())
    q = q.offset(offset).limit(limit)

    res = await session.execute(q)
    evaluations = res.scalars().all()

    total = len(evaluations)

    return {"items": evaluations, "total": total}


# =========================================================
# STATUS CHANGE
# =========================================================

async def change_evaluation_status(
    session: AsyncSession,
    evaluation_id: int,
    status_request: StatusChangeRequest
) -> Evaluation:

    evaluation = await get_evaluation(session, evaluation_id)

    evaluation.status = status_request.status.value
    session.add(evaluation)

    await session.commit()
    await session.refresh(evaluation)

    return evaluation


# =========================================================
# CREATE EVALUATION
# =========================================================

async def create_evaluation(
    session: AsyncSession, evaluation: EvaluationCreate
) -> Evaluation:

    # Create evaluation header
    db_evaluation = Evaluation(
        **evaluation.model_dump(exclude={"evaluation_answers"})
    )
    session.add(db_evaluation)
    await session.flush()  # Obtain ID

    # Prepare payload for scoring
    answers_payload = [
        {
            "aspect_id": ans.aspect_id,
            "value_number": ans.value_number,
            "value_boolean": ans.value_boolean,
            "comment": ans.comment,
        }
        for ans in evaluation.evaluation_answers
    ]

    # Compute scoring
    try:
        scoring = await calculate_evaluation_scores(
            session,
            db_evaluation.campaigns_id,
            answers_payload
        )
    except ScoringError:
        raise

    # Save each answer with scoring metadata
    for ans in answers_payload:
        aspect_id = ans["aspect_id"]

        awarded = 0.0
        aspect_max = 0.0
        section_max = 0.0

        for section_data in scoring["sections"].values():
            if aspect_id in section_data["aspects"]:
                aspect_data = section_data["aspects"][aspect_id]
                awarded = float(aspect_data["awarded"])
                aspect_max = float(aspect_data["aspect_max"])
                section_max = float(section_data["section_max"])
                break

        db_answer = EvaluationAnswer(
            evaluation_id=db_evaluation.id,
            aspect_id=aspect_id,
            value_number=ans.get("value_number"),
            value_boolean=ans.get("value_boolean"),
            comment=ans.get("comment"),
            recorded_aspect_max=aspect_max,
            recorded_points_awarded=awarded,
            recorded_section_max=section_max,
        )
        session.add(db_answer)

    # Totals
    db_evaluation.total_score = float(scoring["total_awarded"])
    db_evaluation.percentage_score = float(scoring["percentage"])

    await session.commit()
    await session.refresh(db_evaluation)

    return db_evaluation


# =========================================================
# UPDATE EVALUATION
# =========================================================

async def update_evaluation(
    session: AsyncSession,
    evaluation_id: int,
    evaluation_update: EvaluationUpdate
) -> Evaluation:

    db_evaluation = await get_evaluation(session, evaluation_id)

    evaluation_data = evaluation_update.model_dump(
        exclude={"evaluation_answers"},
        exclude_unset=True
    )
    db_evaluation.sqlmodel_update(evaluation_data)
    session.add(db_evaluation)
    await session.flush()

    if evaluation_update.evaluation_answers:

        answers_payload = []

        for ans in evaluation_update.evaluation_answers:
            db_ans = await get_evaluation_answer(session, ans.id)

            update_data = ans.model_dump(exclude_unset=True)
            db_ans.sqlmodel_update(update_data)
            session.add(db_ans)

            answers_payload.append({
                "aspect_id": db_ans.aspect_id,
                "value_number": db_ans.value_number,
                "value_boolean": db_ans.value_boolean,
                "comment": db_ans.comment,
            })

        try:
            scoring = await calculate_evaluation_scores(
                session,
                db_evaluation.campaigns_id,
                answers_payload
            )
        except ScoringError:
            raise

        for ans_payload in answers_payload:
            aspect_id = ans_payload["aspect_id"]

            awarded = aspect_max = section_max = 0.0

            for sdata in scoring["sections"].values():
                if aspect_id in sdata["aspects"]:
                    asp = sdata["aspects"][aspect_id]
                    awarded = float(asp["awarded"])
                    aspect_max = float(asp["aspect_max"])
                    section_max = float(sdata["section_max"])
                    break

            q = select(EvaluationAnswer).where(
                EvaluationAnswer.evaluation_id == db_evaluation.id,
                EvaluationAnswer.aspect_id == aspect_id,
                EvaluationAnswer.deleted_at.is_(None)
            )
            res = await session.execute(q)
            db_ans = res.scalars().first()

            if db_ans:
                db_ans.recorded_aspect_max = aspect_max
                db_ans.recorded_points_awarded = awarded
                db_ans.recorded_section_max = section_max
                session.add(db_ans)

        db_evaluation.total_score = float(scoring["total_awarded"])
        db_evaluation.percentage_score = float(scoring["percentage"])

    await session.commit()
    await session.refresh(db_evaluation)

    return db_evaluation


# =========================================================
# SOFT DELETE
# =========================================================

async def soft_delete_evaluation(session: AsyncSession, evaluation_id: int):
    db_eval = await get_evaluation(session, evaluation_id)
    db_eval.deleted_at = datetime.utcnow()
    session.add(db_eval)
    await session.commit()
