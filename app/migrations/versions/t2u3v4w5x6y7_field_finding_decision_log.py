"""field_finding_decision_logs: historial auditable de decisiones sobre hallazgos Field."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "t2u3v4w5x6y7"
down_revision: Union[str, None] = "s1t2u3v4w5x6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "field_finding_decision_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("field_project_id", sa.Integer(), nullable=False),
        sa.Column("field_finding_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=True),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["field_finding_id"], ["field_findings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_project_id"], ["field_projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_field_finding_decision_logs_company_id",
        "field_finding_decision_logs",
        ["company_id"],
    )
    op.create_index(
        "ix_field_finding_decision_logs_field_project_id",
        "field_finding_decision_logs",
        ["field_project_id"],
    )
    op.create_index(
        "ix_field_finding_decision_logs_field_finding_id",
        "field_finding_decision_logs",
        ["field_finding_id"],
    )
    op.create_index(
        "ix_field_finding_decision_logs_actor_user_id",
        "field_finding_decision_logs",
        ["actor_user_id"],
    )


def downgrade() -> None:
    op.drop_table("field_finding_decision_logs")
