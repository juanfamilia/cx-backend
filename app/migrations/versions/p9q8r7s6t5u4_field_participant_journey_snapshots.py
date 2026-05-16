"""field_participant_journeys + field_journey_phases — Study Intelligence P2.

Revision ID: p9q8r7s6t5u4
Revises: n4m3l2k1j0i9
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "p9q8r7s6t5u4"
down_revision: Union[str, None] = "n4m3l2k1j0i9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "field_participant_journeys",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("revision_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("study_id", sa.Integer(), nullable=False),
        sa.Column("instrument_spec_content_hash", sa.String(length=128), nullable=False),
        sa.Column("brief_snapshot_hash", sa.String(length=128), nullable=True),
        sa.Column("framework_catalog_version", sa.String(length=32), nullable=True),
        sa.Column("engine_version", sa.String(length=64), nullable=False),
        sa.Column(
            "ruleset_versions_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "contextual_scores_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["revision_id"], ["field_instrument_revisions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["study_id"], ["field_studies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "revision_id",
            "instrument_spec_content_hash",
            name="uq_field_pj_revision_spec_hash",
        ),
    )
    op.create_index(
        "ix_field_participant_journeys_revision_id",
        "field_participant_journeys",
        ["revision_id"],
        unique=False,
    )
    op.create_index(
        "ix_field_participant_journeys_study_id",
        "field_participant_journeys",
        ["study_id"],
        unique=False,
    )

    op.create_table(
        "field_journey_phases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("participant_journey_id", sa.Integer(), nullable=False),
        sa.Column("phase_key", sa.String(length=64), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("narrative_summary", sa.Text(), nullable=True),
        sa.Column(
            "block_ids_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.ForeignKeyConstraint(
            ["participant_journey_id"],
            ["field_participant_journeys.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_field_journey_phases_participant_journey_id",
        "field_journey_phases",
        ["participant_journey_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_field_journey_phases_participant_journey_id", table_name="field_journey_phases")
    op.drop_table("field_journey_phases")
    op.drop_index("ix_field_participant_journeys_study_id", table_name="field_participant_journeys")
    op.drop_index("ix_field_participant_journeys_revision_id", table_name="field_participant_journeys")
    op.drop_table("field_participant_journeys")
