"""Readiness Gate L4 — política por empresa, signatarios y firmas con snapshot.

Revision ID: r8n7s6r5q4p3
Revises: d2e3f4a5b6c7
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "r8n7s6r5q4p3"
down_revision: Union[str, None] = "d2e3f4a5b6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "company_field_readiness_policy",
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("require_role_research", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("require_role_qa", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("require_role_account", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("block_on_schema_invalid", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("block_on_missing_schema_validation", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("block_on_qa_stop", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("block_on_qa_fix_now", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("require_qa_run", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("enforce_signatory_grants", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("company_id"),
    )

    op.create_table(
        "field_readiness_signatories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("signature_role", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_field_readiness_signatories_company_id",
        "field_readiness_signatories",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        "uq_field_readiness_signatory_live",
        "field_readiness_signatories",
        ["company_id", "user_id", "signature_role"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "field_readiness_signatures",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("revision_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("signature_role", sa.String(length=64), nullable=False),
        sa.Column("signer_user_id", sa.Integer(), nullable=False),
        sa.Column("signed_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("snapshot_spec_hash", sa.String(length=128), nullable=False),
        sa.Column("snapshot_qa_run_id", sa.Integer(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["revision_id"], ["field_instrument_revisions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["signer_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["snapshot_qa_run_id"], ["field_instrument_qa_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_field_readiness_signatures_revision_id",
        "field_readiness_signatures",
        ["revision_id"],
        unique=False,
    )
    op.create_index(
        "uq_field_readiness_signature_role_live",
        "field_readiness_signatures",
        ["revision_id", "signature_role"],
        unique=True,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_field_readiness_signature_role_live",
        table_name="field_readiness_signatures",
        postgresql_where=sa.text("revoked_at IS NULL"),
    )
    op.drop_index("ix_field_readiness_signatures_revision_id", table_name="field_readiness_signatures")
    op.drop_table("field_readiness_signatures")

    op.drop_index(
        "uq_field_readiness_signatory_live",
        table_name="field_readiness_signatories",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_index("ix_field_readiness_signatories_company_id", table_name="field_readiness_signatories")
    op.drop_table("field_readiness_signatories")

    op.drop_table("company_field_readiness_policy")
