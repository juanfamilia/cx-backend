"""Add mananger dashboard view

Revision ID: 3825ab663ce2
Revises: dd8e4c7a1f3d
Create Date: 2025-06-16 12:12:17.722677

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = "3825ab663ce2"
down_revision: Union[str, None] = "cd599382fbd5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

manager_summary_sql = """
CREATE VIEW manager_summary AS
SELECT 
    u.id AS user_id,
    u.company_id,
    COUNT(uz.zone_id) AS zonas_asignadas,
    COUNT(DISTINCT e.id) AS evaluadores_asignados,
    COUNT(DISTINCT c.id) AS active_campaigns
FROM users u
LEFT JOIN user_zones uz ON u.id = uz.user_id AND uz.deleted_at IS NULL
LEFT JOIN users e ON e.role = 3 AND e.company_id = u.company_id AND e.deleted_at IS NULL 
                   AND EXISTS (SELECT 1 FROM user_zones ez WHERE ez.user_id = e.id AND ez.zone_id = uz.zone_id AND ez.deleted_at IS NULL)
LEFT JOIN campaigns c ON c.company_id = u.company_id AND c.date_end > NOW() AND c.deleted_at IS NULL
WHERE u.role = 2 AND u.deleted_at IS NULL
GROUP BY u.id, u.company_id;
"""

user_evaluation_summary_sql = """
CREATE VIEW user_evaluation_summary AS
SELECT 
    user_id,
    COUNT(*) FILTER (WHERE status::text = 'REJECTED') AS rechazadas,
    COUNT(*) FILTER (WHERE status::text = 'APROVED') AS aprobadas,
    COUNT(*) FILTER (WHERE status::text = 'EDIT') AS ediciones_pendientes,
    COUNT(*) FILTER (WHERE status::text = 'SEND') AS enviadas,
    COUNT(*) FILTER (WHERE status::text = 'UPDATED') AS actualizadas
FROM evaluations
WHERE evaluations.deleted_at IS NULL
GROUP BY user_id;
"""

company_users_evaluations_sql = """
CREATE VIEW company_users_evaluations AS
SELECT 
    u.company_id,
    COUNT(*) FILTER (WHERE u.role = 2 AND u.deleted_at IS NULL) AS gerentes,
    COUNT(*) FILTER (WHERE u.role = 3 AND u.deleted_at IS NULL) AS evaluadores,
    COUNT(*) FILTER (WHERE e.status = 'APROVED' AND e.deleted_at IS NULL) AS evaluaciones_aprobadas,
    COUNT(*) FILTER (WHERE e.status = 'REJECTED' AND e.deleted_at IS NULL) AS evaluaciones_rechazadas
FROM users u
LEFT JOIN evaluations e ON u.id = e.user_id
GROUP BY u.company_id;
"""


def upgrade() -> None:
    op.execute(manager_summary_sql)
    op.execute(user_evaluation_summary_sql)
    op.execute(company_users_evaluations_sql)


def downgrade() -> None:
    op.execute("DROP VIEW manager_summary;")
    op.execute("DROP VIEW user_evaluation_summary;")
    op.execute("DROP VIEW company_users_evaluations;")
