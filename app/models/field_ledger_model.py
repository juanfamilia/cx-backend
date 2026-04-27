"""Field — Execution Ledger (B): filas de import, hallazgos QC, eventos auditables."""

from datetime import datetime
from typing import Any, Optional

from pydantic import ConfigDict
from sqlalchemy import Column, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class FieldImportRow(SQLModel, table=True):
    __tablename__ = "field_import_rows"

    id: int | None = Field(default=None, primary_key=True)
    field_project_id: int = Field(foreign_key="field_projects.id", index=True)
    field_import_run_id: int = Field(foreign_key="field_import_runs.id", index=True)
    source_row_number: int = Field(description="Número de línea de datos en el CSV (1 = primera fila tras cabeceras).")
    case_id: str = Field(max_length=500, index=True)
    wave_id: str = Field(max_length=500, index=True)
    interviewer_id: str = Field(max_length=500)
    disposition: str = Field(max_length=255)
    started_at_text: str | None = Field(default=None, max_length=500)
    completed_at_text: str | None = Field(default=None, max_length=500)
    duration_sec: int | None = Field(default=None)
    extras: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))


class FieldFindingDecisionLog(SQLModel, table=True):
    """
    Historial de decisiones operativas sobre un hallazgo (auditoría).
    Alineado al contrato mínimo de plataforma: quién, cuándo, de qué estado a cuál, con nota opcional.
    """

    __tablename__ = "field_finding_decision_logs"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    field_project_id: int = Field(foreign_key="field_projects.id", index=True)
    field_finding_id: int = Field(foreign_key="field_findings.id", index=True)
    actor_user_id: int = Field(foreign_key="users.id", index=True)
    from_status: str | None = Field(default=None, max_length=32, description="approval_status previo (o null).")
    to_status: str = Field(max_length=32, description="approved | rejected | pending")
    note: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))


class FieldFinding(SQLModel, table=True):
    __tablename__ = "field_findings"

    id: int | None = Field(default=None, primary_key=True)
    field_project_id: int = Field(foreign_key="field_projects.id", index=True)
    # Nullable cuando el hallazgo proviene de la capa de decisión (Dooblo) sin import CSV.
    field_import_run_id: int | None = Field(
        default=None,
        foreign_key="field_import_runs.id",
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
    field_import_row_id: int | None = Field(
        default=None,
        foreign_key="field_import_rows.id",
        index=True,
    )
    idempotency_key: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    # Origen: csv, dooblo_analysis, …
    source: str | None = Field(default=None, max_length=32, index=True)
    code: str = Field(max_length=64, index=True)
    severity: str = Field(max_length=16, description="info | warn | error")
    case_id: str | None = Field(default=None, max_length=500, index=True)
    wave_id: str | None = Field(default=None, max_length=500)
    message: str = Field(sa_column=Column(Text, nullable=False))
    explanation: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    recommendation: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    evidence: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    # pending | approved | rejected | None (legado o sin flujo)
    approval_status: str | None = Field(default=None, max_length=32, index=True)
    reviewed_by_user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    reviewed_at: datetime | None = Field(default=None)

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))


class FieldLedgerEvent(SQLModel, table=True):
    __tablename__ = "field_ledger_events"

    id: int | None = Field(default=None, primary_key=True)
    field_project_id: int = Field(foreign_key="field_projects.id", index=True)
    field_import_run_id: int | None = Field(
        default=None,
        foreign_key="field_import_runs.id",
        index=True,
    )
    actor_user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    event_type: str = Field(max_length=64, index=True)
    payload: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))


class FieldImportRowPublic(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    field_project_id: int
    field_import_run_id: int
    source_row_number: int
    case_id: str
    wave_id: str
    interviewer_id: str
    disposition: str
    started_at_text: str | None
    completed_at_text: str | None
    duration_sec: int | None
    extras: Optional[dict[str, Any]]
    created_at: datetime


class FieldFindingPublic(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    field_project_id: int
    field_import_run_id: int | None
    field_sync_run_id: int | None
    field_policy_set_id: int | None
    field_import_row_id: int | None
    idempotency_key: str | None
    source: str | None
    code: str
    severity: str
    case_id: str | None
    wave_id: str | None
    message: str
    explanation: str | None
    recommendation: str | None
    evidence: Optional[dict[str, Any]]
    approval_status: str | None
    reviewed_by_user_id: int | None
    reviewed_at: datetime | None
    created_at: datetime


class FieldLedgerEventPublic(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    field_project_id: int
    field_import_run_id: int | None
    actor_user_id: int | None
    event_type: str
    payload: Optional[dict[str, Any]]
    created_at: datetime


class FieldFindingDecisionLogPublic(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    field_project_id: int
    field_finding_id: int
    actor_user_id: int
    from_status: str | None
    to_status: str
    note: str | None
    created_at: datetime
    actor_display: str | None = Field(
        default=None, description="Nombre + apellido o email del actor (rellenado en API)."
    )
