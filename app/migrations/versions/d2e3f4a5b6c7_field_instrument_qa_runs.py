"""field_instrument_qa_runs — historial Auto QA bootstrap PRE-FIELD.

Revision ID: d2e3f4a5b6c7
Revises: b7c8d9e0f1a2
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "field_instrument_qa_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("revision_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("ruleset_version", sa.String(length=64), nullable=False),
        sa.Column(
            "source",
            sa.String(length=64),
            nullable=False,
            server_default="instrument_qa_runtime",
        ),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column(
            "findings_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("stop_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fix_now_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("monitor_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["revision_id"], ["field_instrument_revisions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_field_instrument_qa_runs_revision_id",
        "field_instrument_qa_runs",
        ["revision_id"],
        unique=False,
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_field_instrument_qa_runs_rev_created "
            "ON field_instrument_qa_runs (revision_id, created_at DESC)"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_field_instrument_qa_runs_rev_created"))
    op.drop_index("ix_field_instrument_qa_runs_revision_id", table_name="field_instrument_qa_runs")
    op.drop_table("field_instrument_qa_runs")
