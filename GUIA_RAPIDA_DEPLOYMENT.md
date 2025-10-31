# 🎯 GUÍA RÁPIDA: DEPLOYMENT STAGING/DEVELOPMENT - SIETE CX

**Para:** Juan  
**Tiempo:** 20-30 minutos  
**Objetivo:** Crear ambientes de testing SIN afectar producción

---

## ✅ PASO 1: CONFIRMAR GITHUB (Emergent)

### Backend:
1. Busca botón **"Save to GitHub"** en el chat
2. Configura:
   - Repository: `juanfamilia/cx-backend`
   - Branch: `phase0-4-enhancements1` ← **NUEVO** (no toca main)
   - Folder: `/app/cx-backend`
3. Click "Save" y espera ~2 minutos

### Frontend:
- ✅ **No necesitas guardar nada** (no hay cambios)

### Verificar:
Ve a: `https://github.com/juanfamilia/cx-backend/branches`  
Deberías ver: `phase0-4-enhancements1` ✅

---

## 🚀 PASO 2: CREAR STAGING EN RAILWAY

### 2.1 Crear Proyecto Nuevo

1. Ve a: https://railway.app/dashboard
2. Click **"New Project"**
3. Nombre: `siete-cx-staging`
4. Click **"Deploy from GitHub repo"**
5. Selecciona: `juanfamilia/cx-backend`
6. Branch: `phase0-4-enhancements1` ← **IMPORTANTE**
7. Click "Deploy"

### 2.2 Agregar Base de Datos

1. En el proyecto → Click **"+ New"**
2. Click **"Database"** → **"PostgreSQL"**
3. Railway creará la DB automáticamente

### 2.3 Configurar Variables de Entorno

En tu proyecto → **"Variables"** → Agregar:

```bash
# Básicas
PROJECT_NAME=Siete CX Staging
ENVIRONMENT=staging
JWT_SECRET_KEY=[ver abajo cómo generar]
JWT_ALGORITHM=HS256
JWT_EXPIRE=1440

# Database (auto)
POSTGRES_URI=${{Postgres.DATABASE_URL}}

# CORS (importante)
CORS_ORIGINS=https://cx-staging.sieteic.com,http://localhost:4200

# OpenAI (si tienes key de test)
OPENAI_API_KEY=sk-tu-key-aqui

# Opcional: SendGrid, Twilio (puedes agregar después)
```

**Generar JWT_SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2.4 Configurar Build Command

1. En tu proyecto → **"Settings"** → **"Deploy"**
2. **Build Command:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Start Command:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

### 2.5 Ejecutar Migraciones

**Opción A: Via CLI**
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Conectar a staging
railway link siete-cx-staging

# Ejecutar migraciones
railway run alembic upgrade head
```

**Opción B: Via Railway Dashboard**
1. En tu proyecto → Click en el servicio backend
2. Click **"Settings"** → **"Deploy"**
3. Agregar **"Deploy Command":**
   ```bash
   alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

### 2.6 Obtener URL

1. En tu proyecto → Click en el servicio
2. Ve a **"Settings"** → **"Networking"**
3. Verás una URL como: `https://siete-cx-staging.up.railway.app`

**Probar:**
```bash
curl https://tu-url-staging.railway.app/health
```

---

## 🎨 PASO 3: CREAR STAGING EN VERCEL

### 3.1 Crear Proyecto

1. Ve a: https://vercel.com/dashboard
2. Click **"Add New"** → **"Project"**
3. Import: `juanfamilia/cx-frontend`
4. Nombre: `cx-staging`
5. Branch: `phase0-4-enhancementsfe`
6. Framework: **Angular**
7. **Build Command:**
   ```bash
   npm install && npm run build
   ```
8. **Output Directory:**
   ```bash
   dist/cx-frontend/browser
   ```
9. Click **"Deploy"**

### 3.2 Configurar Variables

En el proyecto → **"Settings"** → **"Environment Variables"**:

```bash
NG_APP_API_URL=https://tu-url-staging.railway.app/api/v1
NODE_ENV=staging
```

### 3.3 Redeploy

1. Ve a **"Deployments"**
2. Click en el último deployment → **"Redeploy"**

### 3.4 Obtener URL

Vercel te dará una URL como:
- `https://cx-staging.vercel.app`

---

## 🧪 PASO 4: PROBAR STAGING

### Backend:
```bash
# Health check
curl https://tu-url-staging.railway.app/health

# Login
curl -X POST https://tu-url-staging.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}'
```

### Frontend:
1. Abre: `https://cx-staging.vercel.app`
2. Intenta hacer login
3. Abre consola del navegador (F12)
4. Verifica que no hay errores CORS

---

## 🔄 PASO 5: REPETIR PARA DEVELOPMENT

### Railway Development:
1. Crear proyecto: `siete-cx-development`
2. Branch: `develop` (primero créalo en GitHub)
3. Mismos pasos que staging

### Vercel Development:
1. Crear proyecto: `cx-development`
2. Branch: `develop`
3. Mismos pasos que staging

---

## 📊 RESUMEN FINAL

| Ambiente | Backend Railway | Frontend Vercel | Afecta Producción? |
|----------|----------------|-----------------|-------------------|
| **Production** | (existente) | (existente) | ✅ SÍ |
| **Staging** | siete-cx-staging | cx-staging | ❌ NO |
| **Development** | siete-cx-development | cx-development | ❌ NO |

### URLs Finales:

**Staging:**
- Backend: `https://siete-cx-staging.up.railway.app`
- Frontend: `https://cx-staging.vercel.app`

**Development:**
- Backend: `https://siete-cx-development.up.railway.app`
- Frontend: `https://cx-development.vercel.app`

---

## ⚠️ IMPORTANTE

### ✅ LO QUE ES SEGURO:
- Crear nuevos proyectos en Railway/Vercel
- Usar branches diferentes (`phase0-4-enhancements1`, `develop`)
- Cada ambiente tiene su propia base de datos

### ❌ LO QUE NO DEBES HACER:
- NO cambiar el branch de producción
- NO usar la misma base de datos
- NO deployar directamente a `main` hasta probar en staging

---

## 🎯 PRÓXIMOS PASOS

1. ✅ **Ahora:** Guarda en GitHub usando "Save to GitHub"
2. ✅ **Después:** Crea staging siguiendo esta guía
3. ✅ **Probar:** Todo funciona en staging
4. ✅ **Entregar:** Pasa `GUIA_DESARROLLADOR.md` a tu equipo
5. ⏳ **Luego:** Ellos implementan el frontend Angular
6. ⏳ **Finalmente:** Deploy a producción

---

## ❓ DUDAS COMUNES

**¿Y si algo sale mal en staging?**  
→ No pasa nada, producción sigue funcionando normal

**¿Necesito dominio custom ahora?**  
→ No, puedes usar las URLs de Railway/Vercel

**¿Cuánto cuesta esto?**  
→ Railway: ~$5/mes por ambiente  
→ Vercel: Gratis para staging/dev

**¿Puedo eliminar staging después?**  
→ Sí, simplemente elimina el proyecto en Railway/Vercel

---

**¡Listo! Ahora puedes probar sin miedo** 🚀
