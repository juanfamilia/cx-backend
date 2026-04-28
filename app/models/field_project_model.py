"""Siete Field — proyectos de control de levantamiento (CSV / conectores)."""

from datetime import datetime

from pydantic import ConfigDict, field_validator
from sqlalchemy import Column, DateTime, Text, func
from sqlmodel import Field, SQLModel


class FieldProjectBase(SQLModel):
    name: str = Field(max_length=500)
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    import_format_version: str = Field(
        default="2026.1",
        max_length=32,
        description="Versión del layout CSV esperado en importaciones.",
    )
    status: str = Field(
        default="draft",
        max_length=32,
        description="draft | active | archived",
    )
    ingest_mode: str = Field(
        default="csv",
        max_length=32,
        description="Origen principal declarado: csv (archivo) | dooblo (API SurveyToGo).",
    )


class FieldProject(FieldProjectBase, table=True):
    __tablename__ = "field_projects"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    client_id: int = Field(foreign_key="end_clients.id", index=True)
    study_id: int | None = Field(
        default=None,
        foreign_key="field_studies.id",
        index=True,
        description="Estudio canónico Field (opcional durante migración legacy).",
    )

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)


class FieldProjectCreate(SQLModel):
    name: str
    description: str | None = None
    client_id: int = Field(
        description="Cliente final (end_clients); debe existir y pertenecer a la misma empresa que company_id.",
    )
    company_id: int | None = Field(
        default=None,
        description=(
            "Rol 0 sin empresa en el perfil (company_id null en users): obligatorio. "
            "Rol 0 con empresa: opcional (se usa la del usuario). Roles 1–2: omitir."
        ),
    )
    ingest_mode: str = Field(
        default="csv",
        max_length=32,
        description="csv | dooblo — origen de datos que el operador declara al crear el proyecto.",
    )
    study_id: int | None = Field(
        default=None,
        description="field_studies.id (misma empresa; mismo client_id que el estudio).",
    )

    @field_validator("ingest_mode", mode="before")
    @classmethod
    def _normalize_ingest_mode(cls, v: object) -> str:
        if v is None or (isinstance(v, str) and not v.strip()):
            return "csv"
        s = str(v).strip().lower()
        if s not in ("csv", "dooblo"):
            raise ValueError("ingest_mode debe ser csv o dooblo")
        return s


class FieldProjectPublic(FieldProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    client_id: int
    study_id: int | None = None
    created_at: datetime
    updated_at: datetime


class FieldProjectPatch(SQLModel):
    """Actualización parcial (solo campos enviados)."""

    study_id: int | None = Field(
        default=None,
        description="Vincular a field_studies.id o null para quitar vínculo (misma empresa y cliente que el proyecto).",
    )


class FieldImportRunBase(SQLModel):
    status: str = Field(max_length=32)  # pending | processing | completed | failed
    format_version: str = Field(max_length=32)
    error_detail: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    row_count: int | None = Field(default=None)


class FieldImportRun(FieldImportRunBase, table=True):
    __tablename__ = "field_import_runs"

    id: int | None = Field(default=None, primary_key=True)
    field_project_id: int = Field(foreign_key="field_projects.id", index=True)

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))
    completed_at: datetime | None = Field(default=None)


class FieldImportRunPublic(FieldImportRunBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    field_project_id: int
    created_at: datetime
    completed_at: datetime | None
