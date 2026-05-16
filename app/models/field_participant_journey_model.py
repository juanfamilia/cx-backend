"""Persistencia PRE-FIELD — snapshots de `participant_journey` por revisión (Study Intelligence P2)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class FieldParticipantJourney(SQLModel, table=True):
    """Una fila por par (revisión, hash de spec) — último análisis guardado para ese snapshot."""

    __tablename__ = "field_participant_journeys"
    __table_args__ = (
        UniqueConstraint(
            "revision_id",
            "instrument_spec_content_hash",
            name="uq_field_pj_revision_spec_hash",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    revision_id: int = Field(foreign_key="field_instrument_revisions.id", index=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    study_id: int = Field(foreign_key="field_studies.id", index=True)

    instrument_spec_content_hash: str = Field(default="", max_length=128)
    brief_snapshot_hash: str | None = Field(default=None, max_length=128)
    framework_catalog_version: str | None = Field(default=None, max_length=32)
    engine_version: str = Field(max_length=64)
    ruleset_versions_json: list[Any] = Field(sa_column=Column(JSONB, nullable=False))
    contextual_scores_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
    )

    bundle_snapshot_json: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Último `StudyIntelligenceBundlePublic` serializado (insights, señales, journey).",
    )
    field_instrument_qa_run_id: int | None = Field(
        default=None,
        foreign_key="field_instrument_qa_runs.id",
        index=True,
        description="Corrida Auto QA más reciente para la revisión al persistir (referencia blanda).",
    )

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now())
    )


class FieldJourneyPhase(SQLModel, table=True):
    """Fase normalizada ligada a `field_participant_journeys`."""

    __tablename__ = "field_journey_phases"

    id: Optional[int] = Field(default=None, primary_key=True)
    participant_journey_id: int = Field(
        foreign_key="field_participant_journeys.id",
        index=True,
    )
    phase_key: str = Field(max_length=64)
    order_index: int = Field(default=0)
    title: str = Field(max_length=500)
    narrative_summary: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    block_ids_json: list[Any] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )
    experience_arc_key: str = Field(default="", max_length=64)
    experience_arc_title: str = Field(default="", max_length=128)
