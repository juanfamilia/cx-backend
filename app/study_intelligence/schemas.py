"""Esquemas HTTP para Study Intelligence (OpenAPI)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.study_intelligence.constants import STUDY_INTELLIGENCE_ENGINE_VERSION
from app.study_intelligence.contracts import InsightPriority, StudyIntelligenceBundle


class JourneyPhasePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    phase_key: str
    order_index: int
    title: str
    narrative_summary: str | None = None
    block_ids: list[str] = Field(default_factory=list)
    experience_arc_key: str | None = None
    experience_arc_title: str | None = None


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

    participant_journey_snapshot_id: int | None = None
    participant_journey: ParticipantJourneyPublic | None = None
    operational_risks: list[OperationalRiskPublic] = Field(default_factory=list)
    methodological_signals: list[MethodologicalSignalPublic] = Field(default_factory=list)
    fatigue_risks: list[FatigueRiskPublic] = Field(default_factory=list)
    sensitivity_areas: list[SensitivityAreaPublic] = Field(default_factory=list)
    expected_dropout_zones: list[ExpectedDropoutZonePublic] = Field(default_factory=list)
    insight_cards: list[InsightCardPublic] = Field(default_factory=list)
    contextual_scores: dict[str, Any] = Field(default_factory=dict)


def bundle_to_public(
    contract: StudyIntelligenceBundle,
    *,
    participant_journey_snapshot_id: int | None = None,
) -> StudyIntelligenceBundlePublic:
    pj = contract.participant_journey
    pj_pub = None
    if pj is not None:
        pj_pub = ParticipantJourneyPublic(
            study_id=pj.study_id,
            instrument_revision_id=pj.instrument_revision_id,
            brief_snapshot_hash=pj.brief_snapshot_hash,
            instrument_spec_content_hash=pj.instrument_spec_content_hash,
            framework_catalog_version=pj.framework_catalog_version,
            phases=[
                JourneyPhasePublic(
                    phase_key=p.phase_key,
                    order_index=p.order_index,
                    title=p.title,
                    narrative_summary=p.narrative_summary,
                    block_ids=list(p.block_ids),
                    experience_arc_key=(p.experience_arc_key or None),
                    experience_arc_title=(p.experience_arc_title or None),
                )
                for p in pj.phases
            ],
        )

    return StudyIntelligenceBundlePublic(
        engine_version=STUDY_INTELLIGENCE_ENGINE_VERSION,
        ruleset_versions=list(contract.ruleset_versions),
        participant_journey_snapshot_id=participant_journey_snapshot_id,
        participant_journey=pj_pub,
        operational_risks=[
            OperationalRiskPublic(
                code=r.code,
                message_human=r.message_human,
                severity=r.severity,
                linked_block_id=r.linked_block_id,
                linked_item_id=r.linked_item_id,
                source_rule_id=r.source_rule_id,
            )
            for r in contract.operational_risks
        ],
        methodological_signals=[
            MethodologicalSignalPublic(
                code=m.code,
                message_human=m.message_human,
                severity=m.severity,
                linked_block_id=m.linked_block_id,
                framework_rule_ref=m.framework_rule_ref,
            )
            for m in contract.methodological_signals
        ],
        fatigue_risks=[
            FatigueRiskPublic(
                code=f.code,
                message_human=f.message_human,
                level=f.level,
                linked_block_id=f.linked_block_id,
            )
            for f in contract.fatigue_risks
        ],
        sensitivity_areas=[
            SensitivityAreaPublic(
                code=s.code,
                label_human=s.label_human,
                rationale_human=s.rationale_human,
                linked_block_ids=list(s.linked_block_ids),
            )
            for s in contract.sensitivity_areas
        ],
        expected_dropout_zones=[
            ExpectedDropoutZonePublic(
                phase_key=z.phase_key,
                linked_block_id=z.linked_block_id,
                message_human=z.message_human,
                confidence=z.confidence,
            )
            for z in contract.expected_dropout_zones
        ],
        insight_cards=[
            InsightCardPublic(
                insight_id=i.insight_id,
                headline=i.headline,
                body=i.body,
                priority=i.priority,
                tone=i.tone,
                trace_rule_ids=list(i.trace_rule_ids),
                trace_heuristic_ids=list(i.trace_heuristic_ids),
            )
            for i in contract.insight_cards
        ],
        contextual_scores=dict(contract.contextual_scores),
    )
