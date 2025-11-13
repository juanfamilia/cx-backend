"""add widgets and onboarding only

Revision ID: 0645a6205f5a
Revises: 246e347a5be0
Create Date: 2025-11-12 15:27:37.014835

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String

# revision identifiers, used by Alembic.
revision: str = '0645a6205f5a'
down_revision: Union[str, None] = '246e347a5be0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'widgets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'user_dashboard_widgets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('widget_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['widget_id'], ['widgets.id']),
    )
    op.create_table(
        'onboarding_status',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('steps_completed', ARRAY(String), nullable=True),
        sa.Column('tours_completed', ARRAY(String), nullable=True),
        sa.Column('last_step', sa.String(length=100), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
    )

def downgrade() -> None:
    op.drop_table('onboarding_status')
    op.drop_table('user_dashboard_widgets')
    op.drop_table('widgets')
