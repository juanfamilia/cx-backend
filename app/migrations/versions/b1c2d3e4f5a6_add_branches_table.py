"""Add branches table and branch_fk_id to evaluations.

Revision ID: b1c2d3e4f5a6
Revises: a7b8c9d0e1f2
Create Date: 2026-04-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "branches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("zone_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("country", sa.String(), nullable=False, server_default="DO"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_branches_company_id", "branches", ["company_id"])
    op.create_index("ix_branches_zone_id", "branches", ["zone_id"])
    op.create_index("ix_branches_name", "branches", ["name"])
    op.create_index("ix_branches_code", "branches", ["code"])
    # Unique code per company
    op.create_index(
        "uq_branches_company_code", "branches", ["company_id", "code"], unique=True
    )

    # FK en evaluations (nullable, backward-compatible)
    op.add_column(
        "evaluations",
        sa.Column("branch_fk_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_evaluations_branch_fk_id",
        "evaluations",
        "branches",
        ["branch_fk_id"],
        ["id"],
    )
    op.create_index("ix_evaluations_branch_fk_id", "evaluations", ["branch_fk_id"])


def downgrade() -> None:
    op.drop_index("ix_evaluations_branch_fk_id", "evaluations")
    op.drop_constraint("fk_evaluations_branch_fk_id", "evaluations", type_="foreignkey")
    op.drop_column("evaluations", "branch_fk_id")

    op.drop_index("uq_branches_company_code", "branches")
    op.drop_index("ix_branches_code", "branches")
    op.drop_index("ix_branches_name", "branches")
    op.drop_index("ix_branches_zone_id", "branches")
    op.drop_index("ix_branches_company_id", "branches")
    op.drop_table("branches")
