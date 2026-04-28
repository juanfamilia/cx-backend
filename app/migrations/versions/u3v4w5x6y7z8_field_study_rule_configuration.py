"""field_studies, rule configuration packs/versions; field_projects.study_id; findings QA refs.

Revision ID: u3v4w5x6y7z8
Revises: t2u3v4w5x6y7
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "u3v4w5x6y7z8"
down_revision: Union[str, None] = "t2u3v4w5x6y7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "field_studies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["client_id"], ["end_clients.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_field_studies_company_id", "field_studies", ["company_id"], unique=False)
    op.create_index("ix_field_studies_client_id", "field_studies", ["client_id"], unique=False)

    op.create_table(
        "field_rule_configuration_packs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("pack_kind", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "slug", name="uq_field_rule_pack_company_slug"),
    )
    op.create_index(
        "ix_field_rule_configuration_packs_company_id",
        "field_rule_configuration_packs",
        ["company_id"],
        unique=False,
    )

    op.create_table(
        "field_rule_configuration_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pack_id", sa.Integer(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("effective_from", sa.DateTime(), nullable=False),
        sa.Column("effective_to", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["approved_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["pack_id"],
            ["field_rule_configuration_packs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pack_id", "version_number", name="uq_field_rule_version_pack_no"),
    )
    op.create_index(
        "ix_field_rule_configuration_versions_pack_id",
        "field_rule_configuration_versions",
        ["pack_id"],
        unique=False,
    )

    op.add_column(
        "field_projects",
        sa.Column("study_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_field_projects_study_id_field_studies",
        "field_projects",
        "field_studies",
        ["study_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_field_projects_study_id",
        "field_projects",
        ["study_id"],
        unique=False,
    )

    op.add_column(
        "field_findings",
        sa.Column("operational_criticality", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "field_findings",
        sa.Column("operational_gate", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "field_findings",
        sa.Column("rule_configuration_version_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_field_findings_rule_configuration_version_id",
        "field_findings",
        "field_rule_configuration_versions",
        ["rule_configuration_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_field_findings_rule_configuration_version_id",
        "field_findings",
        ["rule_configuration_version_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_field_findings_rule_configuration_version_id", table_name="field_findings"
    )
    op.drop_constraint(
        "fk_field_findings_rule_configuration_version_id",
        "field_findings",
        type_="foreignkey",
    )
    op.drop_column("field_findings", "rule_configuration_version_id")
    op.drop_column("field_findings", "operational_gate")
    op.drop_column("field_findings", "operational_criticality")

    op.drop_index("ix_field_projects_study_id", table_name="field_projects")
    op.drop_constraint(
        "fk_field_projects_study_id_field_studies", "field_projects", type_="foreignkey"
    )
    op.drop_column("field_projects", "study_id")

    op.drop_table("field_rule_configuration_versions")
    op.drop_table("field_rule_configuration_packs")
    op.drop_table("field_studies")
