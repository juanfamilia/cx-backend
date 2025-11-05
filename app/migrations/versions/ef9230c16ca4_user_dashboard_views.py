"""user dashboard views

Revision ID: ef9230c16ca4
Revises: bb9c6359b94f
Create Date: 2025-11-04 22:14:41.421580

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = "ef9230c16ca4"
down_revision: Union[str, None] = "bb9c6359b94f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

campaign_goals_weekly_progress = """
CREATE OR REPLACE VIEW campaign_goals_weekly_progress AS
WITH week_days AS (
    SELECT 
        (DATE_TRUNC('week', CURRENT_DATE) + i * INTERVAL '1 day')::date AS day_date
    FROM generate_series(0, 6) AS s(i)
)
SELECT
    cge.campaign_id,
    c.name AS campaign_name,
    cge.evaluator_id,
    TO_CHAR(wd.day_date, 'Day') AS day_name,
    wd.day_date,
    cge.goal AS goal_weekly,
    ROUND(cge.goal / 7.0, 2) AS daily_goal,
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
GROUP BY
    cge.campaign_id,
    c.name,
    cge.evaluator_id,
    wd.day_date,
    cge.goal
ORDER BY
    cge.evaluator_id,
    wd.day_date;    
"""

campaign_goals_coverage = """
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
GROUP BY
    cge.campaign_id, c.name, cge.evaluator_id, cge.goal;
"""


def upgrade() -> None:
    op.execute(campaign_goals_weekly_progress)
    op.execute(campaign_goals_coverage)


def downgrade() -> None:
    op.execute("DROP VIEW campaign_goals_weekly_progress;")
    op.execute("DROP VIEW campaign_goals_coverage;")
