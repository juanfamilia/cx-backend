# 🚀 Deployment Next Steps - Siete CX Backend

## ✅ What Has Been Fixed

The critical SQLAlchemy async engine error has been resolved:

### Changes Applied:
1. **Fixed async database connection** (`app/core/db.py`)
   - Removed incorrect `AsyncAdaptedQueuePool` usage
   - Let SQLAlchemy automatically manage the connection pool

2. **Added automatic URL conversion** (`app/core/config.py`)
   - Railway's PostgreSQL URLs are now automatically converted to async format
   - `postgresql://` → `postgresql+asyncpg://`

3. **Created comprehensive guides:**
   - `docs/RAILWAY_SETUP_GUIDE.md` - Complete Railway deployment guide
   - `RAILWAY_FIX_SUMMARY.md` - Technical details of the fix

---

## 📋 Step-by-Step Deployment Instructions

### STEP 1: Save Changes to GitHub

Since Emergent's "Save to GitHub" feature has limitations, we'll prepare the files for you to push manually.

**Option A: Using Emergent's "Save to GitHub" Feature**

1. Click the **"Save to GitHub"** button in the chat interface
2. Select all modified files:
   - `app/core/config.py`
   - `app/core/db.py`
   - `docs/RAILWAY_SETUP_GUIDE.md`
   - `RAILWAY_FIX_SUMMARY.md`
3. Commit message: `fix: resolve SQLAlchemy async engine configuration for Railway deployment`
4. Push to branch: `phase0-4-enhancements1`

**Option B: Manual Git Push (if Option A fails)**

I can prepare a script for you to run locally. Would you like me to create it?

---

### STEP 2: Deploy to Railway

#### 2.1 Create PostgreSQL Database (if not done)

1. Go to Railway Dashboard: https://railway.app/dashboard
2. Open your project
3. Click **"+ New"** → **"Database"** → **"PostgreSQL"**
4. Wait for provisioning (1-2 minutes)

#### 2.2 Configure Environment Variables

Go to your backend service → **Variables** tab and add:

**REQUIRED VARIABLES:**
```bash
PROJECT_NAME=Siete CX Backend
API_URL=/api/v1
JWT_SECRET_KEY=<GENERATE_THIS>
JWT_ALGORITHM=HS256
JWT_EXPIRE=1440
POSTGRES_URI=${{Postgres.DATABASE_URL}}
```

**To generate JWT_SECRET_KEY:**
```bash
# Run this command in your terminal
openssl rand -hex 32
```

**OPTIONAL (for full features):**
```bash
OPENAI_API_KEY=sk-...
CLOUDFLARE_STREAM_KEY=...
CLOUDFLARE_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=siete-cx-videos
R2_ENDPOINT_URL=...
```

#### 2.3 Deploy

1. If already connected to GitHub:
   - Railway should auto-deploy when you push the fix
   - Monitor in **Deployments** tab

2. If not connected:
   - Click **"Deploy from GitHub"**
   - Select repository: `juanfamilia/cx-backend`
   - Select branch: `phase0-4-enhancements1`

#### 2.4 Monitor Deployment

Watch the deployment logs for:
```
✅ Successfully installed requirements
✅ Starting uvicorn
✅ Application startup complete
✅ Uvicorn running on http://0.0.0.0:8001
```

#### 2.5 Run Database Migrations

After successful deployment:

**Using Railway CLI:**
```bash
railway run alembic upgrade head
```

**OR add to start command:**
```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

### STEP 3: Verify Backend Deployment

Test your API (replace with your Railway URL):

```bash
# Get your Railway URL from the dashboard
curl https://your-app.up.railway.app/api/v1/health

