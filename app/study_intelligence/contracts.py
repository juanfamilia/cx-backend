"""Typed domain contracts for study intelligence (PRE-FIELD → FIELD).

SQL migrations will mirror these logical entities; runtime uses immutable dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class InsightPriority(str, Enum):
    """Human-facing priority for ordering insight cards and alerts."""

    MUST_ACT = "must_act"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    FYI = "fyi"


@dataclass(frozen=True)
class JourneyPhase:
    """A phase inside a participant journey (logical `journey_phase` row)."""

    phase_key: str
    order_index: int
    title: str
    narrative_summary: str | None
    block_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ParticipantJourney:
    """Logical `participant_journey` — one analyzed snapshot per revision/run."""

    study_id: int
    instrument_revision_id: int
    brief_snapshot_hash: str | None
    instrument_spec_content_hash: str | None
    framework_catalog_version: str | None
    phases: tuple[JourneyPhase, ...] = ()


@dataclass(frozen=True)
class OperationalRisk:
    """Logical `operational_risk`."""

    code: str
    message_human: str
    severity: str
    linked_block_id: str | None = None
    linked_item_id: str | None = None
    source_rule_id: str | None = None


@dataclass(frozen=True)
class MethodologicalSignal:
    """Logical `methodological_signal` — coverage, order, framework gaps."""

    code: str
    message_human: str
    severity: str
    linked_block_id: str | None = None
    framework_rule_ref: str | None = None


@dataclass(frozen=True)
class FatigueRisk:
    """Logical `fatigue_risk`."""

    code: str
    message_human: str
    level: str  # e.g. low | medium | high
    linked_block_id: str | None = None


@dataclass(frozen=True)
class SensitivityArea:
    """Logical `sensitivity_area` — themes needing careful tone or pacing."""

    code: str
    label_human: str
    rationale_human: str
    linked_block_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExpectedDropoutZone:
    """Logical `expected_dropout_zone`."""

    phase_key: str | None
    linked_block_id: str | None
    message_human: str
    confidence: str | None = None  # heuristic | model | blended


@dataclass(frozen=True)
class InsightCard:
    """Single human-facing insight for API/UI (aggregates signals with priority)."""

    insight_id: str
    headline: str
    body: str
    priority: InsightPriority
    tone: str = "observe"  # observe | caution | bright — UI mapping
    trace_rule_ids: tuple[str, ...] = ()
    trace_heuristic_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class StudyIntelligenceBundle:
    """Facade output — one object per revision analysis pass."""

    participant_journey: ParticipantJourney | None
    operational_risks: tuple[OperationalRisk, ...] = ()
    methodological_signals: tuple[MethodologicalSignal, ...] = ()
    fatigue_risks: tuple[FatigueRisk, ...] = ()
    sensitivity_areas: tuple[SensitivityArea, ...] = ()
    expected_dropout_zones: tuple[ExpectedDropoutZone, ...] = ()
    insight_cards: tuple[InsightCard, ...] = ()
    contextual_scores: dict[str, Any] = field(default_factory=dict)
    ruleset_versions: tuple[str, ...] = ()
