"""add evaluation events table

Revision ID: b3f2d1c4a8e7
Revises: 2fbe48d2fb88
Create Date: 2026-03-23 10:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = "b3f2d1c4a8e7"
down_revision: Union[str, None] = "2fbe48d2fb88"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evaluation_events",
        sa.Column("evaluation_id", sa.Integer(), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "complaint",
                "emotional_peak",
                "sales_signal",
                "objection",
                "resolution",
                "compliance_risk",
                "other",
                name="evaluationeventtypeenum",
            ),
            nullable=False,
        ),
        sa.Column("timestamp_seconds", sa.Float(), nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column("source", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["evaluation_id"], ["evaluations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_evaluation_events_evaluation_id"),
        "evaluation_events",
        ["evaluation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evaluation_events_timestamp_seconds"),
        "evaluation_events",
        ["timestamp_seconds"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_evaluation_events_timestamp_seconds"), table_name="evaluation_events")
    op.drop_index(op.f("ix_evaluation_events_evaluation_id"), table_name="evaluation_events")
    op.drop_table("evaluation_events")
    op.execute("DROP TYPE IF EXISTS evaluationeventtypeenum")
