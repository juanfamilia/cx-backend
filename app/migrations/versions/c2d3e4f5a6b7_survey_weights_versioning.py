"""Add weights, new aspect types, versioning to survey forms/sections/aspects.

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-04-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- survey_forms: versionado ---
    op.add_column("survey_forms", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("survey_forms", sa.Column("parent_form_id", sa.Integer(), nullable=True))
    op.add_column("survey_forms", sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"))
    op.create_foreign_key(
        "fk_survey_forms_parent_form_id",
        "survey_forms", "survey_forms",
        ["parent_form_id"], ["id"],
    )

    # --- survey_sections: peso ---
    op.add_column("survey_sections", sa.Column("weight", sa.Float(), nullable=True))

    # --- survey_aspects: peso, requires_evidence, nuevos tipos ---
    op.add_column("survey_aspects", sa.Column("weight", sa.Float(), nullable=True))
    op.add_column("survey_aspects", sa.Column("requires_evidence", sa.Boolean(), nullable=False, server_default="false"))

    # Ampliar el enum de tipo de aspecto con los nuevos valores
    op.execute("ALTER TYPE aspecttypeenum ADD VALUE IF NOT EXISTS 'likert'")
    op.execute("ALTER TYPE aspecttypeenum ADD VALUE IF NOT EXISTS 'compliance'")
    op.execute("ALTER TYPE aspecttypeenum ADD VALUE IF NOT EXISTS 'media'")


def downgrade() -> None:
    op.drop_column("survey_aspects", "requires_evidence")
    op.drop_column("survey_aspects", "weight")
    op.drop_column("survey_sections", "weight")
    op.drop_constraint("fk_survey_forms_parent_form_id", "survey_forms", type_="foreignkey")
    op.drop_column("survey_forms", "is_active")
    op.drop_column("survey_forms", "parent_form_id")
    op.drop_column("survey_forms", "version")
    # Nota: PostgreSQL no permite eliminar valores de un enum sin recrearlo.
    # El downgrade no revierte los nuevos valores del enum.
