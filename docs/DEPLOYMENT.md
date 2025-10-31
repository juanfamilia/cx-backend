# SIETE CX - DEPLOYMENT DOCUMENTATION

**Version:** 1.0  
**Last Updated:** January 2025  
**Platform:** Railway.app + Vercel

---

## TABLE OF CONTENTS

1. [Deployment Overview](#1-deployment-overview)
2. [Railway Backend Deployment](#2-railway-backend-deployment)
3. [Vercel Frontend Deployment](#3-vercel-frontend-deployment)
4. [Environment Variables](#4-environment-variables)
5. [Database Migrations](#5-database-migrations)
6. [Post-Deployment Checklist](#6-post-deployment-checklist)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. DEPLOYMENT OVERVIEW

### 1.1 Architecture

```
┌─────────────────────────────────────────────┐
│           Users (Browser/Mobile)            │
└─────────────────┬───────────────────────────┘
                  │
      ┌───────────┴───────────┐
      │                       │
      ▼                       ▼
┌──────────┐           ┌──────────┐
│  Vercel  │           │ Railway  │
│ Frontend │◄─────────►│ Backend  │
│ Angular  │   API     │ FastAPI  │
└──────────┘           └────┬─────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  PostgreSQL  │
                     │   Database   │
                     └──────────────┘
```

### 1.2 Services

| Service | Platform | URL Pattern | Purpose |
|---------|----------|-------------|---------|
| Frontend | Vercel | `cx.sieteic.com` | Angular 19 SPA |
| Backend | Railway | `cx-api.sieteic.com` | FastAPI REST API |
| Database | Railway | Internal | PostgreSQL 14+ |

---

## 2. RAILWAY BACKEND DEPLOYMENT

### 2.1 Prerequisites

- Railway account
- GitHub repository connected
- PostgreSQL database provisioned on Railway

### 2.2 Initial Setup

**Step 1: Create New Project**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init
```

**Step 2: Connect GitHub Repository**
1. Go to Railway dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose `juanfamilia/cx-backend`
5. Select branch: `phase0-4-enhancements1`

**Step 3: Add PostgreSQL Database**
1. In project dashboard, click "+ New"
2. Select "Database" → "PostgreSQL"
3. Database will be automatically provisioned
4. Connection string available in variables

### 2.3 Configuration

**Root Directory:** `/` (or leave empty if deploying from repo root)

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:** (See section 4)

### 2.4 Custom Domain

1. Go to Settings → Domains
2. Click "Generate Domain" or "Custom Domain"
3. Add `cx-api.sieteic.com`
4. Update DNS records:
   ```
   Type: CNAME
   Name: cx-api
   Value: [railway-domain].railway.app
   ```

### 2.5 Railway CLI Deployment

```bash
# Link to project
railway link

# Deploy
railway up

# Run migrations
railway run alembic upgrade head

# View logs
railway logs

# Open app
railway open
```

---

## 3. VERCEL FRONTEND DEPLOYMENT

### 3.1 Prerequisites

- Vercel account
- GitHub repository connected

### 3.2 Deployment Steps

**Step 1: Import Project**
1. Go to Vercel dashboard
2. Click "Add New" → "Project"
3. Import `juanfamilia/cx-frontend`
4. Select branch: `phase0-4-enhancementsfe`

**Step 2: Configure Build Settings**

**Framework Preset:** Angular

**Root Directory:** `/` (leave empty)

**Build Command:**
```bash
npm install && npm run build
```

**Output Directory:**
```bash
dist/cx-frontend/browser
```

**Install Command:**
```bash
npm install
```

### 3.3 Environment Variables

Add in Vercel dashboard (Settings → Environment Variables):

```bash
NG_APP_API_URL=https://cx-api.sieteic.com/api/v1
NODE_ENV=production
```

### 3.4 Custom Domain

1. Go to Settings → Domains
2. Add `cx.sieteic.com`
3. Update DNS records:
   ```
   Type: A
   Name: cx
   Value: 76.76.21.21
   
   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   ```

### 3.5 Vercel CLI Deployment

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# Deploy to production
vercel --prod
```

---

## 4. ENVIRONMENT VARIABLES

### 4.1 Backend (Railway)

**Required:**
```bash
# Project
PROJECT_NAME=Siete CX Backend
PROJECT_URL=https://cx-api.sieteic.com
API_URL=/api/v1

# JWT Authentication
JWT_SECRET_KEY=[generate-secure-key]
JWT_ALGORITHM=HS256
JWT_EXPIRE=1440

# PostgreSQL (auto-provided by Railway)
POSTGRES_URI=${{Postgres.DATABASE_URL}}

# OpenAI API
OPENAI_API_KEY=sk-[your-key]

# Cloudflare Stream
CLOUDFLARE_STREAM_KEY=[your-key]
CLOUDFLARE_ACCOUNT_ID=[your-account-id]

# Cloudflare R2
R2_ACCESS_KEY_ID=[your-key]
R2_SECRET_ACCESS_KEY=[your-secret]
R2_BUCKET=siete-cx-videos
R2_ENDPOINT_URL=[your-endpoint]
```

**Optional (Phase 4):**
```bash
# SendGrid (Email)
SENDGRID_API_KEY=SG.[your-key]
SENDGRID_FROM_EMAIL=noreply@sieteic.com
SENDGRID_FROM_NAME=Siete CX

# Twilio (SMS)
TWILIO_ACCOUNT_SID=AC[your-sid]
TWILIO_AUTH_TOKEN=[your-token]
TWILIO_FROM_NUMBER=+1234567890

# AWS S3 (Optional/Legacy)
AWS_ACCESS_KEY_ID=[your-key]
AWS_SECRET_ACCESS_KEY=[your-secret]
AWS_BUCKET_NAME=siete-cx-files
```

### 4.2 Frontend (Vercel)

```bash
NG_APP_API_URL=https://cx-api.sieteic.com/api/v1
NODE_ENV=production
```

### 4.3 Generating JWT Secret

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32
```

---

## 5. DATABASE MIGRATIONS

### 5.1 Running Migrations

**On Railway:**
```bash
# Using Railway CLI
railway run alembic upgrade head

# Or add to deploy script
railway run --service backend alembic upgrade head
```

**Locally:**
```bash
cd /app/cx-backend
alembic upgrade head
```

### 5.2 Creating New Migration

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "Add new feature"

# Create empty migration
alembic revision -m "Custom migration"

# Edit migration file in app/migrations/versions/
# Then upgrade
alembic upgrade head
```

### 5.3 Migration Files Needed (Phase 0-4)

Create these migrations in order:

1. **prompt_managers** table
2. **dashboard_configs** table
3. **widget_definitions** table
4. **insights** table
5. **tags** table
6. **evaluation_tags** table
7. **alert_thresholds** table
8. **trends** table
9. **company_themes** table

**Run all:**
```bash
alembic upgrade head
```

---

## 6. POST-DEPLOYMENT CHECKLIST

### 6.1 Backend Health Check

```bash
# Check API is running
curl https://cx-api.sieteic.com/health

# Test login
curl -X POST https://cx-api.sieteic.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"password"}'

# Test protected endpoint
curl https://cx-api.sieteic.com/api/v1/users \
  -H "Authorization: Bearer [token]"
```

### 6.2 Frontend Health Check

```bash
# Check frontend loads
curl https://cx.sieteic.com

# Check API connection
# (Open browser dev tools → Network tab)
```

### 6.3 Database Check

```bash
# Connect to Railway PostgreSQL
railway connect postgres

# Check tables exist
\dt

# Check data
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM companies;
```

### 6.4 Feature Testing

- [ ] Login works
- [ ] Dashboard loads
- [ ] Evaluation submission works
- [ ] AI analysis triggers
- [ ] Insights generate
- [ ] Tags apply automatically
- [ ] Notifications send
- [ ] Theme loads correctly
- [ ] Exports work (Excel/PDF)

---

## 7. TROUBLESHOOTING

### 7.1 Common Issues

**Issue: "502 Bad Gateway"**
```bash
# Check backend logs
railway logs --service backend

# Verify start command is correct
# Ensure PORT variable is used: --port $PORT
```

**Issue: "Database connection failed"**
```bash
# Verify POSTGRES_URI is set
railway variables --service backend

# Check database is running
railway status

# Test connection
railway connect postgres
```

**Issue: "CORS errors in frontend"**
```bash
# Verify backend CORS_ORIGINS includes frontend URL
# In app/core/config.py or environment:
CORS_ORIGINS="https://cx.sieteic.com,http://localhost:4200"
```

**Issue: "Migration failed"**
```bash
# Check current migration version
railway run alembic current

# View migration history
railway run alembic history

# Force to specific version
railway run alembic stamp head
```

**Issue: "Frontend build fails"**
```bash
# Check Node version (should be 18+)
# Check package.json dependencies
# Run locally first:
npm install
npm run build
```

### 7.2 Logs

**Railway Logs:**
```bash
railway logs --service backend
railway logs --service backend --follow
railway logs --service backend --tail 100
```

**Vercel Logs:**
```bash
vercel logs
vercel logs [deployment-url]
```

### 7.3 Rollback

**Railway:**
```bash
# List deployments
railway status

# Rollback to previous
# (Use Railway dashboard → Deployments → Rollback)
```

**Vercel:**
```bash
# Promote previous deployment
vercel promote [previous-deployment-url]
```

---

## APPENDIX A: Railway Configuration File

**railway.json:**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "numReplicas": 1,
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

## APPENDIX B: Vercel Configuration File

**vercel.json:**
```json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "dist/cx-frontend/browser"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}
```

---

## APPENDIX C: Health Check Endpoints

**Add to app/main.py:**
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health/db")
async def health_check_db(session: AsyncSession = Depends(get_db)):
    try:
        await session.execute(text("SELECT 1"))
        return {"database": "connected"}
    except Exception as e:
        return {"database": "error", "message": str(e)}
```

---

**End of Deployment Documentation**

For testing procedures, see `TESTING.md`.  
For architecture details, see `ARCHITECTURE_MASTER.md`.
