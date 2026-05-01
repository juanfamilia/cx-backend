"""7Field — modelo canónico de ejecución: encuestas bajo proyecto + KPIs materializados."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import ConfigDict
from sqlalchemy import Column, DateTime, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class FieldSurvey(SQLModel, table=True):
    """
    Encuesta Field (no replica Dooblo): vínculo estable external_survey_id + metadatos editables.
    """

    __tablename__ = "field_surveys"
    __table_args__ = (
        UniqueConstraint("field_project_id", "external_survey_id", name="uq_field_survey_project_external"),
    )

    id: int | None = Field(default=None, primary_key=True)
    field_project_id: int = Field(foreign_key="field_projects.id", index=True)
    company_id: int = Field(foreign_key="companies.id", index=True)

    external_survey_id: str = Field(max_length=255, index=True)
    name: str | None = Field(default=None, max_length=500)
    mode: str | None = Field(default=None, max_length=32, description="CAPI | CATI | CAWI")
    status: str = Field(default="active", max_length=32, description="active | closed")

    survey_metadata: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column("survey_metadata", JSONB, nullable=True),
    )

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now())
    )


class FieldMetric(SQLModel, table=True):
    """Serie temporal de KPIs por proyecto (Clever consume agregados, no entrevistas crudas)."""

    __tablename__ = "field_metrics"

    id: int | None = Field(default=None, primary_key=True)
    field_project_id: int = Field(foreign_key="field_projects.id", index=True)
    metric_code: str = Field(max_length=64, index=True)
    value: float = Field(description="Valor normalizado del KPI en el instante calculated_at.")
    calculated_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now(), index=True))

    dimensions: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Opcional: survey_id, wave, etc.",
    )


class FieldSurveyPublic(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    field_project_id: int
    company_id: int
    external_survey_id: str
    name: str | None
    mode: str | None
    status: str
    survey_metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class FieldMetricPublic(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    field_project_id: int
    metric_code: str
    value: float
    calculated_at: datetime
    dimensions: dict[str, Any] | None = None


class FieldProjectSyncResponse(SQLModel):
    """Respuesta síncrona del stub de sync (partial success explícito)."""

    field_project_id: int
    surveys_upserted: int
    metrics_emitted: list[str]
    partial_errors: list[dict[str, Any]]
