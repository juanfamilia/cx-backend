"""Field: hallazgos con capa de decisión (import opcional, sync, política, gobernanza).

Revision ID: q8r9s0t1u2v3
Revises: p7q8r9s0t1u2
Create Date: 2026-04-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "q8r9s0t1u2v3"
down_revision: Union[str, None] = "p7q8r9s0t1u2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("field_findings", sa.Column("field_sync_run_id", sa.Integer(), nullable=True))
    op.add_column("field_findings", sa.Column("field_policy_set_id", sa.Integer(), nullable=True))
    op.add_column("field_findings", sa.Column("idempotency_key", sa.Text(), nullable=True))
    op.add_column("field_findings", sa.Column("source", sa.String(length=32), nullable=True))
    op.add_column("field_findings", sa.Column("explanation", sa.Text(), nullable=True))
    op.add_column("field_findings", sa.Column("recommendation", sa.Text(), nullable=True))
    op.add_column("field_findings", sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("field_findings", sa.Column("approval_status", sa.String(length=32), nullable=True))
    op.add_column("field_findings", sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True))
    op.add_column("field_findings", sa.Column("reviewed_at", sa.DateTime(), nullable=True))
    op.alter_column("field_findings", "field_import_run_id", existing_type=sa.Integer(), nullable=True)
    op.create_index("ix_field_findings_sync_run", "field_findings", ["field_sync_run_id"], unique=False)
    op.create_index("ix_field_findings_policy", "field_findings", ["field_policy_set_id"], unique=False)
    op.create_index("ix_field_findings_source", "field_findings", ["source"], unique=False)
    op.create_foreign_key(
        "field_findings_field_sync_run_id_fk",
        "field_findings",
        "field_sync_runs",
        ["field_sync_run_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "field_findings_field_policy_set_id_fk",
        "field_findings",
        "field_policy_sets",
        ["field_policy_set_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "field_findings_reviewed_by_user_id_fk",
        "field_findings",
        "users",
        ["reviewed_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_field_finding_idem_unique",
        "field_findings",
        ["field_project_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_field_finding_idem_unique", table_name="field_findings", postgresql_where=sa.text("idempotency_key IS NOT NULL"))
    op.drop_constraint("field_findings_reviewed_by_user_id_fk", "field_findings", type_="foreignkey")
    op.drop_constraint("field_findings_field_policy_set_id_fk", "field_findings", type_="foreignkey")
    op.drop_constraint("field_findings_field_sync_run_id_fk", "field_findings", type_="foreignkey")
    op.drop_index("ix_field_findings_source", table_name="field_findings")
    op.drop_index("ix_field_findings_policy", table_name="field_findings")
    op.drop_index("ix_field_findings_sync_run", table_name="field_findings")
    op.alter_column("field_findings", "field_import_run_id", existing_type=sa.Integer(), nullable=False)
    op.drop_column("field_findings", "reviewed_at")
    op.drop_column("field_findings", "reviewed_by_user_id")
    op.drop_column("field_findings", "approval_status")
    op.drop_column("field_findings", "evidence")
    op.drop_column("field_findings", "recommendation")
    op.drop_column("field_findings", "explanation")
    op.drop_column("field_findings", "source")
    op.drop_column("field_findings", "idempotency_key")
    op.drop_column("field_findings", "field_policy_set_id")
    op.drop_column("field_findings", "field_sync_run_id")
