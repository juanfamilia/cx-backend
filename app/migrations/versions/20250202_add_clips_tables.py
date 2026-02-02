"""Add clip and clip_config tables

Revision ID: 20250202_add_clips_tables
Revises: f10d72303278
Create Date: 2025-02-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250202_add_clips_tables'
down_revision: Union[str, None] = 'f10d72303278'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create clip_configs table
    op.create_table(
        'clip_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('critical_before', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('critical_after', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('negative_before', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('negative_after', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('positive_before', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('positive_after', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('max_clip_duration', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('max_clips_delivered', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_clip_configs_company_id', 'clip_configs', ['company_id'])

    # Create clips table
    op.create_table(
        'clips',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=False),
        sa.Column('cloudflare_uid', sa.String(), nullable=True),
        sa.Column('stream_url', sa.String(), nullable=True),
        sa.Column('thumbnail_url', sa.String(), nullable=True),
        sa.Column('verbatim_type', sa.String(), nullable=False),
        sa.Column('verbatim_text', sa.Text(), nullable=False),
        sa.Column('verbatim_origin', sa.String(), nullable=False, server_default='cliente'),
        sa.Column('original_timestamp', sa.Integer(), nullable=False),
        sa.Column('clip_start', sa.Integer(), nullable=False),
        sa.Column('clip_end', sa.Integer(), nullable=False),
        sa.Column('clip_duration', sa.Integer(), nullable=False),
        sa.Column('priority_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('priority_rank', sa.Integer(), nullable=True),
        sa.Column('is_delivered', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('extra_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_clips_evaluation_id', 'clips', ['evaluation_id'])
    op.create_index('ix_clips_status', 'clips', ['status'])
    op.create_index('ix_clips_verbatim_type', 'clips', ['verbatim_type'])
    op.create_index('ix_clips_is_delivered', 'clips', ['is_delivered'])


def downgrade() -> None:
    op.drop_index('ix_clips_is_delivered', table_name='clips')
    op.drop_index('ix_clips_verbatim_type', table_name='clips')
    op.drop_index('ix_clips_status', table_name='clips')
    op.drop_index('ix_clips_evaluation_id', table_name='clips')
    op.drop_table('clips')
    
    op.drop_index('ix_clip_configs_company_id', table_name='clip_configs')
    op.drop_table('clip_configs')
