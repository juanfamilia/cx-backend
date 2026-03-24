from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.evaluation_event_model import (
    EvaluationEvent,
    EvaluationEventCreate,
    EvaluationEventsPublic,
)


async def create_evaluation_event(
    session: AsyncSession, evaluation_id: int, payload: EvaluationEventCreate
) -> EvaluationEvent:
    event = EvaluationEvent(evaluation_id=evaluation_id, **payload.model_dump())
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


async def get_evaluation_events(
    session: AsyncSession, evaluation_id: int
) -> EvaluationEventsPublic:
    query = (
        select(EvaluationEvent)
        .where(EvaluationEvent.evaluation_id == evaluation_id)
        .order_by(EvaluationEvent.timestamp_seconds.asc())
    )
    result = await session.execute(query)
    events = result.scalars().all()
    return EvaluationEventsPublic(data=events, total=len(events))
