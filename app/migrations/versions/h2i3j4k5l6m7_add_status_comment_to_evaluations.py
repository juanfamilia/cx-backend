"""Add status_comment to evaluations so evaluators can see reviewer feedback.

Revision ID: h2i3j4k5l6m7
Revises: g1h2i3j4k5l6
Create Date: 2026-04-13

"""

from typing import Sequence, Union

from alembic import op

revision: str = "h2i3j4k5l6m7"
down_revision: Union[str, None] = "g1h2i3j4k5l6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS status_comment TEXT;"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE evaluations DROP COLUMN IF EXISTS status_comment;"
    )
