"""Añade columnas de metadatos/IA en evaluations si faltan (staging desincronizado).

El modelo Evaluation incluye campos que nunca estuvieron en una migración aparte;
si la BD solo aplicó parte del historial, INSERT falla tras visited_zones.

Revision ID: d4e5f6789abc
Revises: c9012d3e4f5a
Create Date: 2026-04-08

"""

from typing import Sequence, Union

from alembic import op

revision: str = "d4e5f6789abc"
down_revision: Union[str, None] = "c9012d3e4f5a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE interactiontypeenum AS ENUM (
                'IN_PERSON', 'CALL_CENTER', 'WHATSAPP', 'VIDEO_CALL', 'OTHER'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS country VARCHAR;"
    )
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS branch_id VARCHAR;"
    )
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS branch_name VARCHAR;"
    )
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS "
        "interaction_type interactiontypeenum;"
    )
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS interaction_date DATE;"
    )
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS interaction_duration INTEGER;"
    )
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS customer_segment VARCHAR;"
    )
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS product_consulted VARCHAR;"
    )
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS customer_emotion VARCHAR;"
    )
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS agent_emotion VARCHAR;"
    )
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS problem_resolved BOOLEAN;"
    )
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS product_offered BOOLEAN;"
    )
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS risk_of_churn INTEGER;"
    )
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS service_quality_score INTEGER;"
    )
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS customer_effort_score INTEGER;"
    )
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS nps_inferred INTEGER;"
    )
    op.execute(
        "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS greeting_detected BOOLEAN;"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE evaluations DROP COLUMN IF EXISTS greeting_detected;"
    )
    op.execute(
        "ALTER TABLE evaluations DROP COLUMN IF EXISTS nps_inferred;"
    )
    op.execute(
        "ALTER TABLE evaluations DROP COLUMN IF EXISTS customer_effort_score;"
    )
    op.execute(
        "ALTER TABLE evaluations DROP COLUMN IF EXISTS service_quality_score;"
    )
    op.execute("ALTER TABLE evaluations DROP COLUMN IF EXISTS risk_of_churn;")
    op.execute("ALTER TABLE evaluations DROP COLUMN IF EXISTS product_offered;")
    op.execute("ALTER TABLE evaluations DROP COLUMN IF EXISTS problem_resolved;")
    op.execute("ALTER TABLE evaluations DROP COLUMN IF EXISTS agent_emotion;")
    op.execute("ALTER TABLE evaluations DROP COLUMN IF EXISTS customer_emotion;")
    op.execute("ALTER TABLE evaluations DROP COLUMN IF EXISTS product_consulted;")
    op.execute("ALTER TABLE evaluations DROP COLUMN IF EXISTS customer_segment;")
    op.execute(
        "ALTER TABLE evaluations DROP COLUMN IF EXISTS interaction_duration;"
    )
    op.execute("ALTER TABLE evaluations DROP COLUMN IF EXISTS interaction_date;")
    op.execute("ALTER TABLE evaluations DROP COLUMN IF EXISTS interaction_type;")
    op.execute("ALTER TABLE evaluations DROP COLUMN IF EXISTS branch_name;")
    op.execute("ALTER TABLE evaluations DROP COLUMN IF EXISTS branch_id;")
    op.execute("ALTER TABLE evaluations DROP COLUMN IF EXISTS country;")
    op.execute("DROP TYPE IF EXISTS interactiontypeenum;")
