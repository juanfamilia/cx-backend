"""Brief PRE-FIELD: persistente por FieldStudy (gobierno ADR 001)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import ConfigDict, Field as PydanticField
from sqlalchemy import Column, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class FieldBriefConsultHintPublic(SQLModel):
    """Mensaje consultivo emitido por el servidor (no reglas en navegador)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    tone: Literal["warn", "ok"]
    message: str
    apply_label: str = "Ir al brief"
    show_apply: bool = True


class FieldStudyBrief(SQLModel, table=True):
    __tablename__ = "field_study_brief"

    id: int | None = Field(default=None, primary_key=True)
    study_id: int = Field(foreign_key="field_studies.id", unique=True, index=True)
    company_id: int = Field(foreign_key="companies.id", index=True)

    payload_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB, nullable=False))
    completeness_score: float | None = Field(default=None)

    approval_state: str = Field(default="draft", max_length=32)

    approved_internal_user_id: int | None = Field(default=None, foreign_key="users.id")
    approved_internal_at: datetime | None = Field(default=None)
    approved_client_user_id: int | None = Field(default=None, foreign_key="users.id")
    approved_client_at: datetime | None = Field(default=None)

    body_hash: str = Field(default="", max_length=128)

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now())
    )
    updated_by_user_id: int | None = Field(default=None, foreign_key="users.id")


class FieldStudyBriefPatch(SQLModel):
    payload: dict[str, Any] | None = None
    completeness_score: float | None = PydanticField(
        default=None,
        ge=0,
        le=100,
        description="Score 0–100 o convención acordada; nullable.",
    )


class FieldStudyBriefPublic(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    study_id: int
    company_id: int
    payload_json: dict[str, Any]
    completeness_score: float | None = None
    approval_state: str
    approved_internal_user_id: int | None = None
    approved_internal_at: datetime | None = None
    approved_client_user_id: int | None = None
    approved_client_at: datetime | None = None
    body_hash: str
    updated_at: datetime

    #: Clasificación de «densidad» del brief desde `completeness_score` (solo FastAPI).
    brief_density_band: Literal["unknown", "thin", "adequate", "rich"] = "unknown"
    consultive_hints: list[FieldBriefConsultHintPublic] = Field(default_factory=list)

