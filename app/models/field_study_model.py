"""7Field — estudio canónico (cadena Study → Field Project → hallazgos)."""

from datetime import datetime

from pydantic import ConfigDict
from sqlalchemy import Column, DateTime, Text, func
from sqlmodel import Field, SQLModel


class FieldStudyBase(SQLModel):
    name: str = Field(max_length=500)
    primary_language: str | None = Field(
        default=None,
        max_length=16,
        description="BCP-47 corto (ej. es, es-MX); null hasta configurarlo.",
    )
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    status: str = Field(
        default="draft",
        max_length=32,
        description="draft | active | archived",
    )
    external_ref: str | None = Field(
        default=None,
        max_length=255,
        description="Referencia en CRM u otro sistema del cliente.",
    )


class FieldStudy(FieldStudyBase, table=True):
    __tablename__ = "field_studies"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    client_id: int = Field(foreign_key="end_clients.id", index=True)

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now())
    )


class FieldStudyCreate(SQLModel):
    name: str
    description: str | None = None
    client_id: int
    company_id: int | None = Field(
        default=None,
        description="Rol 0: obligatorio si el usuario no tiene empresa en sesión.",
    )


class FieldStudyPublic(FieldStudyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    client_id: int
    created_at: datetime
    updated_at: datetime
