"""Readiness Gate L4 — políticas, signatarios autorizados y firmas."""

from __future__ import annotations

from datetime import datetime

from pydantic import ConfigDict, Field as PydanticField, field_validator
from sqlalchemy import Column, DateTime, Text, func
from sqlmodel import Field, SQLModel

from app.models.field_instrument_revision_model import FieldInstrumentRevisionPublic


class CompanyFieldReadinessPolicy(SQLModel, table=True):
    __tablename__ = "company_field_readiness_policy"

    company_id: int = Field(foreign_key="companies.id", primary_key=True)
    require_role_research: bool = Field(default=True)
    require_role_qa: bool = Field(default=True)
    require_role_account: bool = Field(default=False)
    block_on_schema_invalid: bool = Field(default=True)
    block_on_missing_schema_validation: bool = Field(default=True)
    block_on_qa_stop: bool = Field(default=True)
    block_on_qa_fix_now: bool = Field(default=False)
    require_qa_run: bool = Field(default=True)
    enforce_signatory_grants: bool = Field(default=False)
    require_brief_approved: bool = Field(
        default=False,
        description=(
            "Si true, Readiness bloquea hasta brief del Study en approved_internal o approved."
        ),
    )

    updated_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now())
    )
    updated_by_user_id: int | None = Field(default=None, foreign_key="users.id")


class FieldReadinessSignatory(SQLModel, table=True):
    __tablename__ = "field_readiness_signatories"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    signature_role: str = Field(max_length=64)

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))
    deleted_at: datetime | None = Field(default=None)


class FieldReadinessSignature(SQLModel, table=True):
    __tablename__ = "field_readiness_signatures"

    id: int | None = Field(default=None, primary_key=True)
    revision_id: int = Field(foreign_key="field_instrument_revisions.id", index=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    signature_role: str = Field(max_length=64)
    signer_user_id: int = Field(foreign_key="users.id")

    signed_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))
    comment: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    snapshot_spec_hash: str = Field(max_length=128)
    snapshot_qa_run_id: int | None = Field(
        default=None,
        foreign_key="field_instrument_qa_runs.id",
    )
    revoked_at: datetime | None = Field(default=None)


class FieldReadinessPolicyPublic(SQLModel):
    company_id: int
    require_role_research: bool
    require_role_qa: bool
    require_role_account: bool
    block_on_schema_invalid: bool
    block_on_missing_schema_validation: bool
    block_on_qa_stop: bool
    block_on_qa_fix_now: bool
    require_qa_run: bool
    enforce_signatory_grants: bool
    require_brief_approved: bool


class FieldReadinessPolicyUpsert(SQLModel):
    """Upsert parcial (solo campos enviados)."""

    require_role_research: bool | None = None
    require_role_qa: bool | None = None
    require_role_account: bool | None = None
    block_on_schema_invalid: bool | None = None
    block_on_missing_schema_validation: bool | None = None
    block_on_qa_stop: bool | None = None
    block_on_qa_fix_now: bool | None = None
    require_qa_run: bool | None = None
    enforce_signatory_grants: bool | None = None
    require_brief_approved: bool | None = None


class FieldReadinessSignatoryPublic(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    user_id: int
    signature_role: str
    created_at: datetime


class FieldReadinessSignatoryCreate(SQLModel):
    user_id: int
    signature_role: str

    @field_validator("signature_role", mode="before")
    @classmethod
    def _strip_role(cls, v: object) -> str:
        return str(v).strip()


class FieldReadinessSignaturePublic(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    revision_id: int
    signature_role: str
    signer_user_id: int
    signed_at: datetime
    comment: str | None = None
    snapshot_spec_hash: str
    snapshot_qa_run_id: int | None = None


class ReadinessSignBody(SQLModel):
    signature_role: str = PydanticField(max_length=64)
    comment: str | None = PydanticField(default=None, max_length=2000)

    @field_validator("signature_role", mode="before")
    @classmethod
    def _strip(cls, v: object) -> str:
        return str(v).strip()


class ReadinessGatePublic(SQLModel):
    """Estado agregado Readiness para UI / integraciones."""

    revision_id: int
    revision_status: str
    aggregate_status: str = PydanticField(
        description="blocked | pending_signatures | ready | approved",
    )
    blocking_codes: list[str]
    missing_roles: list[str]
    stale_roles: list[str]
    required_roles: list[str]
    policy: FieldReadinessPolicyPublic
    last_validation_ok: bool | None = None
    content_hash: str
    latest_qa_run_id: int | None = None
    qa_stop_count: int | None = None
    qa_fix_now_count: int | None = None
    signatures: list[FieldReadinessSignaturePublic]


class ReadinessSignResult(SQLModel):
    readiness: ReadinessGatePublic
    revision: FieldInstrumentRevisionPublic
