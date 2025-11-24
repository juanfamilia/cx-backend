"""merge heads for unified migration

Revision ID: f10d72303278
Revises: 20251117_phase04, fd400e2f4e52
Create Date: 2025-11-24 12:32:46.416283

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = 'f10d72303278'
down_revision: Union[str, None] = ('20251117_phase04', 'fd400e2f4e52')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
