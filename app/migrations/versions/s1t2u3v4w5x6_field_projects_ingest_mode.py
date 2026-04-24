"""field_projects: ingest_mode (csv | dooblo) declarado al crear el proyecto."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "s1t2u3v4w5x6"
down_revision: Union[str, None] = "r1s2t3u4v5w6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "field_projects",
        sa.Column(
            "ingest_mode",
            sa.String(length=32),
            server_default="csv",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("field_projects", "ingest_mode")
