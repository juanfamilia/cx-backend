"""add prompt manager table

Revision ID: add_prompt_manager
Revises: 
Create Date: 2025-01-30

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_prompt_manager'
down_revision = None  # Update this to the latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Create prompt_managers table
    op.create_table(
        'prompt_managers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('prompt_name', sa.String(length=100), nullable=False),
        sa.Column('prompt_type', sa.String(), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_prompt_managers_company_id'), 'prompt_managers', ['company_id'], unique=False)
    op.create_index(op.f('ix_prompt_managers_is_active'), 'prompt_managers', ['is_active'], unique=False)
    op.create_index(op.f('ix_prompt_managers_prompt_type'), 'prompt_managers', ['prompt_type'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_prompt_managers_prompt_type'), table_name='prompt_managers')
    op.drop_index(op.f('ix_prompt_managers_is_active'), table_name='prompt_managers')
    op.drop_index(op.f('ix_prompt_managers_company_id'), table_name='prompt_managers')
    
    # Drop table
    op.drop_table('prompt_managers')
