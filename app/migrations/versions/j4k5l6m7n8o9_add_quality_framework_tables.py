"""Add Service Quality Framework tables.

Introduces the Service Quality model described in docs/METHODOLOGY.md:
  - industries
  - quality_frameworks
  - quality_framework_dimensions
  - quality_competencies
  - competency_indicators
  - competency_framework_refs
  - industry_templates
  - company_competency_configs

Also adds:
  - companies.industry_id (nullable FK) — assigned by superadmin per company
  - survey_aspects.competency_id (nullable FK) — links a form aspect to a
    Quality Competency so Gap Analysis can use explicit linkage instead of
    keyword heuristics.

All new FKs are nullable to preserve backward compatibility with existing
companies and surveys.

Revision ID: j4k5l6m7n8o9
Revises: i3j4k5l6m7n8
Create Date: 2026-04-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "j4k5l6m7n8o9"
down_revision: Union[str, None] = "i3j4k5l6m7n8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------------------
    # industries
    # -----------------------------------------------------------------
    op.create_table(
        "industries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_industries_code", "industries", ["code"], unique=True)

    # -----------------------------------------------------------------
    # quality_frameworks
    # -----------------------------------------------------------------
    op.create_table(
        "quality_frameworks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("authors", sa.String(length=512), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("source_citation", sa.Text(), nullable=True),
        sa.Column("url_reference", sa.String(length=512), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_quality_frameworks_code", "quality_frameworks", ["code"], unique=True
    )

    # -----------------------------------------------------------------
    # quality_framework_dimensions
    # -----------------------------------------------------------------
    op.create_table(
        "quality_framework_dimensions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("framework_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=96), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["framework_id"], ["quality_frameworks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_qfd_framework_id", "quality_framework_dimensions", ["framework_id"]
    )
    op.create_index(
        "ix_qfd_code", "quality_framework_dimensions", ["code"], unique=True
    )

    # -----------------------------------------------------------------
    # quality_competencies
    # -----------------------------------------------------------------
    op.create_table(
        "quality_competencies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=96), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column(
            "category",
            sa.String(length=32),
            nullable=False,
            server_default="ATTENTION",
        ),
        sa.Column("definition", sa.Text(), nullable=True),
        sa.Column(
            "measurement_type",
            sa.String(length=16),
            nullable=False,
            server_default="boolean",
        ),
        sa.Column(
            "default_weight",
            sa.Float(),
            nullable=False,
            server_default="1.0",
        ),
        sa.Column("ai_field_hint", sa.String(length=96), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_quality_competencies_code", "quality_competencies", ["code"], unique=True
    )

    # -----------------------------------------------------------------
    # competency_indicators
    # -----------------------------------------------------------------
    op.create_table(
        "competency_indicators",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("competency_id", sa.Integer(), nullable=False),
        sa.Column(
            "indicator_type",
            sa.String(length=16),
            nullable=False,
            server_default="positive",
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("detection_hint", sa.Text(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["competency_id"], ["quality_competencies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_comp_indicators_competency_id", "competency_indicators", ["competency_id"]
    )

    # -----------------------------------------------------------------
    # competency_framework_refs (M:N competency ↔ framework_dimension)
    # -----------------------------------------------------------------
    op.create_table(
        "competency_framework_refs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("competency_id", sa.Integer(), nullable=False),
        sa.Column("framework_dimension_id", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["competency_id"], ["quality_competencies.id"]),
        sa.ForeignKeyConstraint(
            ["framework_dimension_id"], ["quality_framework_dimensions.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cfr_competency_id", "competency_framework_refs", ["competency_id"]
    )
    op.create_index(
        "ix_cfr_dimension_id",
        "competency_framework_refs",
        ["framework_dimension_id"],
    )
    op.create_index(
        "uq_cfr_competency_dimension",
        "competency_framework_refs",
        ["competency_id", "framework_dimension_id"],
        unique=True,
    )

    # -----------------------------------------------------------------
    # industry_templates
    # -----------------------------------------------------------------
    op.create_table(
        "industry_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("industry_id", sa.Integer(), nullable=False),
        sa.Column("competency_id", sa.Integer(), nullable=False),
        sa.Column(
            "suggested_weight", sa.Float(), nullable=False, server_default="1.0"
        ),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["industry_id"], ["industries.id"]),
        sa.ForeignKeyConstraint(["competency_id"], ["quality_competencies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "industry_id",
            "competency_id",
            name="uq_industry_templates_industry_comp",
        ),
    )
    op.create_index(
        "ix_industry_templates_industry_id", "industry_templates", ["industry_id"]
    )
    op.create_index(
        "ix_industry_templates_competency_id",
        "industry_templates",
        ["competency_id"],
    )

    # -----------------------------------------------------------------
    # company_competency_configs
    # -----------------------------------------------------------------
    op.create_table(
        "company_competency_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("competency_id", sa.Integer(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("custom_weight", sa.Float(), nullable=True),
        sa.Column("custom_notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["competency_id"], ["quality_competencies.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id",
            "competency_id",
            name="uq_company_comp_config_company_comp",
        ),
    )
    op.create_index(
        "ix_ccc_company_id", "company_competency_configs", ["company_id"]
    )
    op.create_index(
        "ix_ccc_competency_id", "company_competency_configs", ["competency_id"]
    )
    op.create_index(
        "ix_ccc_created_by_user_id",
        "company_competency_configs",
        ["created_by_user_id"],
    )

    # -----------------------------------------------------------------
    # companies.industry_id (nullable, backward compatible)
    # -----------------------------------------------------------------
    op.add_column(
        "companies",
        sa.Column("industry_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_companies_industry_id",
        "companies",
        "industries",
        ["industry_id"],
        ["id"],
    )
    op.create_index("ix_companies_industry_id", "companies", ["industry_id"])

    # -----------------------------------------------------------------
    # survey_aspects.competency_id (nullable, backward compatible)
    # -----------------------------------------------------------------
    op.add_column(
        "survey_aspects",
        sa.Column("competency_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_survey_aspects_competency_id",
        "survey_aspects",
        "quality_competencies",
        ["competency_id"],
        ["id"],
    )
    op.create_index(
        "ix_survey_aspects_competency_id", "survey_aspects", ["competency_id"]
    )


def downgrade() -> None:
    # survey_aspects.competency_id
    op.drop_index("ix_survey_aspects_competency_id", "survey_aspects")
    op.drop_constraint(
        "fk_survey_aspects_competency_id", "survey_aspects", type_="foreignkey"
    )
    op.drop_column("survey_aspects", "competency_id")

    # companies.industry_id
    op.drop_index("ix_companies_industry_id", "companies")
    op.drop_constraint("fk_companies_industry_id", "companies", type_="foreignkey")
    op.drop_column("companies", "industry_id")

    # company_competency_configs
    op.drop_index("ix_ccc_created_by_user_id", "company_competency_configs")
    op.drop_index("ix_ccc_competency_id", "company_competency_configs")
    op.drop_index("ix_ccc_company_id", "company_competency_configs")
    op.drop_table("company_competency_configs")

    # industry_templates
    op.drop_index("ix_industry_templates_competency_id", "industry_templates")
    op.drop_index("ix_industry_templates_industry_id", "industry_templates")
    op.drop_table("industry_templates")

    # competency_framework_refs
    op.drop_index("uq_cfr_competency_dimension", "competency_framework_refs")
    op.drop_index("ix_cfr_dimension_id", "competency_framework_refs")
    op.drop_index("ix_cfr_competency_id", "competency_framework_refs")
    op.drop_table("competency_framework_refs")

    # competency_indicators
    op.drop_index("ix_comp_indicators_competency_id", "competency_indicators")
    op.drop_table("competency_indicators")

    # quality_competencies
    op.drop_index("ix_quality_competencies_code", "quality_competencies")
    op.drop_table("quality_competencies")

    # quality_framework_dimensions
    op.drop_index("ix_qfd_code", "quality_framework_dimensions")
    op.drop_index("ix_qfd_framework_id", "quality_framework_dimensions")
    op.drop_table("quality_framework_dimensions")

    # quality_frameworks
    op.drop_index("ix_quality_frameworks_code", "quality_frameworks")
    op.drop_table("quality_frameworks")

    # industries
    op.drop_index("ix_industries_code", "industries")
    op.drop_table("industries")
