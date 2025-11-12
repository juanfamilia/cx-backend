"""add widgets, dashboard_widgets, onboarding_status tables

Revision ID: 246e347a5be0
Revises: 2e7789d68b6a
Create Date: 2025-11-12 14:40:05.018208

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '246e347a5be0'
down_revision: Union[str, None] = '2e7789d68b6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
