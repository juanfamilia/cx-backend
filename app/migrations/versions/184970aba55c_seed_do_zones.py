"""seed_do_zones

Revision ID: 184970aba55c
Revises: f7236061f41c
Create Date: 2025-12-24 20:22:11.293979

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '184970aba55c'
down_revision: Union[str, None] = 'f7236061f41c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
