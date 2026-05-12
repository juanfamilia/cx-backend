"""Framework waiver PRE-FIELD — ligado a instrument_revision_id (ADR 001)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field as PydanticField
from sqlalchemy import Column, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class FieldFrameworkWaiver(SQLModel, table=True):
    __tablename__ = "field_framework_waivers"

    id: int | None = Field(default=None, primary_key=True)
    instrument_revision_id: int = Field(foreign_key="field_instrument_revisions.id", index=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    rationale: str = Field(sa_column=Column(Text, nullable=False))
    waived_sections_json: list[Any] | dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )
    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))
    created_by_user_id: int | None = Field(default=None, foreign_key="users.id")


class FieldFrameworkWaiverCreate(SQLModel):
    rationale: str = PydanticField(max_length=20000)
    waived_sections: list[Any] | dict[str, Any] | None = None


class FieldFrameworkWaiverPublic(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    instrument_revision_id: int
    company_id: int
    rationale: str
    waived_sections_json: list[Any] | dict[str, Any] | None = None
    created_at: datetime
    created_by_user_id: int | None = None