# Expected response
{"status": "healthy", "version": "1.0.0"}
```

---

### STEP 4: Deploy Frontend to Vercel

#### 4.1 Prepare Frontend

1. Ensure Angular frontend is ready in `/app/cx-frontend`
2. Verify build configuration

#### 4.2 Deploy to Vercel

**Via Vercel Dashboard:**

1. Go to https://vercel.com/dashboard
2. Click **"Add New"** → **"Project"**
3. Import from GitHub: `juanfamilia/cx-frontend` (or your repo)
4. Configure:
   - Framework Preset: **Angular**
   - Root Directory: `/` (or leave default)
   - Build Command: `npm run build` (or default)
   - Output Directory: `dist/cx-frontend` (Angular default)

**Environment Variables in Vercel:**
```bash
NG_APP_API_URL=https://your-railway-app.up.railway.app/api/v1
NODE_ENV=production
```

5. Click **"Deploy"**

#### 4.3 Update CORS

After getting your Vercel URL, update backend CORS:

**File:** `/app/cx-backend/app/main.py`
```python
origins = [
    "https://cx.sieteic.com",
    "http://localhost:4200",
    "https://your-vercel-app.vercel.app"  # Add this
]
```

Commit and push this change to trigger Railway redeploy.

---

### STEP 5: End-to-End Testing

1. ✅ Backend health check responds
2. ✅ Frontend loads successfully
3. ✅ Login/authentication works
4. ✅ API calls from frontend to backend work
5. ✅ Database operations function correctly

---

## 🔧 Troubleshooting

### Issue: "Application failed to respond" on Railway

**Check:**
1. All environment variables are set
2. `POSTGRES_URI=${{Postgres.DATABASE_URL}}` is configured
3. PostgreSQL database is running
4. View deployment logs for specific errors

**Solution:**
```bash
# Check logs
railway logs

# Restart service
railway service restart
```

### Issue: Frontend can't connect to backend

**Check:**
1. Backend is deployed and responding
2. Vercel environment variable `NG_APP_API_URL` points to Railway URL
3. CORS is configured with Vercel domain
4. API endpoints use correct `/api/v1` prefix

**Solution:**
- Verify Railway URL in Vercel env vars
- Check browser console for CORS errors
- Update backend CORS origins if needed

### Issue: Database connection errors

**Check:**
1. PostgreSQL service is running in Railway
2. `POSTGRES_URI` references correct database
3. Migrations have been run

**Solution:**
```bash
# Run migrations
railway run alembic upgrade head

# Check database status
railway status
```

---

## 📚 Reference Documents

All guides are now in the repository:

1. **`/docs/RAILWAY_SETUP_GUIDE.md`**
   - Complete Railway setup walkthrough
   - Environment variable details
   - CLI commands reference

2. **`/RAILWAY_FIX_SUMMARY.md`**
   - Technical explanation of the fix
   - Before/after code comparison
   - Testing procedures

3. **`/docs/DEPLOYMENT.md`**
   - Overall deployment architecture
   - Multi-environment setup
   - Domain configuration

---

## ✅ Deployment Checklist

### Pre-Deployment
- [x] SQLAlchemy async fix applied
- [x] Code linted and validated
- [ ] Changes committed to GitHub
- [ ] Branch: `phase0-4-enhancements1` is up to date

### Railway Backend
- [ ] PostgreSQL database created
- [ ] Environment variables configured
- [ ] Service deployed successfully
- [ ] Migrations applied
- [ ] Health endpoint responding
- [ ] Logs show no errors

### Vercel Frontend
- [ ] Project created in Vercel
- [ ] Environment variables set
- [ ] Build successful
- [ ] Frontend accessible
- [ ] API calls working

### Post-Deployment
- [ ] End-to-end testing complete
- [ ] Authentication working
- [ ] All main features functional
- [ ] Custom domains configured (optional)
- [ ] Monitoring set up

---

## 🎯 Current Status

**Backend Fix:** ✅ COMPLETE
- Database connection issue resolved
- Ready for Railway deployment
- All files prepared and linted

**Next Action Required:** 
1. Push changes to GitHub (use "Save to GitHub" or manual push)
2. Deploy to Railway
3. Configure environment variables
4. Run migrations
5. Test API endpoints

---

## 💡 Quick Start Commands

```bash
# Railway CLI Setup (if using CLI)
npm install -g @railway/cli
railway login
railway link

# Deploy
railway up

# Run migrations
railway run alembic upgrade head

# Check logs
railway logs

# Check status
railway status

# Open dashboard
railway open
```

---

## 🆘 Need Help?

If you encounter any issues:

1. **Check the detailed guides** in `/docs` folder
2. **Review deployment logs** in Railway dashboard
3. **Verify environment variables** are correctly set
4. **Check database connection** in Railway
5. **Ask me!** I can help troubleshoot specific errors

---

**Ready to deploy? Let me know if you need help with any step!** 🚀
