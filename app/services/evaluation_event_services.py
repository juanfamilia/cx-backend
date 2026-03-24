from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, select

from app.models.evaluation_event_model import (
    EvaluationEvent,
    EvaluationEventCreate,
    EvaluationEventTypeEnum,
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


async def delete_events_for_evaluation(session: AsyncSession, evaluation_id: int) -> int:
    stmt = delete(EvaluationEvent).where(EvaluationEvent.evaluation_id == evaluation_id)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount


async def create_events_batch(
    session: AsyncSession,
    evaluation_id: int,
    events: list[EvaluationEventCreate],
) -> list[EvaluationEvent]:
    if not events:
        return []

    db_events: list[EvaluationEvent] = []
    for payload in events:
        event = EvaluationEvent(evaluation_id=evaluation_id, **payload.model_dump())
        session.add(event)
        db_events.append(event)

    await session.commit()
    for event in db_events:
        await session.refresh(event)
    return db_events


def detect_events_from_segments(segments: list[dict]) -> list[EvaluationEventCreate]:
    detected: list[EvaluationEventCreate] = []

    complaint_terms = ("queja", "molesto", "mal servicio", "reclamo", "no funciona")
    sales_terms = ("oferta", "plan", "promocion", "descuento", "producto")
    objection_terms = ("caro", "no me interesa", "luego", "no puedo", "no quiero")

    for seg in segments:
        text = seg.get("text", "").strip().lower()
        if not text:
            continue

        start_time = float(seg.get("start", 0.0))
        confidence = None
        if seg.get("avg_logprob") is not None:
            import math

            confidence = max(0.0, min(1.0, math.exp(seg["avg_logprob"])))

        if any(term in text for term in complaint_terms):
            detected.append(
                EvaluationEventCreate(
                    event_type=EvaluationEventTypeEnum.COMPLAINT,
                    timestamp_seconds=start_time,
                    severity=4,
                    confidence=confidence,
                    evidence_text=seg.get("text", "")[:500],
                    source="heuristic",
                )
            )

        if any(term in text for term in sales_terms):
            detected.append(
                EvaluationEventCreate(
                    event_type=EvaluationEventTypeEnum.SALES_SIGNAL,
                    timestamp_seconds=start_time,
                    severity=3,
                    confidence=confidence,
                    evidence_text=seg.get("text", "")[:500],
                    source="heuristic",
                )
            )

        if any(term in text for term in objection_terms):
            detected.append(
                EvaluationEventCreate(
                    event_type=EvaluationEventTypeEnum.OBJECTION,
                    timestamp_seconds=start_time,
                    severity=3,
                    confidence=confidence,
                    evidence_text=seg.get("text", "")[:500],
                    source="heuristic",
                )
            )

    return detected
