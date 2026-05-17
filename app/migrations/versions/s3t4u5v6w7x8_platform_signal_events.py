"""platform_signal_events — memoria compartida cross-dominio (tenant brain).

Revision ID: s3t4u5v6w7x8
Revises: w5x6y7z8a9b0
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "s3t4u5v6w7x8"
down_revision: Union[str, None] = "w5x6y7z8a9b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "platform_signal_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("source_domain", sa.String(length=32), nullable=False),
        sa.Column("signal_code", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column(
            "payload_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("field_study_id", sa.Integer(), nullable=True),
        sa.Column("field_project_id", sa.Integer(), nullable=True),
        sa.Column("ins_study_id", sa.Integer(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["field_study_id"], ["field_studies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["field_project_id"], ["field_projects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ins_study_id"], ["ins_studies.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_platform_signal_events_company_created",
        "platform_signal_events",
        ["company_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_platform_signal_events_source_domain"),
        "platform_signal_events",
        ["source_domain"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_platform_signal_events_source_domain"), table_name="platform_signal_events")
    op.drop_index("ix_platform_signal_events_company_created", table_name="platform_signal_events")
    op.drop_table("platform_signal_events")
