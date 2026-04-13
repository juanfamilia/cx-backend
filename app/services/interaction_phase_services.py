"""
Interaction Phase Services

Extrae y persiste las fases de negocio de una interacción
(ENTRY → ATTENTION → CLOSURE, etc.) como EvaluationEvents especiales,
permitiendo navegación por momentos en el reproductor del frontend.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.evaluation_event_model import (
    EvaluationEvent,
    EvaluationEventCreate,
    EvaluationEventTypeEnum,
    EvaluationHighlightPublic,
    EvaluationHighlightsPublic,
)
from app.services.evaluation_event_services import (
    create_events_batch,
    delete_events_for_evaluation,
)

logger = logging.getLogger(__name__)

PHASE_SOURCE = "interaction_phase"

# Mapeo phase → EventType para reutilizar el modelo existente
_PHASE_TO_EVENT: Dict[str, EvaluationEventTypeEnum] = {
    "ENTRY":       EvaluationEventTypeEnum.OTHER,
    "ATTENTION":   EvaluationEventTypeEnum.OTHER,
    "CLOSURE":     EvaluationEventTypeEnum.OTHER,
    "WAITING":     EvaluationEventTypeEnum.COMPLAINT,
    "ESCALATION":  EvaluationEventTypeEnum.RESOLUTION,
    "OTHER":       EvaluationEventTypeEnum.OTHER,
}


class InteractionPhase(BaseModel):
    phase: str
    label: str
    start_seconds: float
    end_seconds: float
    summary: Optional[str] = None


class InteractionPhasesPublic(BaseModel):
    evaluation_id: int
    phases: List[InteractionPhase]
    total_duration: float


def _extract_phases_from_json(operative_view: str) -> List[Dict[str, Any]]:
    """
    Extrae el array interaction_phases del JSON operativo.
    Tolerante a bloques markdown y JSON parcialmente malformado.
    """
    try:
        match = re.search(r"```json\s*(.*?)\s*```", operative_view, re.DOTALL)
        json_str = match.group(1) if match else operative_view
        data = json.loads(json_str)
        return data.get("interaction_phases", [])
    except Exception as exc:
        logger.warning("Could not extract interaction_phases from operative_view: %s", exc)
        return []


async def persist_interaction_phases(
    session: AsyncSession,
    evaluation_id: int,
    operative_view: str,
) -> List[EvaluationEvent]:
    """
    Parsea las fases del JSON operativo y las persiste como EvaluationEvents
    con source='interaction_phase' para diferenciarlas de otros eventos.
    Elimina fases previas antes de re-persistir (idempotente).
    """
    raw_phases = _extract_phases_from_json(operative_view)
    if not raw_phases:
        logger.info("No interaction_phases found for evaluation_id=%s", evaluation_id)
        return []

    # Borrar fases previas de esta evaluación (guard: tabla puede no existir en BD antigua)
    from sqlmodel import delete
    from sqlalchemy import text as sa_text
    try:
        tbl_exists = await session.scalar(
            sa_text("SELECT to_regclass('public.evaluation_events')")
        )
        if not tbl_exists:
            logger.warning("evaluation_events table missing; skipping persist_interaction_phases evaluation_id=%s", evaluation_id)
            return []
        stmt = (
            delete(EvaluationEvent)
            .where(
                EvaluationEvent.evaluation_id == evaluation_id,
                EvaluationEvent.source == PHASE_SOURCE,
            )
        )
        await session.execute(stmt)
        await session.commit()
    except Exception as exc:
        logger.error("persist_interaction_phases delete failed evaluation_id=%s: %s", evaluation_id, exc)
        await session.rollback()
        return []

    events: List[EvaluationEventCreate] = []
    for p in raw_phases:
        phase_key = str(p.get("phase", "OTHER")).upper()
        event_type = _PHASE_TO_EVENT.get(phase_key, EvaluationEventTypeEnum.OTHER)
        label = p.get("label", phase_key)
        summary = p.get("summary", "")
        start = float(p.get("start_seconds", 0))

        events.append(
            EvaluationEventCreate(
                event_type=event_type,
                timestamp_seconds=start,
                severity=1,
                confidence=1.0,
                evidence_text=f"[{phase_key}] {label}: {summary}",
                source=PHASE_SOURCE,
            )
        )

    saved = await create_events_batch(session, evaluation_id, events)
    logger.info(
        "Interaction phases persisted evaluation_id=%s count=%s",
        evaluation_id,
        len(saved),
    )
    return saved


async def get_interaction_phases(
    session: AsyncSession,
    evaluation_id: int,
) -> InteractionPhasesPublic:
    """
    Devuelve las fases de negocio persistidas para una evaluación,
    reconstruidas desde los EvaluationEvents con source='interaction_phase'.
    """
    q = (
        select(EvaluationEvent)
        .where(
            EvaluationEvent.evaluation_id == evaluation_id,
            EvaluationEvent.source == PHASE_SOURCE,
        )
        .order_by(EvaluationEvent.timestamp_seconds.asc())
    )
    rows = (await session.execute(q)).scalars().all()

    phases: List[InteractionPhase] = []
    for i, ev in enumerate(rows):
        # Extraer metadatos del evidence_text: "[PHASE_KEY] Label: Summary"
        text = ev.evidence_text or ""
        phase_key = "OTHER"
        label = text
        summary = ""
        bracket = re.match(r"\[([A-Z_]+)\]\s*(.*?):\s*(.*)", text, re.DOTALL)
        if bracket:
            phase_key = bracket.group(1)
            label = bracket.group(2).strip()
            summary = bracket.group(3).strip()

        # end_seconds = inicio del siguiente evento o timestamp propio + estimado
        next_start = rows[i + 1].timestamp_seconds if i + 1 < len(rows) else ev.timestamp_seconds + 60

        phases.append(
            InteractionPhase(
                phase=phase_key,
                label=label,
                start_seconds=ev.timestamp_seconds,
                end_seconds=next_start,
                summary=summary,
            )
        )

    total_duration = phases[-1].end_seconds if phases else 0.0

    return InteractionPhasesPublic(
        evaluation_id=evaluation_id,
        phases=phases,
        total_duration=total_duration,
    )
