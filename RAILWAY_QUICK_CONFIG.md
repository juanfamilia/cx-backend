# 🚀 Railway Quick Configuration Reference

## ✅ Exact Settings for Railway Dashboard

Copy these exact values into your Railway settings:

---

### 📁 Build Configuration

**Builder Type:**
```
Dockerfile
```

**Dockerfile Path:**
```
cx-backend/Dockerfile
```

**Root Directory:** *(optional, leave empty or set to)*
```
cx-backend
```

---

### 🔧 Environment Variables

Go to **Variables** tab and add:

**Required Variables:**
```bash
PROJECT_NAME=Siete CX Backend
API_URL=/api/v1
JWT_SECRET_KEY=<paste-your-generated-key-here>
JWT_ALGORITHM=HS256
JWT_EXPIRE=1440
POSTGRES_URI=${{Postgres.DATABASE_URL}}
```

**To generate JWT_SECRET_KEY, run locally:**
```bash
openssl rand -hex 32
```

---

### 📝 Step-by-Step Setup

1. **Select Builder**
   - Settings → Build → Builder → Select **"Dockerfile"**

2. **Set Dockerfile Path**
   - Dockerfile Path field → Enter: `cx-backend/Dockerfile`
   - Press Enter to save

3. **Add Database** (if not already added)
   - Project Dashboard → "+ New" → Database → PostgreSQL

4. **Set Environment Variables**
   - Service → Variables tab
   - Click "+ New Variable"
   - Add each variable from the list above
   - Make sure `POSTGRES_URI=${{Postgres.DATABASE_URL}}` references your database

5. **Deploy**
   - Go to Deployments tab
   - Click "Redeploy" or push new commit to GitHub

---

### ✅ What You Should See in Build Logs

**Success looks like:**

```
✓ Found Dockerfile at cx-backend/Dockerfile
✓ Building Docker image
✓ Step 1/7 : FROM python:3.13-slim
✓ Step 2/7 : RUN apt-get update...
✓ Step 3/7 : WORKDIR /app
✓ Step 4/7 : COPY requirements.txt .
✓ Step 5/7 : RUN pip install...
✓ Successfully installed [packages]
✓ Step 6/7 : COPY . .
✓ Step 7/7 : CMD uvicorn...
✓ Build complete
✓ Deploying...
✓ Started uvicorn on 0.0.0.0:$PORT
✓ Application startup complete
✓ Deployment successful
```

---

### ❌ What You Should NOT See

```
✖ Railpack could not determine how to build the app
✖ Script start.sh not found
✖ No Python application detected
```

If you see these errors, double-check:
- Dockerfile Path is set to `cx-backend/Dockerfile`
- The path doesn't have extra spaces
- Builder is set to "Dockerfile" not "Nixpacks" or "Railpack"

---

### 🧪 Test Your Deployment

After successful deployment, test with:

```bash
# Replace with your Railway URL
curl https://your-app.up.railway.app/api/v1/health

# Expected response:
{"status":"healthy","version":"1.0.0"}
```

Or open in browser:
```
https://your-app.up.railway.app/api/v1/health
```

---

### 🔄 After First Successful Deploy

Run database migrations:

**Option 1: Railway CLI**
```bash
railway run alembic upgrade head
```

**Option 2: One-time deployment command**
Add to Settings → Deploy → Override Start Command (temporarily):
```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
Then redeploy, and after success, remove the override.

---

### 📊 Project Structure Reminder

Your repository structure:
```
/app/
├── cx-backend/              ← Railway should build from here
│   ├── Dockerfile          ← This is the file Railway needs
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── models/
│   │   └── routes/
│   └── alembic/
├── cx-frontend/
└── ...
```

Railway Configuration:
- **Dockerfile Path**: Points to `cx-backend/Dockerfile`
- **Build Context**: Entire `cx-backend/` directory
- **Working Directory**: `/app` (inside container)

---

### 🆘 Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| "Dockerfile not found" | Check path is `cx-backend/Dockerfile` (no leading `/`) |
| "Railpack building" | Change Builder to "Dockerfile" |
| "Port binding error" | Verify Dockerfile uses `${PORT:-8001}` |
| "Database connection error" | Check `POSTGRES_URI=${{Postgres.DATABASE_URL}}` |
| "Module not found" | Check `requirements.txt` is in `cx-backend/` |
| "Build cache issues" | Settings → Advanced → Clear Build Cache |

---

### 💡 Pro Tips

1. **Don't edit these files in Railway**, edit in your repo and push to GitHub
2. **Use Railway's reference variables** like `${{Postgres.DATABASE_URL}}` for automatic linking
3. **Generate a strong JWT secret** - don't use default values in production
4. **Monitor first deployment** closely to catch any errors early
5. **Keep logs open** during first deploy to see what's happening

---

### 🎯 TL;DR - Just Copy This

**In Railway Dashboard:**

1. **Settings → Build:**
   - Builder: `Dockerfile`
   - Dockerfile Path: `cx-backend/Dockerfile`

2. **Variables:**
   ```
   POSTGRES_URI=${{Postgres.DATABASE_URL}}
   JWT_SECRET_KEY=<generate-with-openssl-rand>
   JWT_ALGORITHM=HS256
   JWT_EXPIRE=1440
   PROJECT_NAME=Siete CX Backend
   API_URL=/api/v1
   ```

3. **Deploy:**
   - Deployments → Redeploy

**That's it! 🚀**

---

### 📞 Still Stuck?

If deployment fails:
1. Share the build logs (copy full text)
2. Share a screenshot of your Build settings
3. Confirm the Dockerfile Path value
4. I'll help debug the specific issue!
