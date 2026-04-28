"""field_studies: column external_ref (align ORM with DB).

Revision ID: v4w5x6y7z8a9
Revises: u3v4w5x6y7z8
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "v4w5x6y7z8a9"
down_revision: Union[str, None] = "u3v4w5x6y7z8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "field_studies",
        sa.Column("external_ref", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("field_studies", "external_ref")
