"""phase 0-4 complete tables

Revision ID: 20251117_phase04
Revises: 
Create Date: 2025-11-17 02:40:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251117_phase04'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create insights table
    op.create_table('insights',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=True),
        sa.Column('insight_type', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('suggested_actions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_insights_company_id'), 'insights', ['company_id'], unique=False)
    op.create_index(op.f('ix_insights_deleted_at'), 'insights', ['deleted_at'], unique=False)

    # Create tags table
    op.create_table('tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(), nullable=False, server_default='general'),
        sa.Column('color', sa.String(), nullable=False, server_default='#6b7280'),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create evaluation_tags table
    op.create_table('evaluation_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('auto_tagged', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create alert_thresholds table
    op.create_table('alert_thresholds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(), nullable=False),
        sa.Column('condition', sa.String(), nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('threshold_value_max', sa.Float(), nullable=True),
        sa.Column('alert_severity', sa.String(), nullable=False, server_default='medium'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create trends table
    op.create_table('trends',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(), nullable=False),
        sa.Column('period', sa.String(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('average_value', sa.Float(), nullable=False),
        sa.Column('min_value', sa.Float(), nullable=False),
        sa.Column('max_value', sa.Float(), nullable=False),
        sa.Column('sample_count', sa.Integer(), nullable=False),
        sa.Column('trend_direction', sa.String(), nullable=True),
        sa.Column('trend_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create prompts table
    op.create_table('prompts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('template', sa.Text(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('variables', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prompts_category'), 'prompts', ['category'], unique=False)

    # Create widget_definitions table
    op.create_table('widget_definitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('widget_type', sa.String(), nullable=False),
        sa.Column('widget_name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('data_source', sa.String(), nullable=False),
        sa.Column('default_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('available_for_roles', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('category', sa.String(), nullable=False, server_default='general'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create dashboard_configs table
    op.create_table('dashboard_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('layout_config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('config_name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create company_themes table
    op.create_table('company_themes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('primary_color', sa.String(length=7), nullable=False),
        sa.Column('secondary_color', sa.String(length=7), nullable=False),
        sa.Column('accent_color', sa.String(length=7), nullable=False),
        sa.Column('logo_url', sa.String(), nullable=True),
        sa.Column('favicon_url', sa.String(), nullable=True),
        sa.Column('custom_css', sa.Text(), nullable=True),
        sa.Column('font_family', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_company_themes_company_id'), 'company_themes', ['company_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_company_themes_company_id'), table_name='company_themes')
    op.drop_table('company_themes')
    op.drop_table('dashboard_configs')
    op.drop_table('widget_definitions')
    op.drop_index(op.f('ix_prompts_category'), table_name='prompts')
    op.drop_table('prompts')
    op.drop_table('trends')
    op.drop_table('alert_thresholds')
    op.drop_table('evaluation_tags')
    op.drop_table('tags')
    op.drop_index(op.f('ix_insights_deleted_at'), table_name='insights')
    op.drop_index(op.f('ix_insights_company_id'), table_name='insights')
    op.drop_table('insights')
