"""update goals view

Revision ID: ee1de394a11e
Revises: 53f55fd99f8b
Create Date: 2025-07-11 14:29:47.569381

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = "ee1de394a11e"
down_revision: Union[str, None] = "53f55fd99f8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

view_sql = """
CREATE VIEW campaign_goals_progress AS
SELECT 
    cge.campaign_id,
    c.name AS campaign_name,
    cge.evaluator_id,
    cge.goal AS goal_evaluator,
    COALESCE(COUNT(ev.id), 0) AS goal_complete,
    c.date_start,
    c.date_end
FROM campaign_goals_evaluators cge
JOIN campaigns c ON c.id = cge.campaign_id
LEFT JOIN evaluations ev 
    ON ev.campaigns_id = c.id 
   AND ev.user_id = cge.evaluator_id
   AND ev.deleted_at IS NULL
   AND ev.status = 'APROVED'
GROUP BY 
    cge.campaign_id, 
    c.name, 
    cge.evaluator_id, 
    cge.goal, 
    c.date_start, 
    c.date_end;
"""


def upgrade() -> None:
    op.execute("DROP VIEW campaign_goals_progress;")
    op.execute(view_sql)


def downgrade() -> None:
    op.execute("DROP VIEW campaign_goals_progress;")
