"""PRE-FIELD gobierno: brief por estudio, lineage en revisión, waivers, gate brief Readiness.

Revision ID: n4m3l2k1j0i9
Revises: z1y2x3w4v5u6
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "n4m3l2k1j0i9"
down_revision: Union[str, None] = "z1y2x3w4v5u6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_EMPTY_OBJECT_CANONICAL_HASH = (
    "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"
)


def upgrade() -> None:
    op.add_column(
        "field_studies",
        sa.Column("primary_language", sa.String(length=16), nullable=True),
    )

    op.create_table(
        "field_study_brief",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("study_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column(
            "payload_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("completeness_score", sa.Double(), nullable=True),
        sa.Column(
            "approval_state",
            sa.String(length=32),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("approved_internal_user_id", sa.Integer(), nullable=True),
        sa.Column("approved_internal_at", sa.DateTime(), nullable=True),
        sa.Column("approved_client_user_id", sa.Integer(), nullable=True),
        sa.Column("approved_client_at", sa.DateTime(), nullable=True),
        sa.Column(
            "body_hash",
            sa.String(length=128),
            nullable=False,
            server_default=_EMPTY_OBJECT_CANONICAL_HASH,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["study_id"], ["field_studies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approved_internal_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["approved_client_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("study_id", name="uq_field_study_brief_study_id"),
    )
    op.create_index("ix_field_study_brief_company_id", "field_study_brief", ["company_id"])

    op.execute(
        f"""
            INSERT INTO field_study_brief (
                study_id, company_id, payload_json, body_hash, approval_state
            )
            SELECT id, company_id, '{{}}'::jsonb, '{_EMPTY_OBJECT_CANONICAL_HASH}', 'draft'
            FROM field_studies
            """
    )

    op.add_column(
        "field_instrument_revisions",
        sa.Column(
            "brief_snapshot_hash",
            sa.String(length=128),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "field_instrument_revisions",
        sa.Column("framework_catalog_version", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "field_instrument_revisions",
        sa.Column("last_ruleset_version", sa.String(length=64), nullable=True),
    )

    op.create_table(
        "field_framework_waivers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("instrument_revision_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column(
            "waived_sections_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["instrument_revision_id"],
            ["field_instrument_revisions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_field_framework_waivers_revision_id",
        "field_framework_waivers",
        ["instrument_revision_id"],
    )
    op.create_index(
        "ix_field_framework_waivers_company_id",
        "field_framework_waivers",
        ["company_id"],
    )

    op.add_column(
        "company_field_readiness_policy",
        sa.Column(
            "require_brief_approved",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("company_field_readiness_policy", "require_brief_approved")
    op.drop_index("ix_field_framework_waivers_company_id", table_name="field_framework_waivers")
    op.drop_index("ix_field_framework_waivers_revision_id", table_name="field_framework_waivers")
    op.drop_table("field_framework_waivers")
    op.drop_column("field_instrument_revisions", "last_ruleset_version")
    op.drop_column("field_instrument_revisions", "framework_catalog_version")
    op.drop_column("field_instrument_revisions", "brief_snapshot_hash")
    op.drop_index("ix_field_study_brief_company_id", table_name="field_study_brief")
    op.drop_table("field_study_brief")
    op.drop_column("field_studies", "primary_language")
