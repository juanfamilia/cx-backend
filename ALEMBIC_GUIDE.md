# 🔧 Guía Completa de Migraciones Alembic - Siete CX

## ✅ CORRECCIONES APLICADAS

### 1. **env.py** - Motor Síncrono para Migraciones
- ❌ **ANTES:** Importaba `engine` async de `app.core.db`
- ✅ **AHORA:** Crea su propio engine síncrono con `psycopg2`
- ✅ **Convierte automáticamente:** `postgresql+asyncpg://` → `postgresql://`
- ✅ **Importa TODOS los modelos:** Incluye dashboard_config, intelligence, prompt_manager, theme

### 2. **alembic.ini** - URL desde Variable de Entorno
- ✅ `env.py` lee `POSTGRES_URI` del entorno
- ✅ No usa URL hardcodeada

### 3. **requirements.txt** - Dependencias Verificadas
- ✅ `alembic==1.17.1`
- ✅ `sqlmodel==0.0.27`
- ✅ `psycopg2-binary==2.9.11` (para migraciones síncronas)
- ✅ `asyncpg==0.30.0` (para runtime async)
- ✅ `pydantic-settings==2.11.0`

---

## 📋 VARIABLES DE ENTORNO REQUERIDAS

### Para Desarrollo Local

Crea un archivo `.env` en `/app/cx-backend/`:

```bash
# Base de datos (CRÍTICO)
POSTGRES_URI="postgresql+asyncpg://user:password@localhost:5432/siete_cx"

# JWT (CRÍTICO)
JWT_SECRET_KEY="tu-secret-key-aqui"
JWT_ALGORITHM="HS256"
JWT_EXPIRE=1440

# Proyecto
PROJECT_NAME="Siete CX"
API_URL="/api/v1"

# OpenAI (reemplaza con tu key real)
OPENAI_API_KEY="sk-proj-YOUR-OPENAI-KEY-HERE"

# Cloudflare (proporcionado)
CLOUDFLARE_ACCOUNT_ID="ee7b999ce5048096a724f6a22f5b2e4d"
CLOUDFLARE_STREAM_KEY="yD8qfgx4ZW_IBnVYFGXMYc9FZvoFzIRTQfLRf3p_"

# R2 Storage (dummy si no se usa)
R2_ACCESS_KEY_ID="dummy"
R2_SECRET_ACCESS_KEY="dummy"
R2_BUCKET="dummy"
R2_ENDPOINT_URL="dummy"
```

### Para Railway (Producción)

**En Railway Dashboard → Variables:**

```bash
POSTGRES_URI=${{Postgres.DATABASE_URL}}
JWT_SECRET_KEY=<generar con: openssl rand -hex 32>
JWT_ALGORITHM=HS256
JWT_EXPIRE=1440
PROJECT_NAME=Siete CX
API_URL=/api/v1
OPENAI_API_KEY=sk-proj-...
CLOUDFLARE_ACCOUNT_ID=ee7b999ce...
CLOUDFLARE_STREAM_KEY=yD8qfgx4ZW_...
R2_ACCESS_KEY_ID=dummy
R2_SECRET_ACCESS_KEY=dummy
R2_BUCKET=dummy
R2_ENDPOINT_URL=dummy
```

**⚠️ IMPORTANTE:** Railway automáticamente convierte `${{Postgres.DATABASE_URL}}` a la URL real.

---

## 🚀 COMANDOS DE MIGRACIONES

### 1. Crear una Nueva Migración (Auto-generada)

```bash
# Local
alembic revision --autogenerate -m "descripcion del cambio"

# Railway CLI
railway run alembic revision --autogenerate -m "descripcion del cambio"
```

### 2. Ejecutar Migraciones (Aplicar a BD)

```bash
# Local
alembic upgrade head

# Railway CLI (RECOMENDADO)
railway run alembic upgrade head
```

### 3. Ver Estado de Migraciones

```bash
# Local
alembic current

# Railway CLI
railway run alembic current
```

### 4. Ver Historial

```bash
# Local
alembic history

# Railway CLI
railway run alembic history
```

### 5. Rollback (Deshacer última migración)

```bash
# Local
alembic downgrade -1

# Railway CLI
railway run alembic downgrade -1
```

---

## 🔍 VERIFICACIÓN POST-MIGRACIÓN

### 1. Verificar Tablas Creadas

**Tablas esperadas:**
- `users`
- `companies`
- `payments`
- `zones`
- `user_zones`
- `videos`
- `surveys`
- `survey_forms`
- `campaigns`
- `campaign_users`
- `campaign_zones`
- `evaluations`
- `notifications`
- `evaluation_analysis`
- `campaign_goals_evaluator`
- `dashboard_configs` ← NUEVO
- `widget_definitions` ← NUEVO
- `insights` ← NUEVO
- `trends` ← NUEVO
- `ai_tags` ← NUEVO
- `prompt_managers` ← NUEVO
- `company_themes` ← NUEVO

