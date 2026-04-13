"""Repair: create evaluation_events if it doesn't exist (missing from Railway DB).

Revision ID: i3j4k5l6m7n8
Revises: h2i3j4k5l6m7
Create Date: 2026-04-13

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "i3j4k5l6m7n8"
down_revision: Union[str, None] = "h2i3j4k5l6m7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE IF NOT EXISTS evaluationeventtypeenum AS ENUM (
                'complaint', 'emotional_peak', 'sales_signal',
                'objection', 'resolution', 'compliance_risk', 'other'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS evaluation_events (
            id          SERIAL PRIMARY KEY,
            evaluation_id INTEGER NOT NULL REFERENCES evaluations(id),
            event_type  evaluationeventtypeenum NOT NULL,
            timestamp_seconds DOUBLE PRECISION NOT NULL,
            severity    INTEGER NOT NULL,
            confidence  DOUBLE PRECISION,
            evidence_text TEXT,
            source      VARCHAR NOT NULL,
            created_at  TIMESTAMP,
            updated_at  TIMESTAMP
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_evaluation_events_evaluation_id ON evaluation_events(evaluation_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_evaluation_events_timestamp_seconds ON evaluation_events(timestamp_seconds);"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS evaluation_events;")
