"""add_company_campaign_analysis_view

Revision ID: 7c0439914c05
Revises: ef9230c16ca4
Create Date: 2025-11-12 17:15:50.495442

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = "7c0439914c05"
down_revision: Union[str, None] = "ef9230c16ca4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

company_campaign_analysis = """
CREATE OR REPLACE VIEW company_campaign_analysis AS
SELECT
    c.company_id,
    c.id AS campaign_id,
    c.name AS campaign_name,
    ARRAY_AGG(ea.operative_view ORDER BY e.created_at) AS operative_views
FROM evaluation_analysis ea
JOIN evaluations e ON e.id = ea.evaluation_id
JOIN campaigns c ON c.id = e.campaigns_id
WHERE e.deleted_at IS NULL
  AND ea.deleted_at IS NULL
  AND c.deleted_at IS NULL
GROUP BY c.company_id, c.id, c.name
ORDER BY c.company_id, c.id;
"""


def upgrade() -> None:
    op.execute(company_campaign_analysis)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS company_campaign_analysis;")
