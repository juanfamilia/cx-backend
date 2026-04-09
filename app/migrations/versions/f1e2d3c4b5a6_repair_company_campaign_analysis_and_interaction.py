"""Repara vista company_campaign_analysis y valores legacy de interaction_type.

- Vista usada por get_manager_summary / dashboard rol 2.
- Filas antiguas con interaction_type en español (presencial, …) rompen el ORM
  si la columna pasa a ser interactiontypeenum.

Revision ID: f1e2d3c4b5a6
Revises: d4e5f6789abc
Create Date: 2026-04-09

"""

from typing import Sequence, Union

from alembic import op

revision: str = "f1e2d3c4b5a6"
down_revision: Union[str, None] = "d4e5f6789abc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_company_campaign_analysis = """
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
    op.execute(_company_campaign_analysis)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'evaluations'
                  AND column_name = 'interaction_type'
            ) THEN
                BEGIN
                    CREATE TYPE interactiontypeenum AS ENUM (
                        'IN_PERSON', 'CALL_CENTER', 'WHATSAPP',
                        'VIDEO_CALL', 'OTHER'
                    );
                EXCEPTION
                    WHEN duplicate_object THEN NULL;
                END;
                ALTER TABLE evaluations
                    ALTER COLUMN interaction_type DROP DEFAULT;
                ALTER TABLE evaluations
                    ALTER COLUMN interaction_type TYPE text
                    USING (interaction_type::text);
                UPDATE evaluations SET interaction_type = 'IN_PERSON'
                    WHERE interaction_type IN ('presencial', 'Presencial');
                UPDATE evaluations SET interaction_type = 'CALL_CENTER'
                    WHERE interaction_type IN ('callcenter', 'Callcenter');
                UPDATE evaluations SET interaction_type = 'WHATSAPP'
                    WHERE interaction_type IN ('whatsapp', 'Whatsapp');
                UPDATE evaluations SET interaction_type = 'VIDEO_CALL'
                    WHERE interaction_type IN ('videollamada', 'Videollamada');
                UPDATE evaluations SET interaction_type = 'OTHER'
                    WHERE interaction_type IN ('otro', 'Otro');
                UPDATE evaluations SET interaction_type = 'IN_PERSON'
                    WHERE interaction_type IS NOT NULL
                      AND interaction_type NOT IN (
                        'IN_PERSON', 'CALL_CENTER', 'WHATSAPP',
                        'VIDEO_CALL', 'OTHER'
                      );
                ALTER TABLE evaluations
                    ALTER COLUMN interaction_type TYPE interactiontypeenum
                    USING (
                        CASE
                            WHEN interaction_type IS NULL THEN NULL::interactiontypeenum
                            WHEN interaction_type = 'IN_PERSON' THEN 'IN_PERSON'::interactiontypeenum
                            WHEN interaction_type = 'CALL_CENTER' THEN 'CALL_CENTER'::interactiontypeenum
                            WHEN interaction_type = 'WHATSAPP' THEN 'WHATSAPP'::interactiontypeenum
                            WHEN interaction_type = 'VIDEO_CALL' THEN 'VIDEO_CALL'::interactiontypeenum
                            WHEN interaction_type = 'OTHER' THEN 'OTHER'::interactiontypeenum
                            ELSE 'IN_PERSON'::interactiontypeenum
                        END
                    );
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS company_campaign_analysis;")
