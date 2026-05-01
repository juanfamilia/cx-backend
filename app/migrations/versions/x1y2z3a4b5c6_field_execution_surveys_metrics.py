"""Field execution model: surveys + KPI metrics + project execution_metadata.

Revision ID: x1y2z3a4b5c6
Revises: v4w5x6y7z8a9
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "x1y2z3a4b5c6"
down_revision: Union[str, None] = "v4w5x6y7z8a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "field_projects",
        sa.Column(
            "execution_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "field_projects",
        sa.Column("last_execution_sync_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "field_surveys",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("field_project_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("external_survey_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=True),
        sa.Column("mode", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("survey_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_project_id"], ["field_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("field_project_id", "external_survey_id", name="uq_field_survey_project_external"),
    )
    op.create_index("ix_field_surveys_project", "field_surveys", ["field_project_id"], unique=False)
    op.create_index("ix_field_surveys_company", "field_surveys", ["company_id"], unique=False)
    op.create_index("ix_field_surveys_external", "field_surveys", ["external_survey_id"], unique=False)

    op.create_table(
        "field_metrics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("field_project_id", sa.Integer(), nullable=False),
        sa.Column("metric_code", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column("dimensions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["field_project_id"], ["field_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_field_metrics_project", "field_metrics", ["field_project_id"], unique=False)
    op.create_index("ix_field_metrics_code", "field_metrics", ["metric_code"], unique=False)
    op.create_index("ix_field_metrics_calc_at", "field_metrics", ["calculated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_field_metrics_calc_at", table_name="field_metrics")
    op.drop_index("ix_field_metrics_code", table_name="field_metrics")
    op.drop_index("ix_field_metrics_project", table_name="field_metrics")
    op.drop_table("field_metrics")

    op.drop_index("ix_field_surveys_external", table_name="field_surveys")
    op.drop_index("ix_field_surveys_company", table_name="field_surveys")
    op.drop_index("ix_field_surveys_project", table_name="field_surveys")
    op.drop_table("field_surveys")

    op.drop_column("field_projects", "last_execution_sync_at")
    op.drop_column("field_projects", "execution_metadata")
