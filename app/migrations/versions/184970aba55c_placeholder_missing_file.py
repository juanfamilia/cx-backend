"""Placeholder: revision present in production alembic_version but file was missing from repo.

If this down_revision is wrong for your history, fix alembic_version in Postgres instead, e.g.:
  UPDATE alembic_version SET version_num = 'f0a1b2c3d4e5';
then run alembic upgrade head after reviewing schema.

Revision ID: 184970aba55c
Revises: f0a1b2c3d4e5
Create Date: 2026-04-05

"""

from typing import Sequence, Union

from alembic import op

revision: str = "184970aba55c"
down_revision: Union[str, None] = "f0a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ya aplicado en la BD de Railway (u operación vacía); no repetir DDL aquí.
    pass


def downgrade() -> None:
    pass
