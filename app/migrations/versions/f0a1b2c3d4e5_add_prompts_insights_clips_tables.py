"""add prompts insights clips tables

Revision ID: f0a1b2c3d4e5
Revises: b3f2d1c4a8e7
Create Date: 2026-04-02

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f0a1b2c3d4e5"
down_revision: Union[str, None] = "b3f2d1c4a8e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    insight_type_enum = sa.Enum(
        "summary",
        "alert",
        "recommendation",
        name="insighttypeenum",
    )
    insight_priority_enum = sa.Enum(
        "low",
        "medium",
        "high",
        name="insightpriorityenum",
    )
    insight_type_enum.create(op.get_bind(), checkfirst=True)
    insight_priority_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "prompts",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_prompts_company_id"), "prompts", ["company_id"], unique=False)
    op.create_index(op.f("ix_prompts_is_active"), "prompts", ["is_active"], unique=False)
    op.create_index(op.f("ix_prompts_name"), "prompts", ["name"], unique=False)
    op.create_index(op.f("ix_prompts_type"), "prompts", ["type"], unique=False)

    op.create_table(
        "insights",
        sa.Column("evaluation_id", sa.Integer(), nullable=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM(
                "summary",
                "alert",
                "recommendation",
                name="insighttypeenum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column(
            "priority",
            postgresql.ENUM(
                "low",
                "medium",
                "high",
                name="insightpriorityenum",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column(
            "suggested_actions",
            postgresql.ARRAY(sa.String()),
            nullable=True,
        ),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["evaluation_id"], ["evaluations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_insights_company_id"), "insights", ["company_id"], unique=False
    )
    op.create_index(
        op.f("ix_insights_evaluation_id"), "insights", ["evaluation_id"], unique=False
    )
    op.create_index(op.f("ix_insights_priority"), "insights", ["priority"], unique=False)
    op.create_index(op.f("ix_insights_type"), "insights", ["type"], unique=False)

    op.create_table(
        "clips",
        sa.Column("evaluation_id", sa.Integer(), nullable=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("insight_id", sa.Integer(), nullable=True),
        sa.Column("tag", sa.String(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["evaluation_id"], ["evaluations.id"]),
        sa.ForeignKeyConstraint(["insight_id"], ["insights.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clips_company_id"), "clips", ["company_id"], unique=False)
    op.create_index(
        op.f("ix_clips_evaluation_id"), "clips", ["evaluation_id"], unique=False
    )
    op.create_index(op.f("ix_clips_insight_id"), "clips", ["insight_id"], unique=False)
    op.create_index(op.f("ix_clips_tag"), "clips", ["tag"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_clips_tag"), table_name="clips")
    op.drop_index(op.f("ix_clips_insight_id"), table_name="clips")
    op.drop_index(op.f("ix_clips_evaluation_id"), table_name="clips")
    op.drop_index(op.f("ix_clips_company_id"), table_name="clips")
    op.drop_table("clips")

    op.drop_index(op.f("ix_insights_type"), table_name="insights")
    op.drop_index(op.f("ix_insights_priority"), table_name="insights")
    op.drop_index(op.f("ix_insights_evaluation_id"), table_name="insights")
    op.drop_index(op.f("ix_insights_company_id"), table_name="insights")
    op.drop_table("insights")

    op.drop_index(op.f("ix_prompts_type"), table_name="prompts")
    op.drop_index(op.f("ix_prompts_name"), table_name="prompts")
    op.drop_index(op.f("ix_prompts_is_active"), table_name="prompts")
    op.drop_index(op.f("ix_prompts_company_id"), table_name="prompts")
    op.drop_table("prompts")

    op.execute("DROP TYPE IF EXISTS insightpriorityenum")
    op.execute("DROP TYPE IF EXISTS insighttypeenum")
