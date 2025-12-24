"""seed_do_zones

Revision ID: 184970aba55c
Revises: f7236061f41c
Create Date: 2025-12-24 20:22:11.293979
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.sql import text


revision: str = "184970aba55c"
down_revision: Union[str, None] = "f7236061f41c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Sembrar zonas base para DO sin tocar las existentes (ids 1 y 2)
    conn.execute(
        text(
            """
            INSERT INTO zones (id, name, value, country)
            VALUES
                (3, 'Distrito Nacional', 'DN', 'DO'),
                (4, 'Santo Domingo', 'SD', 'DO'),
                (5, 'Santiago', 'STGO', 'DO')
            ON CONFLICT (id) DO UPDATE
            SET
                name = EXCLUDED.name,
                value = EXCLUDED.value,
                country = EXCLUDED.country;
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    # Solo borrar las zonas creadas por esta migración
    conn.execute(text("DELETE FROM zones WHERE id IN (3,4,5);"))
