"""Add superadmin dashboard view

Revision ID: b1a2aa01b976
Revises: 3825ab663ce2
Create Date: 2025-06-16 12:43:10.092735

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = "b1a2aa01b976"
down_revision: Union[str, None] = "3825ab663ce2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

view_sql = """
CREATE VIEW superadmin_summary AS
WITH latest_payments AS (
    SELECT DISTINCT ON (company_id) company_id, valid_before
    FROM payments
    WHERE deleted_at IS NULL
    ORDER BY company_id, valid_before DESC
),
superadmin_user AS (
    SELECT id AS superadmin_id
    FROM users
    WHERE role = 0 AND deleted_at IS NULL
    LIMIT 1
)
SELECT 
    sa.superadmin_id,
    COUNT(DISTINCT c.id) AS total_empresas,
    COUNT(DISTINCT lp.company_id) FILTER (WHERE lp.valid_before > NOW()) AS empresas_vigentes,
    COUNT(DISTINCT lp.company_id) FILTER (WHERE lp.valid_before <= NOW()) AS empresas_caducadas,
    COUNT(DISTINCT u.id) AS usuarios_totales
FROM companies c
LEFT JOIN latest_payments lp ON c.id = lp.company_id
LEFT JOIN users u ON u.company_id = c.id AND u.role != 0 AND u.deleted_at IS NULL
CROSS JOIN superadmin_user sa
WHERE c.deleted_at IS NULL
GROUP BY sa.superadmin_id;
"""


def upgrade() -> None:
    op.execute(view_sql)


def downgrade() -> None:
    op.execute("DROP VIEW superadmin_summary;")
