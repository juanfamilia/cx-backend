"""7Field — Rule Configuration Engine: packs versionados (payload JSON auditable)."""

from datetime import datetime
from typing import Any, Optional

from pydantic import ConfigDict
from sqlalchemy import Column, DateTime, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

PACK_KIND_SCORING = "scoring"
PACK_KIND_INSTRUMENT_QA = "instrument_qa"
PACK_KIND_FIELD_EXECUTION = "field_execution"


class FieldRuleConfigurationPack(SQLModel, table=True):
    """
    Agrupa versiones de reglas por alcance tenant (`company_id`).
    Los payloads efectivos viven en FieldRuleConfigurationVersion.
    """

    __tablename__ = "field_rule_configuration_packs"
    __table_args__ = (
        UniqueConstraint("company_id", "slug", name="uq_field_rule_pack_company_slug"),
    )

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    name: str = Field(max_length=255)
    slug: str = Field(max_length=128, description="Identificador estable dentro de la empresa.")
    pack_kind: str = Field(
        max_length=32,
        description="scoring | instrument_qa | field_execution",
    )
    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))


class FieldRuleConfigurationVersion(SQLModel, table=True):
    __tablename__ = "field_rule_configuration_versions"
    __table_args__ = (
        UniqueConstraint("pack_id", "version_number", name="uq_field_rule_version_pack_no"),
    )

    id: int | None = Field(default=None, primary_key=True)
    pack_id: int = Field(foreign_key="field_rule_configuration_packs.id", index=True)
    version_number: int = Field(ge=1, description="Monotónico por pack.")
    effective_from: datetime = Field(
        sa_column=Column(DateTime, nullable=False),
        description="Inicio de vigencia (servidor).",
    )
    effective_to: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True),
        description="Fin de vigencia; null = vigente si último aprobado.",
    )
    status: str = Field(
        default="draft",
        max_length=32,
        description="draft | approved | retired",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
        description="Umbrales, pesos, mapping QA_RULE_* según pack_kind.",
    )
    change_reason: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    approved_by_user_id: int | None = Field(default=None, foreign_key="users.id", nullable=True)
    approved_at: datetime | None = Field(default=None)
    created_by_user_id: int | None = Field(default=None, foreign_key="users.id", nullable=True)

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))


class FieldRuleConfigurationPackPublic(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    name: str
    slug: str
    pack_kind: str
    created_at: datetime


class FieldRuleConfigurationVersionPublic(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pack_id: int
    version_number: int
    effective_from: datetime
    effective_to: datetime | None
    status: str
    payload: dict[str, Any]
    change_reason: Optional[str] = None
    approved_by_user_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_by_user_id: Optional[int] = None
    created_at: datetime
