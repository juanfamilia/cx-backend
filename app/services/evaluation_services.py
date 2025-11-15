# app/services/evaluation_services.py (fragmentos relevantes)
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
)
from app.utils.exeptions import NotFoundException
from app.services.scoring_services import calculate_evaluation_scores, ScoringError

# ... otros imports / funciones ...

async def create_evaluation(
    session: AsyncSession, evaluation: EvaluationCreate
) -> Evaluation:

    # Create evaluation record first (status etc.). We'll fill scores after computing.
    db_evaluation = Evaluation(**evaluation.model_dump(exclude={"evaluation_answers"}))
    session.add(db_evaluation)
    await session.flush()  # get db_evaluation.id

    # Build answers list as dicts for scoring
    answers_payload = []
    for answer in evaluation.evaluation_answers:
        answers_payload.append({
            "aspect_id": answer.aspect_id,
            "value_number": answer.value_number,
            "value_boolean": answer.value_boolean,
            "comment": answer.comment,
        })

    # Calculate scoring using campaign -> form mapping
    try:
        scoring = await calculate_evaluation_scores(session, db_evaluation.campaigns_id, answers_payload)
    except ScoringError as e:
        # rollback? we can raise to be handled by router global except
        raise

    # Persist answers with recorded fields
    # We expect evaluation_answers table to have columns: recorded_aspect_max, recorded_points_awarded, recorded_section_max
    for ans in answers_payload:
        aspect_id = ans["aspect_id"]
        # look up computed values
        # find which section contains the aspect in scoring
        awarded = 0.0
        aspect_max = 0.0
        section_max = 0.0
        for sid, sdata in scoring["sections"].items():
            if aspect_id in sdata["aspects"]:
                aspdata = sdata["aspects"][aspect_id]
                awarded = float(aspdata["awarded"])
                aspect_max = float(aspdata["aspect_max"])
                section_max = float(sdata["section_max"])
                break

        db_answer = EvaluationAnswer(
            evaluation_id=db_evaluation.id,
            aspect_id=aspect_id,
            value_number=ans.get("value_number"),
            value_boolean=ans.get("value_boolean"),
            comment=ans.get("comment"),
        )
        # store the historical computed values in new columns (must be added via alembic)
        setattr(db_answer, "recorded_aspect_max", aspect_max)
        setattr(db_answer, "recorded_points_awarded", awarded)
        setattr(db_answer, "recorded_section_max", section_max)

        session.add(db_answer)

    # Update evaluation totals
    db_evaluation.total_score = float(scoring["total_awarded"])
    db_evaluation.percentage_score = float(scoring["percentage"])

    await session.commit()
    await session.refresh(db_evaluation)

    return db_evaluation


async def update_evaluation(
    session: AsyncSession, evaluation_id: int, evaluation_update: EvaluationUpdate
) -> Evaluation:
    db_evaluation = await get_evaluation(session, evaluation_id)

    # update fields
    evaluation_update.status = getattr(evaluation_update, "status", db_evaluation.status or None) or db_evaluation.status
    evaluation_data = evaluation_update.model_dump(exclude={"evaluation_answers"}, exclude_unset=True)
    db_evaluation.sqlmodel_update(evaluation_data)
    session.add(db_evaluation)
    await session.flush()

    # If evaluation_answers present -> update them
    if evaluation_update.evaluation_answers:
        # Build answers payload for scoring - either existing answers or new
        answers_payload = []
        for ans in evaluation_update.evaluation_answers:
            # update existing answer model
            db_ans = await get_evaluation_answer(session, ans.id)
            # apply updates to db_ans
            upd = ans.model_dump(exclude_unset=True)
            db_ans.sqlmodel_update(upd)
            session.add(db_ans)
            answers_payload.append({
                "aspect_id": db_ans.aspect_id,
                "value_number": db_ans.value_number,
                "value_boolean": db_ans.value_boolean,
                "comment": db_ans.comment,
            })

        # Recalculate scoring
        try:
            scoring = await calculate_evaluation_scores(session, db_evaluation.campaigns_id, answers_payload)
        except ScoringError:
            raise

        # Update recorded fields on answers
        for ans_payload in answers_payload:
            aspect_id = ans_payload["aspect_id"]
            awarded = 0.0
            aspect_max = 0.0
            section_max = 0.0
            for sid, sdata in scoring["sections"].items():
                if aspect_id in sdata["aspects"]:
                    aspdata = sdata["aspects"][aspect_id]
                    awarded = float(aspdata["awarded"])
                    aspect_max = float(aspdata["aspect_max"])
                    section_max = float(sdata["section_max"])
                    break
            # find db answer
            q = select(EvaluationAnswer).where(EvaluationAnswer.evaluation_id == db_evaluation.id, EvaluationAnswer.aspect_id == aspect_id, EvaluationAnswer.deleted_at == None)
            res = await session.execute(q)
            db_ans = res.scalars().first()
            if db_ans:
                setattr(db_ans, "recorded_aspect_max", aspect_max)
                setattr(db_ans, "recorded_points_awarded", awarded)
                setattr(db_ans, "recorded_section_max", section_max)
                session.add(db_ans)

        # Update evaluation totals
        db_evaluation.total_score = float(scoring["total_awarded"])
        db_evaluation.percentage_score = float(scoring["percentage"])

    await session.commit()
    await session.refresh(db_evaluation)
    return db_evaluation
