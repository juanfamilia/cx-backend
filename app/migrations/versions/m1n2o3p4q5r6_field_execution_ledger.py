"""Field Execution Ledger (B): filas de import, findings, eventos.

Revision ID: m1n2o3p4q5r6
Revises: l6m7n8o9p0q1
Create Date: 2026-04-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "m1n2o3p4q5r6"
down_revision: Union[str, None] = "l6m7n8o9p0q1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "field_import_rows",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("field_project_id", sa.Integer(), nullable=False),
        sa.Column("field_import_run_id", sa.Integer(), nullable=False),
        sa.Column("source_row_number", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.String(length=500), nullable=False),
        sa.Column("wave_id", sa.String(length=500), nullable=False),
        sa.Column("interviewer_id", sa.String(length=500), nullable=False),
        sa.Column("disposition", sa.String(length=255), nullable=False),
        sa.Column("started_at_text", sa.String(length=500), nullable=True),
        sa.Column("completed_at_text", sa.String(length=500), nullable=True),
        sa.Column("duration_sec", sa.Integer(), nullable=True),
        sa.Column("extras", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["field_import_run_id"], ["field_import_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_project_id"], ["field_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_field_import_rows_run_id", "field_import_rows", ["field_import_run_id"], unique=False)
    op.create_index("ix_field_import_rows_project_case", "field_import_rows", ["field_project_id", "case_id"], unique=False)

    op.create_table(
        "field_findings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("field_project_id", sa.Integer(), nullable=False),
        sa.Column("field_import_run_id", sa.Integer(), nullable=False),
        sa.Column("field_import_row_id", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("case_id", sa.String(length=500), nullable=True),
        sa.Column("wave_id", sa.String(length=500), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["field_import_row_id"], ["field_import_rows.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_import_run_id"], ["field_import_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_project_id"], ["field_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_field_findings_run_id", "field_findings", ["field_import_run_id"], unique=False)
    op.create_index("ix_field_findings_code", "field_findings", ["code"], unique=False)

    op.create_table(
        "field_ledger_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("field_project_id", sa.Integer(), nullable=False),
        sa.Column("field_import_run_id", sa.Integer(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["field_import_run_id"], ["field_import_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["field_project_id"], ["field_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_field_ledger_events_project", "field_ledger_events", ["field_project_id"], unique=False)
    op.create_index("ix_field_ledger_events_run", "field_ledger_events", ["field_import_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_field_ledger_events_run", table_name="field_ledger_events")
    op.drop_index("ix_field_ledger_events_project", table_name="field_ledger_events")
    op.drop_table("field_ledger_events")

    op.drop_index("ix_field_findings_code", table_name="field_findings")
    op.drop_index("ix_field_findings_run_id", table_name="field_findings")
    op.drop_table("field_findings")

    op.drop_index("ix_field_import_rows_project_case", table_name="field_import_rows")
    op.drop_index("ix_field_import_rows_run_id", table_name="field_import_rows")
    op.drop_table("field_import_rows")
