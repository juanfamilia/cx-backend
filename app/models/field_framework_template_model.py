"""Framework Library — plantillas metodológicas PRE-FIELD (catálogo global)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import ConfigDict
from sqlalchemy import Column, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class FieldFrameworkTemplate(SQLModel, table=True):
    __tablename__ = "field_framework_templates"

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(max_length=128, index=True)
    study_type: str = Field(max_length=64, index=True)
    framework_version: str = Field(max_length=32)

    title: str = Field(max_length=300)
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    coverage_rules: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
    )
    stub_spec_json: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )

    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))


class FieldFrameworkTemplatePublic(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    study_type: str
    framework_version: str
    title: str
    description: str | None = None
    coverage_rules: dict[str, Any] = Field(default_factory=dict)
    stub_spec_json: dict[str, Any] | None = None
    sort_order: int
    is_active: bool
