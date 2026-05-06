"""company_qualtrics_settings: credenciales Qualtrics XM API por empresa (Field)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "z9y8x7w6v5u4"
down_revision: Union[str, None] = "x1y2z3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "company_qualtrics_settings",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("base_url", sa.String(length=512), nullable=False),
        sa.Column("api_token_ciphertext", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_company_qualtrics_settings_company_id",
        "company_qualtrics_settings",
        ["company_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_company_qualtrics_settings_company_id", table_name="company_qualtrics_settings")
    op.drop_table("company_qualtrics_settings")
