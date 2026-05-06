"""
Siete Field — capa de decisión: fuentes externas, políticas versionadas, sync, snapshot.

Principio: ID canónico interno (field_projects) + mapeo explícito a sistemas de origen;
reglas y umbrales versionados; sync técnico separable del análisis/decisión.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import ConfigDict
from sqlalchemy import Column, DateTime, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

# -- Valores lógicos (string en BD; no Enum nativo para menoscabar migraciones) --

SOURCE_TYPE_DOOBLO = "dooblo"
SOURCE_TYPE_QUALTRICS = "qualtrics"
SOURCE_TYPE_CSV = "csv"
SOURCE_TYPE_MANUAL = "manual"
# Hallazgos / snapshot generados por motor de decisión (no solo proxy HTTP).
SOURCE_TYPE_DOOBLO_ANALYSIS = "dooblo_analysis"

SYNC_STRATEGY_FULL = "full"
SYNC_STRATEGY_INCREMENTAL = "incremental"

SYNC_RUN_PENDING = "pending"
SYNC_RUN_PROCESSING = "processing"
SYNC_RUN_COMPLETED = "completed"
SYNC_RUN_FAILED = "failed"

# sync_run_kind: qué fase de pipeline
RUN_KIND_DOOBLO_FETCH = "dooblo_fetch"
RUN_KIND_FIELD_ANALYSIS = "field_analysis"
RUN_KIND_CSV_IMPORT = "csv_import"


class FieldProjectExternalSource(SQLModel, table=True):
    """
    Mapeo canónico proyecto Field ↔ orígenes (Dooblo, CSV, manual, otras APIs).
    Un FieldProject puede tener varias filas (varias encuestas/ondas).
    """

    __tablename__ = "field_project_external_sources"

    id: int | None = Field(default=None, primary_key=True)
    field_project_id: int = Field(foreign_key="field_projects.id", index=True)
    company_id: int = Field(foreign_key="companies.id", index=True, description="Denormalizado para filtro tenant.")

    source_type: str = Field(max_length=32, index=True)  # dooblo, csv, manual, …
    external_project_id: str | None = Field(default=None, max_length=255, index=True)
    external_survey_id: str | None = Field(default=None, max_length=255, index=True)
    external_customer_id: str | None = Field(default=None, max_length=255, index=True)
    wave_id: str | None = Field(default=None, max_length=255, index=True)

    is_active: bool = Field(default=True, index=True)
    sync_strategy: str | None = Field(default=None, max_length=64)  # full | incremental

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now())
    )


class FieldPolicySet(SQLModel, table=True):
    """
    Política/umbrales versionados por proyecto (tolerancias, geofence, etc.).
    Cada análisis debe referenciar field_policy_set_id + version fija.
    """

    __tablename__ = "field_policy_sets"
    __table_args__ = (UniqueConstraint("field_project_id", "version", name="uq_field_policy_project_version"),)

    id: int | None = Field(default=None, primary_key=True)
    field_project_id: int = Field(foreign_key="field_projects.id", index=True)
    version: int = Field(ge=1, index=True, description="Monotónico por proyecto.")
    name: str | None = Field(default=None, max_length=255)
    # JSON: { "quota_max_deviation_pct": 5, "duration": {...}, "geo": {...}, ... }
    config: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB, nullable=False))

    created_by_user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))


class FieldSyncRun(SQLModel, table=True):
    """
    Corrida técnica (fetch, staging, o import) — auditable, idempotente.
    Distingue de FieldImportRun (CSV) y de análisis de decisión (ver run_kind).
    """

    __tablename__ = "field_sync_runs"

    id: int | None = Field(default=None, primary_key=True)
    field_project_id: int = Field(foreign_key="field_projects.id", index=True)
    company_id: int = Field(foreign_key="companies.id", index=True)

    run_kind: str = Field(max_length=64, index=True)  # dooblo_fetch, field_analysis, csv_import, …
    idempotency_key: str = Field(
        max_length=512,
        sa_column=Column(Text, nullable=False, unique=True),
    )

    field_project_external_source_id: int | None = Field(
        default=None,
        foreign_key="field_project_external_sources.id",
        index=True,
    )
    field_import_run_id: int | None = Field(
        default=None,
        foreign_key="field_import_runs.id",
        index=True,
    )
    field_policy_set_id: int | None = Field(
        default=None,
        foreign_key="field_policy_sets.id",
        index=True,
    )

    status: str = Field(max_length=32, index=True)  # pending | processing | completed | failed
    error_summary: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    total_records: int | None = Field(default=None)
    # Columna "meta" en BD; atributo distinto para evitar sombra con metadatos ORM/validación.
    context_payload: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column("meta", JSONB, nullable=True),
    )

    started_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), nullable=True)
    )
    completed_at: datetime | None = Field(default=None)


class FieldOperationalSnapshot(SQLModel, table=True):
    """
    Proyección de estado operativo (cuota, señales GPS, flags) + política con la que se calculó.
    Un registro activo por proyecto (reemplazable in-place) o ajuste único.
    """

    __tablename__ = "field_operational_snapshots"

    id: int | None = Field(default=None, primary_key=True)
    field_project_id: int = Field(
        foreign_key="field_projects.id",
        unique=True,
        index=True,
    )
    field_sync_run_id: int | None = Field(
        default=None,
        foreign_key="field_sync_runs.id",
        index=True,
    )
    field_policy_set_id: int | None = Field(
        default=None,
        foreign_key="field_policy_sets.id",
        index=True,
    )

    quotas_state: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    gps_state: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    route_flags: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    field_status: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))

    last_calculated_at: datetime | None = Field(
        sa_column=Column(
            DateTime,
            server_default=func.now(),
        ),
    )


class FieldPolicySetPublic(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    field_project_id: int
    version: int
    name: str | None
    config: dict[str, Any]
    created_by_user_id: int | None
    created_at: datetime


class FieldProjectExternalSourcePublic(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    field_project_id: int
    company_id: int
    source_type: str
    external_project_id: str | None
    external_survey_id: str | None
    external_customer_id: str | None
    wave_id: str | None
    is_active: bool
    sync_strategy: str | None
    created_at: datetime
    updated_at: datetime


class FieldSyncRunPublic(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    field_project_id: int
    company_id: int
    run_kind: str
    idempotency_key: str
    field_project_external_source_id: int | None
    field_import_run_id: int | None
    field_policy_set_id: int | None
    status: str
    error_summary: str | None
    total_records: int | None
    context_payload: dict[str, Any] | None
    started_at: datetime
    completed_at: datetime | None


class FieldOperationalSnapshotPublic(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    field_project_id: int
    field_sync_run_id: int | None
    field_policy_set_id: int | None
    quotas_state: dict[str, Any] | None
    gps_state: dict[str, Any] | None
    route_flags: dict[str, Any] | None
    field_status: dict[str, Any] | None
    last_calculated_at: datetime | None


# --- Cuerpos de escritura (API) ---


class FieldProjectExternalSourceCreate(SQLModel):
    source_type: str = Field(max_length=32, description="dooblo, csv, manual, …")
    external_project_id: str | None = Field(default=None, max_length=255)
    external_survey_id: str | None = Field(default=None, max_length=255)
    external_customer_id: str | None = Field(default=None, max_length=255)
    wave_id: str | None = Field(default=None, max_length=255)
    is_active: bool = True
    sync_strategy: str | None = Field(
        default=None, max_length=64, description="full | incremental u otros, según operación"
    )


class FieldPolicySetCreate(SQLModel):
    name: str | None = Field(default=None, max_length=255)
    config: dict[str, Any] = Field(default_factory=dict, description="Umbrales y reglas (versión = max+1 en servidor).")


class DoobloAnalysisRequest(SQLModel):
    idempotency_key: str = Field(max_length=512, description="Clave de idempotencia (cliente o servidor, única en sync runs).")
    field_project_external_source_id: int | None = None
    field_policy_set_id: int | None = None


class FieldFindingApprovalBody(SQLModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    status: str = Field(description="approved | rejected | pending (reabrir)")
    note: str | None = Field(
        default=None,
        max_length=8000,
        description="Motivo u operación concreta (auditoría en decision log).",
    )
