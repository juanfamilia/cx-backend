"""Add action_plans table for correction workflow.

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-04-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e4f5a6b7c8d9"
down_revision: Union[str, None] = "d3e4f5a6b7c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "action_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("evaluation_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("requires_reevaluation", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("reevaluation_due_date", sa.Date(), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["evaluation_id"], ["evaluations.id"]),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_action_plans_evaluation_id", "action_plans", ["evaluation_id"])
    op.create_index("ix_action_plans_company_id", "action_plans", ["company_id"])
    op.create_index("ix_action_plans_assigned_to_user_id", "action_plans", ["assigned_to_user_id"])
    op.create_index("ix_action_plans_status", "action_plans", ["status"])
    op.create_index("ix_action_plans_due_date", "action_plans", ["due_date"])


def downgrade() -> None:
    op.drop_index("ix_action_plans_due_date", "action_plans")
    op.drop_index("ix_action_plans_status", "action_plans")
    op.drop_index("ix_action_plans_assigned_to_user_id", "action_plans")
    op.drop_index("ix_action_plans_company_id", "action_plans")
    op.drop_index("ix_action_plans_evaluation_id", "action_plans")
    op.drop_table("action_plans")
