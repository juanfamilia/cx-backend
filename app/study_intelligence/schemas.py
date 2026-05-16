"""Esquemas HTTP para Study Intelligence (OpenAPI)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.study_intelligence.contracts import InsightPriority


class JourneyPhasePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    phase_key: str
    order_index: int
    title: str
    narrative_summary: str | None = None
    block_ids: list[str] = Field(default_factory=list)


class ParticipantJourneyPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    study_id: int
    instrument_revision_id: int
    brief_snapshot_hash: str | None = None
    instrument_spec_content_hash: str | None = None
    framework_catalog_version: str | None = None
    phases: list[JourneyPhasePublic] = Field(default_factory=list)


class OperationalRiskPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    message_human: str
    severity: str
    linked_block_id: str | None = None
    linked_item_id: str | None = None
    source_rule_id: str | None = None


class MethodologicalSignalPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    message_human: str
    severity: str
    linked_block_id: str | None = None
    framework_rule_ref: str | None = None


class FatigueRiskPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    message_human: str
    level: str
    linked_block_id: str | None = None


class SensitivityAreaPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    label_human: str
    rationale_human: str
    linked_block_ids: list[str] = Field(default_factory=list)


class ExpectedDropoutZonePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    phase_key: str | None = None
    linked_block_id: str | None = None
    message_human: str
    confidence: str | None = None


class InsightCardPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    insight_id: str
    headline: str
    body: str
    priority: InsightPriority
    tone: str = "observe"
    trace_rule_ids: list[str] = Field(default_factory=list)
    trace_heuristic_ids: list[str] = Field(default_factory=list)


class StudyIntelligenceBundlePublic(BaseModel):
    """Salida motor — mismo layout que `StudyIntelligenceBundle` + versiones."""

    engine_version: str
    ruleset_versions: list[str]

    participant_journey: ParticipantJourneyPublic | None = None
    operational_risks: list[OperationalRiskPublic] = Field(default_factory=list)
    methodological_signals: list[MethodologicalSignalPublic] = Field(default_factory=list)
    fatigue_risks: list[FatigueRiskPublic] = Field(default_factory=list)
    sensitivity_areas: list[SensitivityAreaPublic] = Field(default_factory=list)
    expected_dropout_zones: list[ExpectedDropoutZonePublic] = Field(default_factory=list)
    insight_cards: list[InsightCardPublic] = Field(default_factory=list)
    contextual_scores: dict[str, Any] = Field(default_factory=dict)
