"""Tests ensamblaje Study Intelligence (sin DB)."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.field_instrument_revision_model import FieldInstrumentRevisionPublic
from app.services.field_instrument_revision_services import DEFAULT_INSTRUMENT_SPEC_STUB
from app.services.instrument_qa_rules_v1 import run_instrument_qa_rules_bootstrap
from app.study_intelligence.journey_heuristics import phase_index_for_block_title
from app.study_intelligence.pipeline import (
    STUDY_INTELLIGENCE_ENGINE_VERSION,
    assemble_study_intelligence_bundle,
    bundle_to_public,
)


def _revision_stub(**kwargs: object) -> FieldInstrumentRevisionPublic:
    now = datetime.now(timezone.utc)
    base = dict(
        id=1,
        study_id=10,
        company_id=5,
        revision_label="v1",
        status="draft",
        content_hash="content_hash_stub",
        brief_snapshot_hash="brief_hash_stub",
        framework_catalog_version="2026.1",
        created_at=now,
        updated_at=now,
        framework_template_id=None,
        notes=None,
        title=None,
        instrument_spec_version_declared=None,
        last_ruleset_version=None,
        last_validation_at=None,
        last_validation_ok=None,
        last_validation_issue_count=None,
        last_validation_content_hash=None,
        created_by_user_id=None,
        updated_by_user_id=None,
    )
    base.update(kwargs)
    return FieldInstrumentRevisionPublic.model_validate(base)


def test_phase_index_intro_keyword():
    assert phase_index_for_block_title("Introducción y contexto") == 0
    assert phase_index_for_block_title("Screening de elegibilidad") == 1


def test_assemble_bundle_has_six_phases_and_engine_version():
    spec = dict(DEFAULT_INSTRUMENT_SPEC_STUB)
    findings = run_instrument_qa_rules_bootstrap(spec)
    rev = _revision_stub()
    bundle = assemble_study_intelligence_bundle(
        revision_pub=rev,
        spec=spec,
        brief_payload={},
        qa_findings=findings,
        readiness_blocking_codes=(),
    )
    assert bundle.participant_journey is not None
    assert len(bundle.participant_journey.phases) == 6

    pub = bundle_to_public(bundle)
    assert pub.engine_version == STUDY_INTELLIGENCE_ENGINE_VERSION
    assert STUDY_INTELLIGENCE_ENGINE_VERSION in pub.ruleset_versions
    assert isinstance(pub.contextual_scores.get("item_count"), int)


def test_heavy_survey_adds_fatigue_signal():
    blocks = []
    for i in range(10):
        blocks.append(
            {
                "block_id": f"B{i:02d}",
                "title": f"Bloque experiencia {i}",
                "items": [{"item_id": f"Q{i}", "text": "¿Qué tal?"}],
            }
        )
    spec = {
        "instrument_spec_version": "2026.1-draft",
        "title": "Largo",
        "blocks": blocks,
    }
    findings = run_instrument_qa_rules_bootstrap(spec)
    rev = _revision_stub()
    bundle = assemble_study_intelligence_bundle(
        revision_pub=rev,
        spec=spec,
        brief_payload={"notes": "fricción en onboarding"},
        qa_findings=findings,
        readiness_blocking_codes=("qa_run_missing",),
    )
    codes = {r.code for r in bundle.operational_risks}
    assert any(c.startswith("readiness_") for c in codes)
    fatigue_codes = {f.code for f in bundle.fatigue_risks}
    assert "BLOCK_COUNT_HIGH" in fatigue_codes
