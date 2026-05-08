"""field_instrument_revisions — PRE-FIELD revisions + auditoría de validación schema.

Revision ID: b7c8d9e0f1a2
Revises: z9y8x7w6v5u4
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, None] = "z9y8x7w6v5u4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "field_instrument_revisions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("study_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("revision_label", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("framework_template_id", sa.String(length=128), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("instrument_spec_version_declared", sa.String(length=64), nullable=True),
        sa.Column(
            "spec_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("content_hash", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("last_validation_at", sa.DateTime(), nullable=True),
        sa.Column("last_validation_ok", sa.Boolean(), nullable=True),
        sa.Column("last_validation_issue_count", sa.Integer(), nullable=True),
        sa.Column("last_validation_content_hash", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["study_id"], ["field_studies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_field_instrument_revisions_study_id",
        "field_instrument_revisions",
        ["study_id"],
        unique=False,
    )
    op.create_index(
        "ix_field_instrument_revisions_company_id",
        "field_instrument_revisions",
        ["company_id"],
        unique=False,
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_field_instrument_revisions_study_updated_at "
            "ON field_instrument_revisions (study_id, updated_at DESC)"
        )
    )
    op.create_index(
        "uq_field_instr_rev_study_label_live",
        "field_instrument_revisions",
        ["study_id", "revision_label"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_field_instr_rev_study_label_live",
        table_name="field_instrument_revisions",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.execute(sa.text("DROP INDEX IF EXISTS ix_field_instrument_revisions_study_updated_at"))
    op.drop_index("ix_field_instrument_revisions_company_id", table_name="field_instrument_revisions")
    op.drop_index("ix_field_instrument_revisions_study_id", table_name="field_instrument_revisions")
    op.drop_table("field_instrument_revisions")
