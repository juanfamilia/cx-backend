"""Upsert de snapshots journey persistidos (P2)."""

from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.field_instrument_revision_model import FieldInstrumentRevisionPublic
from app.models.field_participant_journey_model import FieldJourneyPhase, FieldParticipantJourney
from app.study_intelligence.contracts import StudyIntelligenceBundle
from app.study_intelligence.constants import STUDY_INTELLIGENCE_ENGINE_VERSION


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
        )
        session.add(row)
        await session.flush()
        journey_id = row.id

    assert journey_id is not None
    for ph in pj.phases:
        session.add(
            FieldJourneyPhase(
                participant_journey_id=journey_id,
                phase_key=ph.phase_key,
                order_index=ph.order_index,
                title=ph.title,
                narrative_summary=ph.narrative_summary,
                block_ids_json=list(ph.block_ids),
            )
        )

    await session.commit()
    return journey_id
