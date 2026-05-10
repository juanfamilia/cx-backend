"""Historial de corridas Auto QA PRE-FIELD (`instrument_qa_runtime`)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field as PydanticField
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

QA_RULESET_BOOTSTRAP_V1_CONST = "QA_RULESET_BOOTSTRAP_V1"
QA_SOURCE_CONST = "instrument_qa_runtime"


class FieldInstrumentQARun(SQLModel, table=True):
    __tablename__ = "field_instrument_qa_runs"

    id: int | None = Field(default=None, primary_key=True)
    revision_id: int = Field(foreign_key="field_instrument_revisions.id", index=True)
    company_id: int = Field(foreign_key="companies.id", index=True)

    ruleset_version: str = Field(max_length=64)
    source: str = Field(default=QA_SOURCE_CONST, max_length=64)
    content_hash: str = Field(max_length=128)

    findings_json: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )
    stop_count: int = Field(default=0)
    fix_now_count: int = Field(default=0)
    monitor_count: int = Field(default=0)

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))
    created_by_user_id: int | None = Field(default=None, foreign_key="users.id")


class FieldInstrumentQARunPublic(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    revision_id: int
    company_id: int
    ruleset_version: str
    source: str
    content_hash: str
    stop_count: int
    fix_now_count: int
    monitor_count: int
    findings_json: list[dict[str, Any]] = PydanticField(default_factory=list)
    created_at: datetime
    created_by_user_id: int | None = None


class InstrumentQAFindingPublic(SQLModel):
    """Hallazgo QA_RULE_* serializable (API)."""

    source: str = QA_SOURCE_CONST
    ruleset_version: str = QA_RULESET_BOOTSTRAP_V1_CONST
    rule_id: str
    severity: str
    item_id: str | None = None
    block_id: str | None = None
    message: str


class InstrumentQAExecuteResponse(SQLModel):
    run: FieldInstrumentQARunPublic
    findings: list[InstrumentQAFindingPublic]
