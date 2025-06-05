"""add isboolan to form

Revision ID: 877007ff425a
Revises: 581ee3b618fb
Create Date: 2025-06-03 08:24:18.418178

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = "877007ff425a"
down_revision: Union[str, None] = "581ee3b618fb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar la columna con un valor por defecto
    op.add_column(
        "survey_aspects",
        sa.Column(
            "is_boolean", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )

    # Modificar 'maximum_score' si es necesario
    op.alter_column(
        "survey_aspects", "maximum_score", existing_type=sa.INTEGER(), nullable=True
    )

    # Eliminar el valor por defecto después de agregar la columna para futuras inserciones
    op.alter_column("survey_aspects", "is_boolean", server_default=None)


def downgrade() -> None:
    # Revertir los cambios
    op.alter_column(
        "survey_aspects", "maximum_score", existing_type=sa.INTEGER(), nullable=False
    )
    op.drop_column("survey_aspects", "is_boolean")
