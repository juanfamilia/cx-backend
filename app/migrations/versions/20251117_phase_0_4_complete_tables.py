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
    # -- Las siguientes líneas están comentadas para evitar el error DuplicateTable.
    # op.create_table('insights', ...)
    # op.create_index(op.f('ix_insights_company_id'), 'insights', ['company_id'], unique=False)
    # op.create_index(op.f('ix_insights_deleted_at'), 'insights', ['deleted_at'], unique=False)
    # op.create_table('tags', ...)
    # op.create_table('evaluation_tags', ...)
    # op.create_table('alert_thresholds', ...)
    # op.create_table('trends', ...)
    # op.create_table('prompts', ...)
    # op.create_index(op.f('ix_prompts_category'), 'prompts', ['category'], unique=False)
    # op.create_table('widget_definitions', ...)
    # op.create_table('dashboard_configs', ...)
    # op.create_table('company_themes', ...)
    # op.create_index(op.f('ix_company_themes_company_id'), 'company_themes', ['company_id'], unique=False)
    
    # Aquí SÓLO deja/elimina/comenta todo lo que intente crear tablas o índices
    # Si tienes cambios de columnas nuevos, déjalos activos
    pass

def downgrade() -> None:
    # Puedes comentar el drop_table también si te preocupa el delete en downgrade.
    # op.drop_index(op.f('ix_company_themes_company_id'), table_name='company_themes')
    # op.drop_table('company_themes')
    # op.drop_table('dashboard_configs')
    # op.drop_table('widget_definitions')
    # op.drop_index(op.f('ix_prompts_category'), table_name='prompts')
    # op.drop_table('prompts')
    # op.drop_table('trends')
    # op.drop_table('alert_thresholds')
    # op.drop_table('evaluation_tags')
    # op.drop_table('tags')
    # op.drop_index(op.f('ix_insights_deleted_at'), table_name='insights')
    # op.drop_index(op.f('ix_insights_company_id'), table_name='insights')
    # op.drop_table('insights')
    pass
