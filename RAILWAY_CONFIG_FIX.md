# Railway Configuration Fix - Root Directory Issue

## ❌ Current Problem

Railway build is failing with:
```
✖ Railpack could not determine how to build the app.
```

**Root Cause:** Railway is looking in the wrong directory. Your project structure is:
```
/app/
├── cx-backend/          ← Backend code is HERE
│   ├── app/
│   ├── Dockerfile       ← Dockerfile is HERE
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── ...
├── cx-frontend/
├── backend/             (ignored)
└── frontend/            (ignored)
```

But Railway is trying to build from `/app/` (root) instead of `/app/cx-backend/`.

---

## ✅ Solution: Configure Root Directory in Railway

### Method 1: Set Root Directory (RECOMMENDED)

**Step-by-step in Railway Dashboard:**

1. **Go to your Railway project**
   - https://railway.app/dashboard
   - Select your Siete CX backend service

2. **Open Settings**
   - Click **Settings** tab (gear icon)

3. **Find Source Section**
   - Scroll down to **"Source"** or **"Deploy"** section

4. **Set Root Directory**
   - Look for **"Root Directory"** field
   - Enter: `cx-backend`
   - Save changes (auto-saves)

5. **Configure Builder (if needed)**
   - In **"Build"** section
   - **Builder**: Select **"Dockerfile"**
   - **Dockerfile Path**: Should auto-detect as `Dockerfile`

6. **Redeploy**
   - Go to **Deployments** tab
   - Click **"Redeploy"** or it will auto-deploy

---

### Method 2: Use Railway CLI

If you prefer command line:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Set root directory
railway set-config --root-directory cx-backend

# Set builder to Dockerfile
railway set-config --builder dockerfile

# Deploy
railway up
```

---

### Method 3: Move Files to Root (Alternative)

If you can't configure root directory, we can restructure:

**Option A: Move backend to root**
```bash
# This would move cx-backend contents to /app/
# NOT RECOMMENDED - disrupts current structure
```

**Option B: Create railway.toml**
Create `/app/railway.toml`:
```toml
[build]
builder = "dockerfile"
dockerfilePath = "cx-backend/Dockerfile"
```

---

## 📸 Visual Guide

### Railway Dashboard Settings:

```
┌─────────────────────────────────────────┐
│ Settings                                │
├─────────────────────────────────────────┤
│                                         │
│ Source                                  │
│ ┌─────────────────────────────────┐   │
│ │ Root Directory                  │   │
│ │ [cx-backend                    ]│   │  ← Enter this
│ └─────────────────────────────────┘   │
│                                         │
│ Build                                   │
│ ┌─────────────────────────────────┐   │
│ │ Builder: [Dockerfile        ▼] │   │  ← Select this
│ │ Dockerfile Path: Dockerfile     │   │
│ └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🔍 Verify Configuration

After setting root directory, Railway should detect:

✅ **Python application** in `cx-backend/`  
✅ **Dockerfile** at `cx-backend/Dockerfile`  
✅ **requirements.txt** at `cx-backend/requirements.txt`  

The build logs should show:
```
[inf] using build driver dockerfile
[inf] Building Dockerfile
[inf] Step 1/7 : FROM python:3.13-slim
...
```

Instead of:
```
[inf] using build driver railpack-v0.9.2
[inf] ✖ Railpack could not determine how to build the app.
```

---

## 🚀 Expected Deployment Flow

After configuration:

1. **Detection Phase**
   ```
   ✓ Found Dockerfile at cx-backend/Dockerfile
   ✓ Using Docker builder
   ```

2. **Build Phase**
   ```
   ✓ Installing dependencies from requirements.txt
   ✓ Copying application files
   ✓ Building image
   ```

3. **Deploy Phase**
   ```
   ✓ Starting container
   ✓ Running uvicorn on port $PORT
   ✓ Application ready
   ```

4. **Health Check**
   ```
   ✓ HTTP 200 response
   ✓ Service healthy
   ```

---

## 🆘 Still Having Issues?

### Issue: Can't find "Root Directory" field

**Railway UI may vary by version. Look for:**
- "Root Directory"
- "Service Root"
- "Working Directory"
- "Build Path"

**Alternative:** Create `railway.json` in project root:
```json
{
  "build": {
    "builder": "dockerfile",
    "dockerfilePath": "cx-backend/Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/api/v1/health"
  }
}
```

### Issue: Dockerfile not detected

**Check:**
1. Dockerfile exists at `/app/cx-backend/Dockerfile`
2. No `.dockerignore` blocking it
3. File is committed to git

**Solution:**
```bash
# Verify Dockerfile exists
ls -la /app/cx-backend/Dockerfile

# Should show:
-rw-r--r-- 1 root root 291 Nov 1 15:00 /app/cx-backend/Dockerfile
```

### Issue: Build still fails after configuration

**Try:**
1. **Clear Railway cache**
   - Settings → Advanced → Clear Build Cache
   - Redeploy

2. **Force Dockerfile builder**
   - Settings → Build → Builder → Force "Dockerfile"

3. **Check environment variables**
   - Variables tab → Ensure `POSTGRES_URI=${{Postgres.DATABASE_URL}}` is set

---

## 📋 Deployment Checklist

Before deploying, ensure:

- [ ] Root Directory set to `cx-backend`
- [ ] Builder set to "Dockerfile"
- [ ] PostgreSQL database is added to project
- [ ] Environment variables configured:
  - `POSTGRES_URI=${{Postgres.DATABASE_URL}}`
  - `JWT_SECRET_KEY=<generated-key>`
  - `JWT_ALGORITHM=HS256`
  - `JWT_EXPIRE=1440`
  - `PROJECT_NAME=Siete CX Backend`
  - `API_URL=/api/v1`
- [ ] Branch `phase0-4-enhancements1` is selected
- [ ] Latest changes are pushed to GitHub

---

## 🎯 Quick Fix Summary

**The Problem:** Railway can't find your app because it's in a subdirectory.

**The Solution:** Tell Railway to look in `cx-backend` directory.

**How to Fix:**
1. Railway Dashboard → Your Service → Settings
2. Set **Root Directory** to `cx-backend`
3. Set **Builder** to `Dockerfile`
4. Redeploy

**Expected Result:** Build succeeds and app deploys! 🚀

---

## 📞 Need Help?

If you're still stuck:
1. Share a screenshot of your Railway Settings page
2. Share the full build logs
3. Confirm the root directory setting is saved

I can provide more specific guidance based on what you're seeing!
