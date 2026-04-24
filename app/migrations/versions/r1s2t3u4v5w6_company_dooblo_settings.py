"""company_dooblo_settings: credenciales SurveyToGo/Dooblo por empresa (Field)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "r1s2t3u4v5w6"
down_revision: Union[str, None] = "q8r9s0t1u2v3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "company_dooblo_settings",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("base_url", sa.String(length=512), nullable=False, server_default="https://api.dooblo.net/newapi"),
        sa.Column("api_user", sa.String(length=512), nullable=False, server_default=""),
        sa.Column("password_ciphertext", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_company_dooblo_settings_company_id",
        "company_dooblo_settings",
        ["company_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_company_dooblo_settings_company_id", table_name="company_dooblo_settings")
    op.drop_table("company_dooblo_settings")
