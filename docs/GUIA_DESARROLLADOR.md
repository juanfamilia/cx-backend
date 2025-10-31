# 👨‍💻 GUÍA PARA DESARROLLADOR - IMPLEMENTACIÓN PASO A PASO

**Para:** Desarrollador de Siete CX  
**Tiempo Total:** 6-8 horas (implementación completa)  
**Riesgo:** BAJO (archivos nuevos, no toca código existente)

---

## 🎯 OBJETIVO:

Implementar nuevas funcionalidades sin romper lo que ya funciona.

---

## 📋 RESUMEN DE LO QUE VOY A HACER:

1. ✅ Crear migraciones de base de datos (5 tablas nuevas)
2. ✅ Copiar archivos nuevos al proyecto
3. ✅ Instalar 2 dependencias nuevas
4. ✅ Configurar variables de entorno opcionales
5. ✅ Probar que todo funciona

---

## 🚀 IMPLEMENTACIÓN RÁPIDA (ORDEN DE PRIORIDAD)

### PRIORIDAD 1: Intelligence Engine (2-3 horas)

**¿Qué hace?** Genera insights automáticos de cada evaluación.

**Pasos:**

1. **Crear migraciones:**
```bash
cd /app/cx-backend

# Crear migración para intelligence
alembic revision -m "add_intelligence_tables"
```

2. **Editar el archivo de migración** (en `app/migrations/versions/XXXXX_add_intelligence_tables.py`):

```python
def upgrade():
    # Tabla insights
    op.create_table(
        'insights',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id')),
        sa.Column('evaluation_id', sa.Integer(), sa.ForeignKey('evaluations.id'), nullable=True),
        sa.Column('insight_type', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), default='medium'),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('metrics', postgresql.JSONB(), nullable=True),
        sa.Column('suggested_actions', postgresql.JSONB(), nullable=True),
        sa.Column('is_read', sa.Boolean(), default=False),
        sa.Column('is_resolved', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True)
    )
    
    # Tabla tags
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('category', sa.String(), default='general'),
        sa.Column('color', sa.String(), default='#6b7280'),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('is_active', sa.Boolean(), default=True)
    )
    
    # Tabla evaluation_tags
    op.create_table(
        'evaluation_tags',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('evaluation_id', sa.Integer(), sa.ForeignKey('evaluations.id')),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('tags.id')),
        sa.Column('auto_tagged', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )
    
    # Tabla alert_thresholds
    op.create_table(
        'alert_thresholds',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id')),
        sa.Column('metric_name', sa.String(), nullable=False),
        sa.Column('condition', sa.String(), nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('threshold_value_max', sa.Float(), nullable=True),
        sa.Column('alert_severity', sa.String(), default='medium'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now())
    )
    
    # Tabla trends
    op.create_table(
        'trends',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id')),
        sa.Column('metric_name', sa.String(), nullable=False),
        sa.Column('period', sa.String(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('average_value', sa.Float(), nullable=False),
        sa.Column('min_value', sa.Float(), nullable=False),
        sa.Column('max_value', sa.Float(), nullable=False),
        sa.Column('sample_count', sa.Integer(), nullable=False),
        sa.Column('trend_direction', sa.String(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

def downgrade():
    op.drop_table('trends')
    op.drop_table('alert_thresholds')
    op.drop_table('evaluation_tags')
    op.drop_table('tags')
    op.drop_table('insights')
```

3. **Ejecutar migración:**
```bash
alembic upgrade head
```

4. **Copiar archivos nuevos del branch:**
```bash
# Desde el branch phase0-4-enhancements1
cp app/models/intelligence_model.py [tu-proyecto]/app/models/
cp app/services/intelligence_services.py [tu-proyecto]/app/services/
cp app/routes/intelligence_router.py [tu-proyecto]/app/routes/
```

5. **Registrar el router** en `app/routes/main.py`:
```python
from app.routes import intelligence_router

# En la función que registra routers:
api_router.include_router(intelligence_router.router)
```

