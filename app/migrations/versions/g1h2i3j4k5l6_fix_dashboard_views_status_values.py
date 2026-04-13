"""Fix dashboard views to use current Spanish status values.

The original views (3825ab663ce2) filtered by uppercase English status values
('APROVED', 'REJECTED', 'EDIT', 'SEND', 'UPDATED') but StatusEnum now stores
lowercase Spanish values ('aprobado', 'rechazado', 'editar', 'enviado',
'actualizado'). This caused all counters on the evaluator dashboard to show 0.

Revision ID: g1h2i3j4k5l6
Revises: f5a6b7c8d9e0
Create Date: 2026-04-13

"""

from typing import Sequence, Union

from alembic import op

revision: str = "g1h2i3j4k5l6"
down_revision: Union[str, None] = "f5a6b7c8d9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_user_evaluation_summary = """
CREATE OR REPLACE VIEW user_evaluation_summary AS
SELECT
    user_id,
    COUNT(*) FILTER (WHERE status::text IN ('REJECTED', 'rechazado'))   AS rechazadas,
    COUNT(*) FILTER (WHERE status::text IN ('APROVED',  'aprobado'))    AS aprobadas,
    COUNT(*) FILTER (WHERE status::text IN ('EDIT',     'editar'))      AS ediciones_pendientes,
    COUNT(*) FILTER (WHERE status::text IN ('SEND',     'enviado'))     AS enviadas,
    COUNT(*) FILTER (WHERE status::text IN ('UPDATED',  'actualizado')) AS actualizadas
FROM evaluations
WHERE evaluations.deleted_at IS NULL
GROUP BY user_id;
"""

_company_users_evaluations = """
CREATE OR REPLACE VIEW company_users_evaluations AS
SELECT
    u.company_id,
    COUNT(*) FILTER (WHERE u.role = 2 AND u.deleted_at IS NULL)                                              AS gerentes,
    COUNT(*) FILTER (WHERE u.role = 3 AND u.deleted_at IS NULL)                                              AS evaluadores,
    COUNT(*) FILTER (WHERE e.status::text IN ('APROVED', 'aprobado')  AND e.deleted_at IS NULL)              AS evaluaciones_aprobadas,
    COUNT(*) FILTER (WHERE e.status::text IN ('REJECTED', 'rechazado') AND e.deleted_at IS NULL)             AS evaluaciones_rechazadas
FROM users u
LEFT JOIN evaluations e ON u.id = e.user_id
GROUP BY u.company_id;
"""


_drop_any = """
DO $$
DECLARE
    obj_type char;
BEGIN
    -- Drop user_evaluation_summary regardless of whether it is a TABLE or VIEW
    SELECT relkind INTO obj_type
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relname = 'user_evaluation_summary' AND n.nspname = 'public';

    IF obj_type = 'r' THEN
        DROP TABLE user_evaluation_summary CASCADE;
    ELSIF obj_type = 'v' THEN
        DROP VIEW user_evaluation_summary CASCADE;
    END IF;

    -- Drop company_users_evaluations regardless of whether it is a TABLE or VIEW
    SELECT relkind INTO obj_type
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relname = 'company_users_evaluations' AND n.nspname = 'public';

    IF obj_type = 'r' THEN
        DROP TABLE company_users_evaluations CASCADE;
    ELSIF obj_type = 'v' THEN
        DROP VIEW company_users_evaluations CASCADE;
    END IF;
END $$;
"""


def upgrade() -> None:
    # Safely drop objects regardless of their type (TABLE vs VIEW) in each env
    op.execute(_drop_any)
    op.execute(_user_evaluation_summary)
    op.execute(_company_users_evaluations)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS user_evaluation_summary CASCADE;")
    op.execute("DROP VIEW IF EXISTS company_users_evaluations CASCADE;")
    # Restore original views that only matched uppercase English values
    op.execute(
        """
        CREATE OR REPLACE VIEW user_evaluation_summary AS
        SELECT
            user_id,
            COUNT(*) FILTER (WHERE status::text = 'REJECTED') AS rechazadas,
            COUNT(*) FILTER (WHERE status::text = 'APROVED')  AS aprobadas,
            COUNT(*) FILTER (WHERE status::text = 'EDIT')     AS ediciones_pendientes,
            COUNT(*) FILTER (WHERE status::text = 'SEND')     AS enviadas,
            COUNT(*) FILTER (WHERE status::text = 'UPDATED')  AS actualizadas
        FROM evaluations
        WHERE evaluations.deleted_at IS NULL
        GROUP BY user_id;
        """
    )
    op.execute(
        """
        CREATE OR REPLACE VIEW company_users_evaluations AS
        SELECT
            u.company_id,
            COUNT(*) FILTER (WHERE u.role = 2 AND u.deleted_at IS NULL)                            AS gerentes,
            COUNT(*) FILTER (WHERE u.role = 3 AND u.deleted_at IS NULL)                            AS evaluadores,
            COUNT(*) FILTER (WHERE e.status = 'APROVED'  AND e.deleted_at IS NULL)                 AS evaluaciones_aprobadas,
            COUNT(*) FILTER (WHERE e.status = 'REJECTED' AND e.deleted_at IS NULL)                 AS evaluaciones_rechazadas
        FROM users u
        LEFT JOIN evaluations e ON u.id = e.user_id
        GROUP BY u.company_id;
        """
    )
