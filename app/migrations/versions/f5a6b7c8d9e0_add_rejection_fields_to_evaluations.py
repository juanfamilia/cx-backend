"""Add rejection_type and requires_revisit to evaluations.

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-04-13

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f5a6b7c8d9e0"
down_revision: Union[str, None] = "e4f5a6b7c8d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # rejection_type: 'descartado' | 'discrepancia' — solo relevante cuando status=REJECTED
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS rejection_type VARCHAR;"
    )
    # requires_revisit: se debe generar una nueva visita
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS requires_revisit BOOLEAN NOT NULL DEFAULT FALSE;"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE evaluations DROP COLUMN IF EXISTS requires_revisit;")
    op.execute("ALTER TABLE evaluations DROP COLUMN IF EXISTS rejection_type;")
