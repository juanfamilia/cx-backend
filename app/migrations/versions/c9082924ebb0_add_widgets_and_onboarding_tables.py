"""add widgets and onboarding tables

Revision ID: c9082924ebb0
Revises: bb9c6359b94f
Create Date: 2025-11-12 11:23:09.511792
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String, inspect

# revision identifiers, used by Alembic.
revision: str = 'c9082924ebb0'
down_revision: Union[str, None] = 'bb9c6359b94f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()

    # --- Crear tabla widgets ---
    if 'widgets' not in tables:
        op.create_table(
            'widgets',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.String(length=255), nullable=True),
            sa.Column('config', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )

    # --- Crear tabla user_dashboard_widgets ---
    if 'user_dashboard_widgets' not in tables:
        op.create_table(
            'user_dashboard_widgets',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('widget_id', sa.Integer(), nullable=False),
            sa.Column('position', sa.Integer(), nullable=True),
            sa.Column('settings', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['widget_id'], ['widgets.id']),
        )

    # --- Crear tabla onboarding_status ---
    if 'onboarding_status' not in tables:
        op.create_table(
            'onboarding_status',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('steps_completed', ARRAY(String), nullable=True),
            sa.Column('tours_completed', ARRAY(String), nullable=True),
            sa.Column('last_step', sa.String(length=100), nullable=True),
            sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
        )

    # --- Crear tabla campaign_goals_progress (solo si no existe) ---
    if 'campaign_goals_progress' not in tables:
        op.create_table(
            'campaign_goals_progress',
            sa.Column('campaign_id', sa.Integer(), nullable=False),
            sa.Column('campaign_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('evaluator_id', sa.Integer(), nullable=False),
            sa.Column('goal_evaluator', sa.Integer(), nullable=False),
            sa.Column('goal_complete', sa.Integer(), nullable=False),
            sa.Column('date_start', sa.DateTime(), nullable=False),
            sa.Column('date_end', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('campaign_id', 'evaluator_id')
        )

    # --- Crear tabla company_users_evaluations ---
    if 'company_users_evaluations' not in tables:
        op.create_table(
            'company_users_evaluations',
            sa.Column('company_id', sa.Integer(), nullable=False),
            sa.Column('gerentes', sa.Integer(), nullable=True),
            sa.Column('evaluadores', sa.Integer(), nullable=True),
            sa.Column('evaluaciones_aprobadas', sa.Integer(), nullable=True),
            sa.Column('evaluaciones_rechazadas', sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint('company_id')
        )

    # --- Crear tabla manager_summary ---
    if 'manager_summary' not in tables:
        op.create_table(
            'manager_summary',
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('company_id', sa.Integer(), nullable=False),
            sa.Column('zonas_asignadas', sa.Integer(), nullable=False),
            sa.Column('evaluadores_asignados', sa.Integer(), nullable=False),
            sa.Column('active_campaigns', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('user_id')
        )

    # --- Crear tabla superadmin_summary ---
    if 'superadmin_summary' not in tables:
        op.create_table(
            'superadmin_summary',
            sa.Column('superadmin_id', sa.Integer(), nullable=False),
            sa.Column('total_empresas', sa.Integer(), nullable=False),
            sa.Column('empresas_vigentes', sa.Integer(), nullable=False),
            sa.Column('empresas_caducadas', sa.Integer(), nullable=False),
            sa.Column('usuarios_totales', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('superadmin_id')
        )

    # --- Crear tabla user_evaluation_summary ---
    if 'user_evaluation_summary' not in tables:
        op.create_table(
            'user_evaluation_summary',
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('rechazadas', sa.Integer(), nullable=True),
            sa.Column('aprobadas', sa.Integer(), nullable=True),
            sa.Column('ediciones_pendientes', sa.Integer(), nullable=True),
            sa.Column('enviadas', sa.Integer(), nullable=True),
            sa.Column('actualizadas', sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint('user_id')
        )

    # --- Ajustar columna goal en campaigns ---
    with op.batch_alter_table('campaigns', schema=None) as batch_op:
        batch_op.alter_column('goal', existing_type=sa.INTEGER(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table('campaigns', schema=None) as batch_op:
        batch_op.alter_column('goal', existing_type=sa.INTEGER(), nullable=True)

    op.drop_table('user_evaluation_summary')
    op.drop_table('superadmin_summary')
    op.drop_table('manager_summary')
    op.drop_table('company_users_evaluations')
    op.drop_table('campaign_goals_progress')
    op.drop_table('onboarding_status')
    op.drop_table('user_dashboard_widgets')
    op.drop_table('widgets')