6. **Modificar** `app/services/extract_audio_services.py` (línea ~120):

Añadir DESPUÉS de guardar el análisis:

```python
# Después de: db_analysis = await create_evaluation_analysis(...)

# 🧠 INTELLIGENCE ENGINE: Auto-generate insights and tags
try:
    from app.services.intelligence_services import (
        generate_insights_from_analysis,
        auto_tag_evaluation,
        check_alert_thresholds
    )
    from app.models.evaluation_model import Evaluation
    from app.models.campaign_model import Campaign
    
    # Get evaluation to retrieve company_id
    eval_query = select(Evaluation).where(Evaluation.id == evaluation_id)
    eval_result = await session.execute(eval_query)
    evaluation = eval_result.scalars().first()
    
    if evaluation:
        campaign_query = select(Campaign).where(Campaign.id == evaluation.campaigns_id)
        campaign_result = await session.execute(campaign_query)
        campaign = campaign_result.scalars().first()
        
        if campaign:
            company_id = campaign.company_id
            
            # Generate insights
            insights = await generate_insights_from_analysis(
                session, evaluation_id, db_analysis, company_id
            )
            
            # Auto-tag
            tags = await auto_tag_evaluation(
                session, evaluation_id, db_analysis
            )
            
            # Check alerts
            alerts = await check_alert_thresholds(
                session, evaluation_id, db_analysis, company_id
            )
            
except Exception as e:
    print(f"⚠️ Intelligence engine error: {e}")
    # Continue even if intelligence fails
```

7. **Probar:**
```bash
# Reiniciar servidor
supervisorctl restart backend

# O si usas uvicorn directamente:
uvicorn app.main:app --reload
```

**✅ Verificar:**
- Sube una evaluación
- Espera análisis
- Ve a `/api/v1/intelligence/insights`
- Deberías ver insights generados

**Tiempo estimado:** 2-3 horas

---

### PRIORIDAD 2: Dashboards Configurables (3-4 horas)

**¿Qué hace?** Widgets personalizables, gráficos, exportar Excel.

**Pasos:**

1. **Instalar dependencias:**
```bash
pip install pandas openpyxl
pip freeze > requirements.txt
```

2. **Crear migraciones:**
```bash
alembic revision -m "add_dashboard_tables"
```

Contenido del archivo de migración:

```python
def upgrade():
    # Tabla dashboard_configs
    op.create_table(
        'dashboard_configs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('layout_config', postgresql.JSONB(), nullable=False),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('config_name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True)
    )
    
    # Tabla widget_definitions
    op.create_table(
        'widget_definitions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('widget_type', sa.String(), nullable=False),
        sa.Column('widget_name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('data_source', sa.String(), nullable=False),
        sa.Column('default_config', postgresql.JSONB(), nullable=True),
        sa.Column('available_for_roles', postgresql.JSONB(), nullable=False),
        sa.Column('category', sa.String(), default='general'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('is_active', sa.Boolean(), default=True)
    )

def downgrade():
    op.drop_table('widget_definitions')
    op.drop_table('dashboard_configs')
```

3. **Ejecutar migración:**
```bash
alembic upgrade head
```

4. **Copiar archivos:**
```bash
cp app/models/dashboard_config_model.py [tu-proyecto]/app/models/
cp app/services/dashboard_config_services.py [tu-proyecto]/app/services/
cp app/services/dashboard_widgets_services.py [tu-proyecto]/app/services/
cp app/services/export_services.py [tu-proyecto]/app/services/
cp app/routes/dashboard_config_router.py [tu-proyecto]/app/routes/
```

5. **Modificar** `app/routes/dashboard_router.py`:

Añadir imports al inicio:
```python
from app.services.dashboard_widgets_services import (
    get_nps_trend_data,
    get_status_breakdown_data,
    get_top_evaluators_data,
    # ... otros imports
)
from app.services.export_services import (
    export_dashboard_to_excel,
    generate_pdf_report
)
```

