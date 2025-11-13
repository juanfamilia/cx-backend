"""add widget type enum

Revision ID: 3fdbf1a24324
Revises: 0645a6205f5a
Create Date: 2025-11-13 10:28:10.462735
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3fdbf1a24324'
down_revision: Union[str, None] = '0645a6205f5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Crear ENUMs antes de usarlos ---
    widget_type_enum = sa.Enum(
        'METRIC_CARD', 'LINE_CHART', 'BAR_CHART', 'PIE_CHART', 'TABLE', 'MAP',
        'HEATMAP', 'LEADERBOARD', 'RECENT_ACTIVITY', 'ALERTS',
        name='widgettype'
    )
    data_source_enum = sa.Enum(
        'EVALUATIONS', 'CAMPAIGNS', 'USERS', 'ZONES', 'CUSTOM',
        name='datasource'
    )

    # ✅ Crear explícitamente los tipos ENUM en PostgreSQL antes de alterar columnas
    bind = op.get_bind()
    widget_type_enum.create(bind, checkfirst=True)
    data_source_enum.create(bind, checkfirst=True)

    # --- Nueva tabla de temas de compañía ---
    op.create_table(
        'company_themes',
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('company_logo_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('company_favicon_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('company_name_override', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('primary_color', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('secondary_color', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('accent_color', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('success_color', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('warning_color', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('error_color', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('font_family_primary', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('font_family_secondary', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('sidebar_background', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('header_background', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('custom_css', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('features_config', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id')
    )

    # --- Limpieza de tablas obsoletas ---
    op.drop_table('onboarding_status')
    op.drop_index(op.f('ix_prompt_managers_company_id'), table_name='prompt_managers')
    op.drop_index(op.f('ix_prompt_managers_is_active'), table_name='prompt_managers')
    op.drop_index(op.f('ix_prompt_managers_prompt_type'), table_name='prompt_managers')
    op.drop_table('prompt_managers')

    # --- Ajustes en user_dashboard_widgets ---
    op.add_column(
        'user_dashboard_widgets',
        sa.Column('is_visible', sa.Boolean(), nullable=False, server_default=sa.text('true'))
    )
    op.add_column(
        'user_dashboard_widgets',
        sa.Column('order', sa.Integer(), nullable=False, server_default=sa.text('0'))
    )
    op.add_column('user_dashboard_widgets', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('user_dashboard_widgets', sa.Column('updated_at', sa.DateTime(), nullable=True))

    # ✅ Convertir position INTEGER → JSON correctamente
    op.execute("""
        ALTER TABLE user_dashboard_widgets
        ALTER COLUMN position TYPE JSON
        USING json_build_object('x', position, 'y', 0, 'cols', 4, 'rows', 2);
    """)

    # Añadir FK sin violaciones
    op.create_foreign_key(
        None,
        'user_dashboard_widgets',
        'users',
        ['user_id'],
        ['id']
    )

    # Eliminar columna obsoleta
    op.drop_column('user_dashboard_widgets', 'settings')

    # --- Ajustes en widgets ---
    op.alter_column(
        'widgets',
        'type',
        existing_type=sa.VARCHAR(length=50),
        type_=widget_type_enum,
        nullable=False
    )

    op.alter_column(
        'widgets',
        'default_position',
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=sa.JSON(),
        existing_nullable=True
    )

    op.alter_column(
        'widgets',
        'data_source',
        existing_type=sa.VARCHAR(length=50),
        type_=data_source_enum,
        nullable=False
    )

    op.alter_column(
        'widgets',
        'query_params',
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=sa.JSON(),
        existing_nullable=True
    )

    op.alter_column(
        'widgets',
        'is_public',
        existing_type=sa.BOOLEAN(),
        server_default=sa.text('true'),
        nullable=False
    )

    op.alter_column(
        'widgets',
        'is_active',
        existing_type=sa.BOOLEAN(),
        server_default=sa.text('true'),
        nullable=False
    )

    op.alter_column(
        'widgets',
        'created_at',
        existing_type=postgresql.TIMESTAMP(),
        nullable=True
    )

    op.create_foreign_key(None, 'widgets', 'companies', ['company_id'], ['id'])
