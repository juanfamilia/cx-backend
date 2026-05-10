"""7Field — revisiones de instrumento (`instrument_spec`) ligadas a FieldStudy."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field as PydanticField, field_validator
from sqlalchemy import Column, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class FieldInstrumentRevisionBase(SQLModel):
    revision_label: str = Field(max_length=64)
    status: str = Field(
        default="draft",
        max_length=32,
        description="draft | approved | archived — approved tras Readiness completo.",
    )
    framework_template_id: str | None = Field(default=None, max_length=128)
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    title: str | None = Field(default=None, max_length=500)
    instrument_spec_version_declared: str | None = Field(default=None, max_length=64)


class FieldInstrumentRevision(FieldInstrumentRevisionBase, table=True):
    __tablename__ = "field_instrument_revisions"

    id: int | None = Field(default=None, primary_key=True)
    study_id: int = Field(foreign_key="field_studies.id", index=True)
    company_id: int = Field(foreign_key="companies.id", index=True)

    spec_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
    )
    content_hash: str = Field(default="", max_length=128)

    last_validation_at: datetime | None = Field(default=None)
    last_validation_ok: bool | None = Field(default=None)
    last_validation_issue_count: int | None = Field(default=None)
    last_validation_content_hash: str | None = Field(default=None, max_length=128)

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)
    created_by_user_id: int | None = Field(default=None, foreign_key="users.id")
    updated_by_user_id: int | None = Field(default=None, foreign_key="users.id")


class FieldInstrumentRevisionCreate(SQLModel):
    """Crear borrador: spec opcional (si falta, plantilla mínima válida por schema)."""

    spec: dict[str, Any] | None = PydanticField(
        default=None,
        description="Raíz `instrument_spec`; debe cumplir schema cuando se envía.",
    )
    revision_label: str | None = PydanticField(
        default=None,
        max_length=64,
        description="Si se omite, se asigna label único por estudio (vN).",
    )
    framework_template_id: str | None = PydanticField(default=None, max_length=128)
    framework_template_slug: str | None = PydanticField(
        default=None,
        max_length=128,
        description="Catálogo `GET /field/framework-templates`; si hay `spec`, este campo solo traza (`framework_template_id`).",
    )
    framework_template_version: str | None = PydanticField(
        default=None,
        max_length=32,
        description="Versión de catálogo (p.ej. `2026.1`); por defecto `2026.1` cuando hay slug.",
    )
    notes: str | None = None

    @field_validator("revision_label", mode="before")
    @classmethod
    def _strip_label(cls, v: object) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator("framework_template_slug", mode="before")
    @classmethod
    def _strip_framework_slug(cls, v: object) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator("framework_template_version", mode="before")
    @classmethod
    def _strip_framework_version(cls, v: object) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None


class FieldInstrumentRevisionPatch(SQLModel):
    """Sustituye el documento completo (sin merge profundo: comportamiento explícito y auditable)."""

    spec: dict[str, Any] | None = None
    revision_label: str | None = PydanticField(default=None, max_length=64)
    framework_template_id: str | None = PydanticField(default=None, max_length=128)
    notes: str | None = None
    status: str | None = PydanticField(
        default=None,
        max_length=32,
        description="Solo transición draft → archived.",
    )

    @field_validator("revision_label", mode="before")
    @classmethod
    def _strip_label(cls, v: object) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None


class FieldInstrumentRevisionPublic(FieldInstrumentRevisionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    study_id: int
    company_id: int
    content_hash: str
    last_validation_at: datetime | None = None
    last_validation_ok: bool | None = None
    last_validation_issue_count: int | None = None
    last_validation_content_hash: str | None = None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: int | None = None
    updated_by_user_id: int | None = None


class FieldInstrumentRevisionWithSpec(FieldInstrumentRevisionPublic):
    """Detalle API: metadatos + `instrument_spec` completo."""

    spec: dict[str, Any]


class InstrumentSpecSchemaIssue(SQLModel):
    path: str
    message: str


class InstrumentSpecValidationReport(SQLModel):
    """Resultado de validación contra JSON Schema oficial (PRE-FIELD)."""

    ok: bool
    instrument_spec_version: str | None = None
    content_hash: str
    schema_issues: list[InstrumentSpecSchemaIssue]
    schema_resource: str = PydanticField(
        default="examples/instrument_spec_v1.schema.json",
        description="Referencia de auditoría (ruta en repo; mismo fichero empaquetado en deploy).",
    )


class InstrumentSpecValidateBody(SQLModel):
    spec: dict[str, Any]


class FieldInstrumentRevisionValidateResponse(SQLModel):
    revision: FieldInstrumentRevisionPublic
    report: InstrumentSpecValidationReport
