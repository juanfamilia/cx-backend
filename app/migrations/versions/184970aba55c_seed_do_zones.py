"""seed_do_zones

Revision ID: 184970aba55c
Revises: f7236061f41c
Create Date: 2025-12-24 20:22:11.293979

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text  # <= útil para SQL crudo


revision: str = "184970aba55c"
down_revision: Union[str, None] = "f7236061f41c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ejemplo: insertar provincias si no existen
    conn.execute(
        text(
            """
            INSERT INTO provinces (id, name)
            VALUES
                (1, 'Distrito Nacional'),
                (2, 'Santo Domingo')
            ON CONFLICT (id) DO UPDATE
            SET name = EXCLUDED.name;
            """
        )
    )

    # ejemplo: insertar zonas ligadas a provincias
    conn.execute(
        text(
            """
            INSERT INTO zones (id, name, province_id)
            VALUES
                (1, 'Zona 1', 1),
                (2, 'Zona 2', 1),
                (3, 'Zona 3', 2)
            ON CONFLICT (id) DO UPDATE
            SET
                name = EXCLUDED.name,
                province_id = EXCLUDED.province_id;
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DELETE FROM zones WHERE id IN (1,2,3);"))
    conn.execute(text("DELETE FROM provinces WHERE id IN (1,2);"))
