"""add company integration fields

Revision ID: f7236061f41c
Revises: f10d72303278
Create Date: 2025-12-22 20:34:00.675041
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision: str = "f7236061f41c"
down_revision: Union[str, None] = "f10d72303278"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column(
            "slack_webhook_url",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
        ),
    )
    op.add_column(
        "companies",
        sa.Column(
            "webhook_url",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
        ),
    )
    op.add_column(
        "companies",
        sa.Column(
            "webhook_secret",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("companies", "webhook_secret")
    op.drop_column("companies", "webhook_url")
    op.drop_column("companies", "slack_webhook_url")