### 2. Verificar en Railway

**Opción A: Railway Dashboard**
1. Ve a tu servicio PostgreSQL
2. Click en **"Data"**
3. Verifica que las tablas existan

**Opción B: Railway CLI**
```bash
railway connect Postgres
# Luego en la consola psql:
\dt
```

---

## ⚡ FLUJO COMPLETO PRODUCCIÓN

### Primera Vez (Setup Inicial):

```bash
# 1. Instalar Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Vincular proyecto
railway link

# 4. Verificar variables de entorno
railway variables

# 5. Ejecutar migraciones
railway run alembic upgrade head

# 6. Verificar estado
railway run alembic current
```

### Cambios Posteriores en Modelos:

```bash
# 1. Crear migración
railway run alembic revision --autogenerate -m "add new field to users"

# 2. Revisar archivo generado en app/migrations/versions/

# 3. Aplicar migración
railway run alembic upgrade head
```

---

## 🐛 TROUBLESHOOTING

### Error: "POSTGRES_URI environment variable is not set"

**Solución:**
```bash
# Verificar variable en Railway
railway variables | grep POSTGRES_URI

# Si no existe, agregarla:
railway variables set POSTGRES_URI='${{Postgres.DATABASE_URL}}'
```

### Error: "No module named 'psycopg2'"

**Solución:**
```bash
# Verificar requirements.txt
grep psycopg2 requirements.txt

# Si falta, agregar:
echo "psycopg2-binary==2.9.11" >> requirements.txt
pip install -r requirements.txt
```

### Error: "cannot import name 'X' from 'app.models'"

**Solución:**
- Verifica que el modelo esté importado en `env.py`
- Verifica que el archivo del modelo esté en `app/models/`

### Error: "Target database is not up to date"

**Solución:**
```bash
# Ver migraciones pendientes
railway run alembic current
railway run alembic heads

# Aplicar migraciones pendientes
railway run alembic upgrade head
```

---

## 📊 ARQUITECTURA DE MIGRACIONES

```
cx-backend/
├── alembic.ini                    # Config principal (no modifica URL)
├── app/
│   ├── migrations/
│   │   ├── env.py                # ✅ Engine SÍNCRONO + imports completos
│   │   └── versions/             # Archivos de migración generados
│   │       ├── xxx_initial.py
│   │       └── yyy_add_field.py
│   ├── models/                   # Todos importados en env.py
│   │   ├── user_model.py
│   │   ├── company_model.py
│   │   ├── dashboard_config_model.py  ← NUEVO
│   │   ├── intelligence_model.py      ← NUEVO
│   │   ├── prompt_manager_model.py    ← NUEVO
│   │   └── theme_model.py             ← NUEVO
│   └── core/
│       └── db.py                 # Engine ASYNC (para FastAPI)
└── requirements.txt              # Todas las dependencias
```

---

## ✅ CHECKLIST FINAL

### Desarrollo Local:
- [ ] Crear `.env` con `POSTGRES_URI`
- [ ] Instalar dependencias: `pip install -r requirements.txt`
- [ ] Ejecutar migraciones: `alembic upgrade head`
- [ ] Verificar tablas en PostgreSQL local

### Railway (Producción):
- [ ] Variables de entorno configuradas en Railway
- [ ] `POSTGRES_URI=${{Postgres.DATABASE_URL}}`
- [ ] Railway CLI instalado y vinculado
- [ ] Ejecutar: `railway run alembic upgrade head`
- [ ] Verificar tablas en Railway PostgreSQL

### Verificación:
- [ ] `railway run alembic current` muestra migración actual
- [ ] Backend inicia sin errores: `railway logs`
- [ ] API responde: `curl https://your-app.railway.app/api/v1/health`

---

## 🎯 RESUMEN DE CAMBIOS CRÍTICOS

| Antes | Después |
|-------|---------|
| env.py usa engine async | env.py crea engine síncrono |
| Importa engine de db.py | Crea su propio engine |
| Falta importar modelos nuevos | Importa TODOS los modelos |
| URL hardcodeada en alembic.ini | Lee de POSTGRES_URI env var |
| asyncpg en migraciones | psycopg2 en migraciones |

---

## 📞 COMANDOS RÁPIDOS

```bash
# Setup inicial Railway
railway login && railway link

# Ejecutar migraciones
railway run alembic upgrade head

# Ver estado
railway run alembic current

# Logs del servicio
railway logs

# Variables de entorno
railway variables
```

---

**Estado:** ✅ LISTO PARA PRODUCCIÓN
**Última actualización:** Noviembre 2024
