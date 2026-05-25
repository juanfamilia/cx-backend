"""Banda consultiva PRE-FIELD (brief) — sin cliente."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.field_study_brief_model import FieldBriefConsultHintPublic, FieldStudyBriefPublic
from app.services.field_study_brief_surface_intel import brief_density_band_from_score, enrich_field_study_brief_public


def _brief_pub(*, completeness: float | None, state: str) -> FieldStudyBriefPublic:
    return FieldStudyBriefPublic(
        study_id=1,
        company_id=2,
        payload_json={},
        completeness_score=completeness,
        approval_state=state,
        body_hash="x",
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )


def test_brief_density_band_from_score_bins() -> None:
    assert brief_density_band_from_score(None) == "unknown"
    assert brief_density_band_from_score(54.9) == "thin"
    assert brief_density_band_from_score(55.0) == "adequate"
    assert brief_density_band_from_score(79.9) == "adequate"
    assert brief_density_band_from_score(80.0) == "rich"


def test_enrich_emits_density_hint_only_for_draft_thin() -> None:
    enriched = enrich_field_study_brief_public(_brief_pub(completeness=40, state="draft"))
    assert enriched.brief_density_band == "thin"
    assert enriched.consultive_hints
    assert enriched.consultive_hints[0].id == "ins-brief-density-thin"
    assert enriched.consultive_hints[0].tone == "warn"

    no_hint = enrich_field_study_brief_public(_brief_pub(completeness=40, state="approved_internal"))
    assert no_hint.consultive_hints == []

    no_hint_band = enrich_field_study_brief_public(_brief_pub(completeness=70, state="draft"))
    assert no_hint_band.brief_density_band == "adequate"
    assert no_hint_band.consultive_hints == []