Añadir endpoints al final del archivo:
```python
# Widget endpoints
@router.get("/widgets/nps-trend")
async def get_nps_trend(...):
    # copiar del archivo

@router.get("/widgets/status-breakdown")
async def get_status_breakdown(...):
    # copiar del archivo

# Export endpoints
@router.get("/export/excel")
async def export_dashboard_excel(...):
    # copiar del archivo
```

6. **Registrar router** en `app/routes/main.py`:
```python
from app.routes import dashboard_config_router

api_router.include_router(dashboard_config_router.router)
```

**✅ Verificar:**
- Ve a `/api/v1/dashboard/widgets/nps-trend`
- Deberías ver datos JSON
- Ve a `/api/v1/dashboard/export/excel`
- Debería descargarse un Excel

**Tiempo estimado:** 3-4 horas

---

### PRIORIDAD 3: Notificaciones Email (1 hora)

**¿Qué hace?** Envía emails cuando termina análisis.

**Pasos:**

1. **Instalar dependencia:**
```bash
pip install sendgrid
pip freeze > requirements.txt
```

2. **Configurar SendGrid:**
- Ve a https://sendgrid.com
- Crea cuenta (gratis hasta 100 emails/día)
- Genera API Key
- Añade a `.env`:
```bash
SENDGRID_API_KEY=SG.xxxxx
SENDGRID_FROM_EMAIL=noreply@sieteic.com
SENDGRID_FROM_NAME=Siete CX
```

3. **Copiar archivo:**
```bash
cp app/services/notification_integration_services.py [tu-proyecto]/app/services/
```

4. **Usar en el flujo de análisis** (opcional por ahora):

En `extract_audio_services.py`, después del intelligence engine:

```python
# Opcional: Notificar por email
try:
    from app.services.notification_integration_services import notification_orchestrator
    
    # Obtener datos del usuario
    user = await session.get(User, evaluation.user_id)
    campaign = await session.get(Campaign, evaluation.campaigns_id)
    
    await notification_orchestrator.notify_evaluation_complete(
        session,
        user_id=user.id,
        user_email=user.email,
        user_name=f"{user.first_name} {user.last_name}",
        user_phone=None,  # añadir si tienes campo phone en User
        evaluation_id=evaluation_id,
        campaign_name=campaign.name
    )
except Exception as e:
    print(f"Email notification failed: {e}")
```

**✅ Verificar:**
- Sube evaluación
- Revisa email del shopper
- Debería llegar notificación

**Tiempo estimado:** 1 hora

---

### PRIORIDAD 4: White-label Theming (2 horas)

**¿Qué hace?** Logo y colores personalizados por empresa.

**Pasos:**

1. **Crear migración:**
```bash
alembic revision -m "add_company_themes"
```

```python
def upgrade():
    op.create_table(
        'company_themes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), unique=True),
        sa.Column('company_logo_url', sa.String(), nullable=True),
        sa.Column('company_favicon_url', sa.String(), nullable=True),
        sa.Column('company_name_override', sa.String(), nullable=True),
        sa.Column('primary_color', sa.String(), default='#8b5cf6'),
        sa.Column('secondary_color', sa.String(), default='#3b82f6'),
        sa.Column('accent_color', sa.String(), default='#10b981'),
        sa.Column('success_color', sa.String(), default='#10b981'),
        sa.Column('warning_color', sa.String(), default='#f59e0b'),
        sa.Column('error_color', sa.String(), default='#ef4444'),
        sa.Column('font_family_primary', sa.String(), default='Inter, sans-serif'),
        sa.Column('font_family_secondary', sa.String(), nullable=True),
        sa.Column('sidebar_background', sa.String(), default='#1f2937'),
        sa.Column('header_background', sa.String(), default='#ffffff'),
        sa.Column('custom_css', sa.Text(), nullable=True),
        sa.Column('features_config', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now())
    )

def downgrade():
    op.drop_table('company_themes')
```

