"""field_participant_journeys: bundle JSON + QA run FK; field_journey_phases: experience arc.

Revision ID: w5x6y7z8a9b0
Revises: p9q8r7s6t5u4
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "w5x6y7z8a9b0"
down_revision: Union[str, None] = "p9q8r7s6t5u4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "field_participant_journeys",
        sa.Column(
            "bundle_snapshot_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "field_participant_journeys",
        sa.Column("field_instrument_qa_run_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_field_pj_qa_run_id",
        "field_participant_journeys",
        "field_instrument_qa_runs",
        ["field_instrument_qa_run_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_field_participant_journeys_field_instrument_qa_run_id",
        "field_participant_journeys",
        ["field_instrument_qa_run_id"],
        unique=False,
    )

    op.add_column(
        "field_journey_phases",
        sa.Column(
            "experience_arc_key",
            sa.String(length=64),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "field_journey_phases",
        sa.Column(
            "experience_arc_title",
            sa.String(length=128),
            nullable=False,
            server_default="",
        ),
    )


def downgrade() -> None:
    op.drop_column("field_journey_phases", "experience_arc_title")
    op.drop_column("field_journey_phases", "experience_arc_key")

    op.drop_index(
        "ix_field_participant_journeys_field_instrument_qa_run_id",
        table_name="field_participant_journeys",
    )
    op.drop_constraint("fk_field_pj_qa_run_id", "field_participant_journeys", type_="foreignkey")
    op.drop_column("field_participant_journeys", "field_instrument_qa_run_id")
    op.drop_column("field_participant_journeys", "bundle_snapshot_json")
