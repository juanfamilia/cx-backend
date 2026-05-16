"""Upsert de snapshots journey persistidos (P2)."""

from __future__ import annotations

from sqlalchemy import delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.field_instrument_qa_run_model import FieldInstrumentQARun
from app.models.field_instrument_revision_model import FieldInstrumentRevisionPublic
from app.models.field_participant_journey_model import FieldJourneyPhase, FieldParticipantJourney
from app.study_intelligence.constants import STUDY_INTELLIGENCE_ENGINE_VERSION
from app.study_intelligence.contracts import StudyIntelligenceBundle
from app.study_intelligence.schemas import bundle_to_public


async def upsert_participant_journey_snapshot(
    session: AsyncSession,
    *,
    revision_pub: FieldInstrumentRevisionPublic,
    bundle: StudyIntelligenceBundle,
) -> int | None:
    """Guarda journey + fases para (revision_id, content_hash). Devuelve id de fila o None."""
    pj = bundle.participant_journey
    if pj is None:
        return None

    content_hash = (pj.instrument_spec_content_hash or revision_pub.content_hash or "").strip()

    stmt = select(FieldParticipantJourney).where(
        FieldParticipantJourney.revision_id == revision_pub.id,
        FieldParticipantJourney.instrument_spec_content_hash == content_hash,
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()

    qa_stmt = (
        select(FieldInstrumentQARun)
        .where(
            FieldInstrumentQARun.revision_id == revision_pub.id,
            FieldInstrumentQARun.company_id == revision_pub.company_id,
        )
        .order_by(desc(FieldInstrumentQARun.created_at))
        .limit(1)
    )
    qa_run = (await session.execute(qa_stmt)).scalar_one_or_none()
    qa_run_id = qa_run.id if qa_run is not None else None

    if existing is not None:
        await session.execute(
            delete(FieldJourneyPhase).where(
                FieldJourneyPhase.participant_journey_id == existing.id,
            )
        )
        row = existing
        row.study_id = revision_pub.study_id
        row.company_id = revision_pub.company_id
        row.brief_snapshot_hash = pj.brief_snapshot_hash
        row.framework_catalog_version = pj.framework_catalog_version
        row.engine_version = STUDY_INTELLIGENCE_ENGINE_VERSION
        row.ruleset_versions_json = list(bundle.ruleset_versions)
        row.contextual_scores_json = dict(bundle.contextual_scores)
        row.field_instrument_qa_run_id = qa_run_id
        session.add(row)
        await session.flush()
        journey_id = row.id
    else:
        row = FieldParticipantJourney(
            revision_id=revision_pub.id,
            company_id=revision_pub.company_id,
            study_id=revision_pub.study_id,
            instrument_spec_content_hash=content_hash,
            brief_snapshot_hash=pj.brief_snapshot_hash,
            framework_catalog_version=pj.framework_catalog_version,
            engine_version=STUDY_INTELLIGENCE_ENGINE_VERSION,
            ruleset_versions_json=list(bundle.ruleset_versions),
            contextual_scores_json=dict(bundle.contextual_scores),
            field_instrument_qa_run_id=qa_run_id,
        )
        session.add(row)
        await session.flush()
        journey_id = row.id

    assert journey_id is not None
    snap = bundle_to_public(bundle, participant_journey_snapshot_id=journey_id)
    row.bundle_snapshot_json = snap.model_dump(mode="json")
    session.add(row)

    for ph in pj.phases:
        session.add(
            FieldJourneyPhase(
                participant_journey_id=journey_id,
                phase_key=ph.phase_key,
                order_index=ph.order_index,
                title=ph.title,
                narrative_summary=ph.narrative_summary,
                block_ids_json=list(ph.block_ids),
                experience_arc_key=ph.experience_arc_key or "",
                experience_arc_title=ph.experience_arc_title or "",
            )
        )

    await session.commit()
    return journey_id