2. **Copiar archivos:**
```bash
cp app/models/theme_model.py [tu-proyecto]/app/models/
cp app/services/theme_services.py [tu-proyecto]/app/services/
cp app/routes/theme_router.py [tu-proyecto]/app/routes/
```

3. **Registrar router:**
```python
from app.routes import theme_router

api_router.include_router(theme_router.router)
```

**✅ Verificar:**
- Ve a `/api/v1/theme/`
- Deberías ver tema default
- Modifica colores
- CSS debería generarse

**Tiempo estimado:** 2 horas

---

### PRIORIDAD 5: Prompts Personalizados (2 horas)

**Pasos:**

1. **Crear migración:**
```bash
alembic revision -m "add_prompt_managers"
```

```python
def upgrade():
    op.create_table(
        'prompt_managers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id')),
        sa.Column('prompt_name', sa.String(100), nullable=False),
        sa.Column('prompt_type', sa.String(), default='dual_analysis'),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True)
    )

def downgrade():
    op.drop_table('prompt_managers')
```

2. **Copiar archivos:**
```bash
cp app/models/prompt_manager_model.py [tu-proyecto]/app/models/
cp app/services/prompt_manager_services.py [tu-proyecto]/app/services/
cp app/routes/prompt_manager_router.py [tu-proyecto]/app/routes/
```

3. **Modificar** `app/services/openai_services.py`:

Reemplazar la función `audio_analysis` con la versión que soporta custom prompts (del branch).

4. **Registrar router:**
```python
from app.routes import prompt_manager_router

api_router.include_router(prompt_manager_router.router)
```

**✅ Verificar:**
- Ve a `/api/v1/prompts`
- Crea un prompt custom
- Sube evaluación
- Análisis debería usar tu prompt

**Tiempo estimado:** 2 horas

---

## 🧪 PRUEBAS FINALES:

```bash
# 1. Verificar migraciones
alembic current

# 2. Verificar tablas creadas
# Conecta a PostgreSQL y verifica:
\dt

# Deberías ver:
# - insights
# - tags
# - evaluation_tags
# - alert_thresholds
# - trends
# - dashboard_configs
# - widget_definitions
# - company_themes
# - prompt_managers

# 3. Verificar endpoints
curl http://localhost:8000/api/v1/intelligence/insights
curl http://localhost:8000/api/v1/dashboard/widgets/nps-trend
curl http://localhost:8000/api/v1/theme
curl http://localhost:8000/api/v1/prompts

# 4. Seed datos de prueba (opcional)
python -m app.seeder.seed_database
```

---

## 📦 DEPENDENCIAS A INSTALAR:

```bash
pip install pandas openpyxl sendgrid twilio
pip freeze > requirements.txt
```

---

## ⚠️ COSAS IMPORTANTES:

1. **SIEMPRE haz backup de BD antes de migraciones**
2. **Prueba en ambiente de desarrollo primero**
3. **NO hagas push a producción sin probar**
4. **Los archivos están diseñados para NO romper código existente**

---

## 🆘 SI ALGO FALLA:

**Error en migración:**
```bash
# Rollback
alembic downgrade -1

# Ver estado
alembic current
```

**Error al importar módulos:**
- Verifica que copiaste todos los archivos
- Revisa que los nombres de archivos sean exactos

**Error 500 en API:**
- Revisa logs: `tail -f /var/log/supervisor/backend.err.log`
- Verifica que migraciones se ejecutaron

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN:

- [ ] Todas las migraciones ejecutadas
- [ ] Todos los archivos copiados
- [ ] Routers registrados en main.py
- [ ] Dependencias instaladas
- [ ] Variables de entorno configuradas
- [ ] Servidor reiniciado
- [ ] Endpoints responden correctamente
- [ ] Seeder ejecutado (opcional)
- [ ] Probado con evaluación real

---

**¡Listo para implementar!** 🚀

**Tiempo total:** 6-8 horas para implementación completa
**Tiempo mínimo viable:** 3-4 horas (solo Prioridad 1 y 2)
