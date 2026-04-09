"""Añade transcript_text a evaluation_analysis (modelo sin migración previa).

Revision ID: a7b8c9d0e1f2
Revises: f1e2d3c4b5a6
Create Date: 2026-04-09

"""

from typing import Sequence, Union

from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "f1e2d3c4b5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE evaluation_analysis ADD COLUMN IF NOT EXISTS transcript_text TEXT;"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE evaluation_analysis DROP COLUMN IF EXISTS transcript_text;"
    )
