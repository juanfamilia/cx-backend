"""Merge heads: manager and widgets-migration

Revision ID: 2e7789d68b6a
Revises: add_prompt_manager, c9082924ebb0
Create Date: 2025-11-12 12:57:02.451368

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '2e7789d68b6a'
down_revision: Union[str, None] = ('add_prompt_manager', 'c9082924ebb0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
