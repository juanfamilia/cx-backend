"""Repara esquema si quedó desincronizado (visited_zones, vistas de metas).

Casos típicos: alembic_version avanzada sin aplicar DDL, o BD restaurada.

Revision ID: c9012d3e4f5a
Revises: 184970aba55c
Create Date: 2026-04-08

"""

from typing import Sequence, Union

from alembic import op

revision: str = "c9012d3e4f5a"
down_revision: Union[str, None] = "184970aba55c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Misma definición que ef9230c16ca4_user_dashboard_views.py
_campaign_goals_weekly_progress = """
CREATE OR REPLACE VIEW public.campaign_goals_weekly_progress AS
WITH week_days AS (
  SELECT (date_trunc('week', CURRENT_DATE) + s.i * interval '1 day')::date AS day_date
  FROM generate_series(0, 6) s(i)
  WHERE EXTRACT(ISODOW FROM (date_trunc('week', CURRENT_DATE) + s.i * interval '1 day')) < 6
),
daily_reports AS (
  SELECT
    cge.evaluator_id,
    wd.day_date,
    to_char(wd.day_date, 'Day') AS day_name,
    SUM(COALESCE(cge.goal, 0)) AS goal_weekly,
    ROUND(SUM(COALESCE(cge.goal, 0))::numeric / 5.0, 2) AS daily_goal,
    COUNT(ev.id) AS reported_today
  FROM campaign_goals_evaluators cge
  JOIN campaigns c ON c.id = cge.campaign_id
  CROSS JOIN week_days wd
  LEFT JOIN evaluations ev
    ON ev.campaigns_id = c.id
   AND ev.user_id = cge.evaluator_id
   AND ev.deleted_at IS NULL
   AND ev.status = 'APROVED'
   AND ev.created_at::date = wd.day_date
  WHERE CURRENT_DATE BETWEEN c.date_start AND c.date_end
  GROUP BY cge.evaluator_id, wd.day_date
)
SELECT *
FROM daily_reports
ORDER BY evaluator_id, day_date;
"""

_campaign_goals_coverage = """
CREATE OR REPLACE VIEW campaign_goals_coverage AS
SELECT
    cge.campaign_id,
    c.name AS campaign_name,
    cge.evaluator_id,
    cge.goal AS goal_weekly,
    COUNT(ev.id) AS reported_total,
    ROUND((COUNT(ev.id)::decimal / cge.goal) * 100, 2) AS coverage_percent
FROM campaign_goals_evaluators cge
JOIN campaigns c ON c.id = cge.campaign_id
LEFT JOIN evaluations ev
    ON ev.campaigns_id = c.id
   AND ev.user_id = cge.evaluator_id
   AND ev.deleted_at IS NULL
   AND ev.status = 'APROVED'
   AND DATE_TRUNC('week', ev.created_at) = DATE_TRUNC('week', CURRENT_DATE)
   AND EXTRACT(ISODOW FROM ev.created_at) < 6
GROUP BY
    cge.campaign_id, c.name, cge.evaluator_id, cge.goal;
"""


def upgrade() -> None:
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS visited_zones INTEGER[];"
    )
    op.execute(_campaign_goals_weekly_progress)
    op.execute(_campaign_goals_coverage)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS campaign_goals_weekly_progress;")
    op.execute("DROP VIEW IF EXISTS campaign_goals_coverage;")
    op.execute("ALTER TABLE evaluations DROP COLUMN IF EXISTS visited_zones;")
