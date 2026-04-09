from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, select

from app.models.evaluation_event_model import (
    EvaluationEvent,
    EvaluationEventCreate,
    EvaluationHighlightPublic,
    EvaluationHighlightsPublic,
    EvaluationEventTypeEnum,
    EvaluationEventsPublic,
)


def is_undefined_evaluation_events_table_error(exc: BaseException | None) -> bool:
    """True when Postgres reports that relation ``evaluation_events`` is missing."""
    depth = 0
    current: BaseException | None = exc
    while current is not None and depth < 10:
        msg = str(current).lower()
        if "evaluation_events" in msg and "does not exist" in msg:
            return True
        nxt = getattr(current, "__cause__", None)
        if nxt is None and isinstance(current, ProgrammingError):
            nxt = getattr(current, "orig", None)
        current = nxt
        depth += 1
    return False


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
    complaint_intensity_terms = ("pesimo", "horrible", "terrible", "indignado", "furioso")
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
            severity = 4
            if any(term in text for term in complaint_intensity_terms):
                severity = 5
            detected.append(
                EvaluationEventCreate(
                    event_type=EvaluationEventTypeEnum.COMPLAINT,
                    timestamp_seconds=start_time,
                    severity=severity,
                    confidence=confidence if confidence is not None else 0.72,
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
                    confidence=confidence if confidence is not None else 0.68,
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
                    confidence=confidence if confidence is not None else 0.7,
                    evidence_text=seg.get("text", "")[:500],
                    source="heuristic",
                )
            )

    return dedupe_nearby_events(detected, time_window_seconds=8.0)


def dedupe_nearby_events(
    events: list[EvaluationEventCreate], time_window_seconds: float = 8.0
) -> list[EvaluationEventCreate]:
    if not events:
        return []

    sorted_events = sorted(events, key=lambda e: (e.event_type.value, e.timestamp_seconds))
    deduped: list[EvaluationEventCreate] = []

    for event in sorted_events:
        if not deduped:
            deduped.append(event)
            continue

        prev = deduped[-1]
        same_type = prev.event_type == event.event_type
        close_in_time = abs(prev.timestamp_seconds - event.timestamp_seconds) <= time_window_seconds

        if same_type and close_in_time:
            # Keep strongest event; merge evidence if useful.
            if event.severity > prev.severity:
                prev.severity = event.severity
                prev.timestamp_seconds = event.timestamp_seconds
            prev.confidence = max(prev.confidence or 0.0, event.confidence or 0.0)
            if event.evidence_text and prev.evidence_text != event.evidence_text:
                prev.evidence_text = f"{(prev.evidence_text or '')} | {event.evidence_text}"[:500]
            continue

        deduped.append(event)

    return deduped


async def get_evaluation_highlights(
    session: AsyncSession,
    evaluation_id: int,
    max_items: int = 20,
    pad_seconds: float = 4.0,
) -> EvaluationHighlightsPublic:
    query = (
        select(EvaluationEvent)
        .where(EvaluationEvent.evaluation_id == evaluation_id)
        .order_by(EvaluationEvent.severity.desc(), EvaluationEvent.timestamp_seconds.asc())
        .limit(max_items)
    )
    result = await session.execute(query)
    events = result.scalars().all()

    labels = {
        EvaluationEventTypeEnum.COMPLAINT: "Complaint peak",
        EvaluationEventTypeEnum.EMOTIONAL_PEAK: "Emotional peak",
        EvaluationEventTypeEnum.SALES_SIGNAL: "Sales opportunity",
        EvaluationEventTypeEnum.OBJECTION: "Customer objection",
        EvaluationEventTypeEnum.RESOLUTION: "Resolution moment",
        EvaluationEventTypeEnum.COMPLIANCE_RISK: "Compliance risk",
        EvaluationEventTypeEnum.OTHER: "Relevant moment",
    }

    highlights = [
        EvaluationHighlightPublic(
            event_id=e.id,
            event_type=e.event_type,
            label=labels.get(e.event_type, "Relevant moment"),
            start_seconds=max(0.0, e.timestamp_seconds - pad_seconds),
            end_seconds=e.timestamp_seconds + pad_seconds,
            severity=e.severity,
            confidence=e.confidence,
            evidence_text=e.evidence_text,
        )
        for e in events
    ]
    return EvaluationHighlightsPublic(data=highlights, total=len(highlights))
