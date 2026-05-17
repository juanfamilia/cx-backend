"""Eventos de señal agnósticos de dominio — memoria compartida por tenant."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class PlatformSignalEvent(SQLModel, table=True):
    """Una fila = una señal emitida por un módulo (InS, Field, …) visible para todo el cerebro."""

    __tablename__ = "platform_signal_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    source_domain: str = Field(max_length=32, index=True)
    signal_code: str = Field(max_length=64)
    severity: Optional[str] = Field(default=None, max_length=16)
    summary: str = Field(sa_column=Column(Text, nullable=False))
    payload_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    field_study_id: Optional[int] = Field(default=None, foreign_key="field_studies.id")
    field_project_id: Optional[int] = Field(default=None, foreign_key="field_projects.id")
    ins_study_id: Optional[int] = Field(default=None, foreign_key="ins_studies.id")
    created_by_user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
