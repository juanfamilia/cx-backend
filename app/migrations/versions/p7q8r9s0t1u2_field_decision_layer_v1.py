"""Field: capa de decisión — fuentes externas, políticas, sync runs, snapshot operacional.

Revision ID: p7q8r9s0t1u2
Revises: m1n2o3p4q5r6
Create Date: 2026-04-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "p7q8r9s0t1u2"
down_revision: Union[str, None] = "m1n2o3p4q5r6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "field_project_external_sources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("field_project_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("external_project_id", sa.String(length=255), nullable=True),
        sa.Column("external_survey_id", sa.String(length=255), nullable=True),
        sa.Column("external_customer_id", sa.String(length=255), nullable=True),
        sa.Column("wave_id", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sync_strategy", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_project_id"], ["field_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fpes_company_id", "field_project_external_sources", ["company_id"], unique=False)
    op.create_index("ix_fpes_field_project", "field_project_external_sources", ["field_project_id"], unique=False)
    op.create_index("ix_fpes_source_type", "field_project_external_sources", ["source_type"], unique=False)
    op.create_index("ix_fpes_active", "field_project_external_sources", ["is_active"], unique=False)

    op.create_table(
        "field_policy_sets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("field_project_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["field_project_id"], ["field_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("field_project_id", "version", name="uq_field_policy_project_version"),
    )
    op.create_index("ix_fps_project", "field_policy_sets", ["field_project_id"], unique=False)
    op.create_index("ix_fps_version", "field_policy_sets", ["version"], unique=False)

    op.create_table(
        "field_sync_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("field_project_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("run_kind", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("field_project_external_source_id", sa.Integer(), nullable=True),
        sa.Column("field_import_run_id", sa.Integer(), nullable=True),
        sa.Column("field_policy_set_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("total_records", sa.Integer(), nullable=True),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_import_run_id"], ["field_import_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["field_policy_set_id"], ["field_policy_sets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["field_project_external_source_id"],
            ["field_project_external_sources.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["field_project_id"], ["field_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fsr_idempotency", "field_sync_runs", ["idempotency_key"], unique=True)
    op.create_index("ix_fsr_project", "field_sync_runs", ["field_project_id"], unique=False)
    op.create_index("ix_fsr_company", "field_sync_runs", ["company_id"], unique=False)
    op.create_index("ix_fsr_run_kind", "field_sync_runs", ["run_kind"], unique=False)
    op.create_index("ix_fsr_status", "field_sync_runs", ["status"], unique=False)

    op.create_table(
        "field_operational_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("field_project_id", sa.Integer(), nullable=False),
        sa.Column("field_sync_run_id", sa.Integer(), nullable=True),
        sa.Column("field_policy_set_id", sa.Integer(), nullable=True),
        sa.Column("quotas_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("gps_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("route_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("field_status", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("last_calculated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["field_policy_set_id"], ["field_policy_sets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["field_project_id"], ["field_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_sync_run_id"], ["field_sync_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("field_project_id", name="uq_fos_one_per_project"),
    )
    op.create_index("ix_fos_sync_run", "field_operational_snapshots", ["field_sync_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_fos_sync_run", table_name="field_operational_snapshots")
    op.drop_table("field_operational_snapshots")

    op.drop_index("ix_fsr_status", table_name="field_sync_runs")
    op.drop_index("ix_fsr_run_kind", table_name="field_sync_runs")
    op.drop_index("ix_fsr_company", table_name="field_sync_runs")
    op.drop_index("ix_fsr_project", table_name="field_sync_runs")
    op.drop_index("ix_fsr_idempotency", table_name="field_sync_runs")
    op.drop_table("field_sync_runs")

    op.drop_index("ix_fps_version", table_name="field_policy_sets")
    op.drop_index("ix_fps_project", table_name="field_policy_sets")
    op.drop_table("field_policy_sets")

    op.drop_index("ix_fpes_active", table_name="field_project_external_sources")
    op.drop_index("ix_fpes_source_type", table_name="field_project_external_sources")
    op.drop_index("ix_fpes_field_project", table_name="field_project_external_sources")
    op.drop_index("ix_fpes_company_id", table_name="field_project_external_sources")
    op.drop_table("field_project_external_sources")
