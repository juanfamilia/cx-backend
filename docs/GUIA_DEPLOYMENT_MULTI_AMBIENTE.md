# 🚀 GUÍA DE DEPLOYMENT MULTI-AMBIENTE - SIETE CX

**Para:** Juan (Owner)  
**Versión:** 1.0  
**Fecha:** Enero 2025

---

## 📑 ÍNDICE

1. [Resumen de Arquitectura](#1-resumen-de-arquitectura)
2. [Railway: Backend Multi-Ambiente](#2-railway-backend-multi-ambiente)
3. [Vercel: Frontend Multi-Ambiente](#3-vercel-frontend-multi-ambiente)
4. [Variables de Entorno por Ambiente](#4-variables-de-entorno-por-ambiente)
5. [Flujo de Trabajo (Workflow)](#5-flujo-de-trabajo-workflow)
6. [Checklist Post-Deployment](#6-checklist-post-deployment)

---

## 1. RESUMEN DE ARQUITECTURA

### 1.1 Ambientes

```
┌─────────────────────────────────────────────────┐
│                PRODUCCIÓN                        │
│  ❌ NO TOCAR - Mantener estable                 │
│  Branch: main                                    │
│  Railway: siete-cx-production                    │
│  Vercel: cx-production                           │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│                 STAGING                          │
│  ✅ Testing pre-producción                      │
│  Branch: phase0-4-enhancements1                  │
│  Railway: siete-cx-staging                       │
│  Vercel: cx-staging                              │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│               DEVELOPMENT                        │
│  ✅ Testing interno del equipo                  │
│  Branch: develop                                 │
│  Railway: siete-cx-development                   │
│  Vercel: cx-development                          │
└─────────────────────────────────────────────────┘
```

### 1.2 URLs Propuestas

| Ambiente | Backend (Railway) | Frontend (Vercel) |
|----------|-------------------|-------------------|
| **Production** | `cx-api.sieteic.com` | `cx.sieteic.com` |
| **Staging** | `cx-api-staging.sieteic.com` | `cx-staging.sieteic.com` |
| **Development** | `cx-api-dev.sieteic.com` | `cx-dev.sieteic.com` |

---

## 2. RAILWAY: BACKEND MULTI-AMBIENTE

### 2.1 Crear Proyecto Base (Solo una vez)

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login
```

### 2.2 Crear los 3 Ambientes en Railway

#### **Opción A: Via Railway Dashboard (Recomendado)**

**1. Crear Proyecto Staging:**
1. Ve a Railway Dashboard → "New Project"
2. Nombre: `siete-cx-staging`
3. Click "Deploy from GitHub repo"
4. Selecciona: `juanfamilia/cx-backend`
5. Branch: `phase0-4-enhancements1`
6. Click "Deploy"

**2. Agregar Base de Datos PostgreSQL:**
1. En el proyecto → Click "+ New"
2. Selecciona "Database" → "PostgreSQL"
3. Railway creará automáticamente la DB

**3. Configurar Variables de Entorno:**
   - Ver sección [4.1 Backend Staging](#41-backend-staging)

**4. Repetir para Development:**
   - Nombre: `siete-cx-development`
   - Branch: `develop` (crear este branch en GitHub primero)

#### **Opción B: Via Railway CLI**

```bash
# Crear proyecto Staging
railway init --name siete-cx-staging

# Conectar GitHub
railway link

# Agregar PostgreSQL
railway add --database postgres

# Deploy
railway up --branch phase0-4-enhancements1

# Repetir para Development
railway init --name siete-cx-development
railway up --branch develop
```

### 2.3 Configurar Build & Start Command

**En cada proyecto de Railway:**

1. Ve a Settings → "Deploy"
2. **Build Command:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Start Command:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. **Root Directory:** `/` (vacío)

### 2.4 Ejecutar Migraciones

**Para Staging:**
```bash
# Conectar a proyecto Staging
railway link siete-cx-staging

# Ejecutar migraciones
railway run alembic upgrade head

# Verificar
railway logs
```

**Para Development:**
```bash
railway link siete-cx-development
railway run alembic upgrade head
```

### 2.5 Configurar Dominios Personalizados

**En cada proyecto Railway:**

1. Settings → "Networking" → "Public Networking"
2. Click "Generate Domain" (obtendrás: `xxx.railway.app`)
3. **O** Click "Custom Domain":
   - Staging: `cx-api-staging.sieteic.com`
   - Development: `cx-api-dev.sieteic.com`

**Configurar DNS (en tu proveedor de dominio):**
```
Type: CNAME
Name: cx-api-staging
Value: [tu-proyecto-staging].railway.app

Type: CNAME
Name: cx-api-dev
Value: [tu-proyecto-dev].railway.app
```

---

## 3. VERCEL: FRONTEND MULTI-AMBIENTE

### 3.1 Crear Proyectos en Vercel

#### **Opción A: Via Vercel Dashboard (Recomendado)**

**1. Crear Proyecto Staging:**
1. Ve a Vercel Dashboard → "Add New" → "Project"
2. Import `juanfamilia/cx-frontend`
3. Nombre del proyecto: `cx-staging`
4. **Git Branch:** `phase0-4-enhancementsfe`
5. **Framework Preset:** Angular
6. **Build Command:** `npm install && npm run build`
7. **Output Directory:** `dist/cx-frontend/browser`
8. Click "Deploy"

**2. Configurar Variables de Entorno:**
   - Ver sección [4.2 Frontend Staging](#42-frontend-staging)

**3. Repetir para Development:**
   - Nombre: `cx-development`
   - Branch: `develop`

#### **Opción B: Via Vercel CLI**

```bash
# Instalar Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy Staging
cd /app/cx-frontend
vercel --prod --name cx-staging

# Deploy Development
vercel --prod --name cx-development
```

### 3.2 Configurar Build Settings

**Para cada proyecto en Vercel:**

1. Settings → "General"
2. **Framework Preset:** Angular
3. **Build Command:**
   ```bash
   npm install && npm run build
   ```
4. **Output Directory:**
   ```bash
   dist/cx-frontend/browser
   ```
5. **Install Command:**
   ```bash
   npm install
   ```

### 3.3 Configurar Dominios

**En cada proyecto Vercel:**

1. Settings → "Domains"
2. Agregar dominios:
   - **Staging:** `cx-staging.sieteic.com`
   - **Development:** `cx-dev.sieteic.com`

**Configurar DNS:**
```
Type: CNAME
Name: cx-staging
Value: cname.vercel-dns.com

Type: CNAME
Name: cx-dev
Value: cname.vercel-dns.com
```

---

## 4. VARIABLES DE ENTORNO POR AMBIENTE

### 4.1 Backend - Staging (Railway)

```bash
# Project
PROJECT_NAME=Siete CX Staging
PROJECT_URL=https://cx-api-staging.sieteic.com
API_URL=/api/v1
ENVIRONMENT=staging

# JWT
JWT_SECRET_KEY=[generar-con: python -c "import secrets; print(secrets.token_urlsafe(32))"]
JWT_ALGORITHM=HS256
JWT_EXPIRE=1440

# PostgreSQL (auto-provisto por Railway)
POSTGRES_URI=${{Postgres.DATABASE_URL}}

# OpenAI (usa una API key de testing)
OPENAI_API_KEY=sk-test-staging-key

# CORS (permite frontend staging)
CORS_ORIGINS=https://cx-staging.sieteic.com,http://localhost:4200

# Cloudflare (opcional - staging credentials)
CLOUDFLARE_STREAM_KEY=[staging-key]
CLOUDFLARE_ACCOUNT_ID=[staging-account]

# SendGrid (opcional - usa cuenta de test)
SENDGRID_API_KEY=SG.[staging-key]
SENDGRID_FROM_EMAIL=staging@sieteic.com

# Twilio (opcional - números de test)
TWILIO_ACCOUNT_SID=AC[staging-sid]
TWILIO_AUTH_TOKEN=[staging-token]
TWILIO_FROM_NUMBER=+1234567890
```

### 4.2 Backend - Development (Railway)

```bash
# Project
PROJECT_NAME=Siete CX Development
PROJECT_URL=https://cx-api-dev.sieteic.com
API_URL=/api/v1
ENVIRONMENT=development

# JWT (mismo que staging)
JWT_SECRET_KEY=[mismo-que-staging]
JWT_ALGORITHM=HS256
JWT_EXPIRE=1440

# PostgreSQL
POSTGRES_URI=${{Postgres.DATABASE_URL}}

# OpenAI (mock o test key)
OPENAI_API_KEY=sk-test-dev-key

# CORS
CORS_ORIGINS=https://cx-dev.sieteic.com,http://localhost:4200

# Integraciones (opcional - mock)
SENDGRID_API_KEY=mock-key
TWILIO_ACCOUNT_SID=mock-sid
```

### 4.3 Frontend - Staging (Vercel)

```bash
NG_APP_API_URL=https://cx-api-staging.sieteic.com/api/v1
NODE_ENV=staging
```

### 4.4 Frontend - Development (Vercel)

```bash
NG_APP_API_URL=https://cx-api-dev.sieteic.com/api/v1
NODE_ENV=development
```

---

## 5. FLUJO DE TRABAJO (WORKFLOW)

### 5.1 Desarrollo de Nuevas Features

```bash
# 1. Desarrollador crea feature branch
git checkout -b feature/nueva-funcionalidad

# 2. Hace cambios y commit
git add .
git commit -m "feat: nueva funcionalidad"

# 3. Push a GitHub
git push origin feature/nueva-funcionalidad

# 4. Crear Pull Request hacia 'develop'
# (Via GitHub UI)

# 5. Una vez aprobado, merge a 'develop'
# → Esto desplegará automáticamente a DEVELOPMENT

# 6. Testing en Development
# → QA prueba en: https://cx-dev.sieteic.com

# 7. Si todo OK, crear PR de 'develop' → 'phase0-4-enhancements1' (staging)
# → Esto desplegará a STAGING

# 8. Testing final en Staging
# → Usuario final prueba en: https://cx-staging.sieteic.com

# 9. Si todo OK, crear PR de 'staging' → 'main' (producción)
# → ⚠️ REVISAR MUY BIEN antes de aprobar
```

### 5.2 Automatic Deploys (GitHub Actions)

Crear archivo: `.github/workflows/deploy.yml` (ya existe en tu proyecto)

```yaml
name: Deploy Multi-Environment

on:
  push:
    branches:
      - develop          # Auto-deploy to Development
      - phase0-4-enhancements1  # Auto-deploy to Staging
      - main            # Auto-deploy to Production

jobs:
  deploy-development:
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Railway Development
        run: echo "Deploying to Development..."
        # Railway se encarga automáticamente
  
  deploy-staging:
    if: github.ref == 'refs/heads/phase0-4-enhancements1'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Railway Staging
        run: echo "Deploying to Staging..."
  
  deploy-production:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Railway Production
        run: echo "Deploying to Production..."
        # ⚠️ Requiere aprobación manual
```

---

## 6. CHECKLIST POST-DEPLOYMENT

### 6.1 Staging Environment

**Backend (Railway):**
- [ ] Proyecto creado: `siete-cx-staging`
- [ ] Branch conectado: `phase0-4-enhancements1`
- [ ] PostgreSQL agregado
- [ ] Variables de entorno configuradas
- [ ] Migraciones ejecutadas: `railway run alembic upgrade head`
- [ ] Health check: `curl https://cx-api-staging.sieteic.com/health`
- [ ] Login funciona:
  ```bash
  curl -X POST https://cx-api-staging.sieteic.com/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"test123"}'
  ```

**Frontend (Vercel):**
- [ ] Proyecto creado: `cx-staging`
- [ ] Branch conectado: `phase0-4-enhancementsfe`
- [ ] Variables configuradas: `NG_APP_API_URL`
- [ ] Build exitoso
- [ ] Sitio carga: `https://cx-staging.sieteic.com`
- [ ] Login funciona desde UI
- [ ] No hay errores CORS en consola

### 6.2 Development Environment

**Backend (Railway):**
- [ ] Proyecto creado: `siete-cx-development`
- [ ] Branch conectado: `develop`
- [ ] PostgreSQL agregado
- [ ] Variables de entorno configuradas
- [ ] Migraciones ejecutadas
- [ ] Health check funciona

**Frontend (Vercel):**
- [ ] Proyecto creado: `cx-development`
- [ ] Branch conectado: `develop`
- [ ] Variables configuradas
- [ ] Build exitoso
- [ ] Sitio carga correctamente

### 6.3 Verificación de Aislamiento

- [ ] Staging DB ≠ Production DB
- [ ] Development DB ≠ Staging DB ≠ Production DB
- [ ] Cada ambiente tiene sus propias API keys
- [ ] No hay data compartida entre ambientes

---

## 7. COMANDOS RÁPIDOS DE REFERENCIA

### Railway CLI

```bash
# Ver todos los proyectos
railway list

# Conectar a un proyecto específico
railway link siete-cx-staging

# Ver variables de entorno
railway variables

# Ver logs en tiempo real
railway logs --follow

# Ejecutar comando
railway run alembic upgrade head

# Restart service
railway restart

# Open dashboard
railway open
```

### Vercel CLI

```bash
# Ver todos los proyectos
vercel list

# Deploy a staging
vercel --prod --scope=tu-team --name=cx-staging

# Ver logs
vercel logs [deployment-url]

# Listar deployments
vercel ls

# Promover deployment anterior
vercel promote [deployment-url]
```

---

## 8. TROUBLESHOOTING

### Error: "Database connection failed"

```bash
# Verificar que POSTGRES_URI está configurado
railway variables | grep POSTGRES

# Reconectar database
railway link siete-cx-staging
railway add --database postgres
```

### Error: "CORS policy blocked"

```bash
# Verificar CORS_ORIGINS incluye el frontend URL
railway variables | grep CORS

# Actualizar:
railway variables set CORS_ORIGINS=https://cx-staging.sieteic.com,http://localhost:4200
```

### Error: "Build failed on Vercel"

```bash
# Verificar Node version (debe ser 18+)
# Agregar a vercel.json:
{
  "buildCommand": "npm install --legacy-peer-deps && npm run build"
}
```

---

## 9. PRÓXIMOS PASOS

1. ✅ **Guardar código en GitHub** (branch `phase0-4-enhancements1`)
2. ✅ **Crear ambientes Staging y Development** siguiendo esta guía
3. ✅ **Testing en Staging** con usuario final
4. ✅ **Pasar a tu equipo dev** la guía de desarrollo (`GUIA_DESARROLLADOR.md`)
5. ⏳ **Implementar frontend Angular** con las nuevas APIs
6. ⏳ **Testing completo E2E** en Staging
7. ⏳ **Deploy a Producción** solo cuando Staging esté 100% estable

---

## ❓ SOPORTE

**Si algo no funciona:**
1. Revisa logs: `railway logs` o `vercel logs`
2. Verifica variables de entorno
3. Confirma que las migraciones corrieron: `railway run alembic current`
4. Contacta al equipo de desarrollo

---

**¡Listo para deployment seguro sin afectar producción!** 🚀
