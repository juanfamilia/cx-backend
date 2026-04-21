"""Siete InS — estudios cualitativos (producto separado de CX, misma plataforma)."""

from datetime import datetime

from pydantic import ConfigDict
from sqlalchemy import Column, DateTime, String, Text, func
from sqlmodel import Field, SQLModel


class InsStudyBase(SQLModel):
    title: str = Field(max_length=500)
    objective: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    """Objetivo de decisión del estudio (p. ej. hipótesis a validar)."""
    status: str = Field(
        default="draft",
        sa_column=Column(String(32), nullable=False),
        description="draft | active | archived",
    )
    pipeline_status: str = Field(
        default="idle",
        sa_column=Column(String(32), nullable=False),
        description="idle | queued | transcribing | analyzing | ready | failed",
    )
    rubric_version: str = Field(
        default="v0",
        sa_column=Column(String(64), nullable=False),
        description="Versión de rúbrica / guía anclada al estudio.",
    )


class InsStudy(InsStudyBase, table=True):
    __tablename__ = "ins_studies"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    created_by: int | None = Field(default=None, foreign_key="users.id", nullable=True)

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)


class InsStudyCreate(SQLModel):
    title: str
    objective: str | None = None
    company_id: int | None = None
    """Solo rol 0: empresa donde se crea el estudio. Resto: se ignora (usa company del usuario)."""


class InsStudyPublic(InsStudyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    created_by: int | None
    created_at: datetime
    updated_at: datetime
