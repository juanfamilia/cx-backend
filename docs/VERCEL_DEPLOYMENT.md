# VERCEL DEPLOYMENT GUIDE - SIETE CX FRONTEND

**Platform:** Vercel  
**Framework:** Angular 19  
**Repository:** `github.com/juanfamilia/cx-frontend`  
**Branch:** `phase0-4-enhancementsfe`

---

## 🚀 QUICK DEPLOYMENT STEPS

### Option 1: Vercel Dashboard (Recommended)

#### Step 1: Import Project
1. Go to https://vercel.com/dashboard
2. Click **"Add New..."** → **"Project"**
3. Click **"Import Git Repository"**
4. Search for `juanfamilia/cx-frontend`
5. Click **"Import"**

#### Step 2: Configure Project

**Framework Preset:** `Angular`

**Root Directory:** Leave empty or `/`

**Build Settings:**
```bash
Build Command: npm run build
Output Directory: dist/cx-frontend/browser
Install Command: npm install
```

**Node.js Version:** `18.x` (or `20.x`)

#### Step 3: Environment Variables

Click **"Environment Variables"** and add:

| Name | Value | Environment |
|------|-------|-------------|
| `NG_APP_API_URL` | `https://cx-api.sieteic.com/api/v1` | Production |
| `NODE_ENV` | `production` | Production |
| `NG_APP_API_URL` | `http://localhost:8000/api/v1` | Development |

#### Step 4: Deploy

1. Click **"Deploy"**
2. Wait for build to complete (~2-3 minutes)
3. Once deployed, you'll get a URL like: `cx-frontend-xxx.vercel.app`

#### Step 5: Custom Domain

1. Go to **Settings** → **Domains**
2. Click **"Add Domain"**
3. Enter: `cx.sieteic.com`
4. Follow DNS instructions:
   ```
   Type: A
   Name: cx (or @)
   Value: 76.76.21.21
   
   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   ```
5. Wait for DNS propagation (5-60 minutes)

---

### Option 2: Vercel CLI

#### Step 1: Install Vercel CLI
```bash
npm install -g vercel
```

#### Step 2: Login
```bash
vercel login
```

#### Step 3: Navigate to Project
```bash
cd /app/cx-frontend
```

#### Step 4: Deploy
```bash
# First deployment (preview)
vercel

# Production deployment
vercel --prod
```

#### Step 5: Set Environment Variables
```bash
vercel env add NG_APP_API_URL production
# Enter: https://cx-api.sieteic.com/api/v1

vercel env add NODE_ENV production
# Enter: production
```

#### Step 6: Redeploy with Variables
```bash
vercel --prod
```

---

## 📋 CONFIGURATION FILES

### vercel.json
Create `/app/cx-frontend/vercel.json`:

```json
{
  "version": 2,
  "name": "siete-cx-frontend",
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
      "src": "/assets/(.*)",
      "dest": "/assets/$1"
    },
    {
      "src": "/(.*\\.(js|css|ico|png|jpg|svg|woff|woff2))",
      "dest": "/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
```

### package.json Scripts
Ensure these scripts exist in `/app/cx-frontend/package.json`:

```json
{
  "scripts": {
    "ng": "ng",
    "start": "ng serve",
    "build": "ng build --configuration production",
    "build:prod": "ng build --configuration production",
    "test": "ng test",
    "lint": "ng lint"
  }
}
```

### angular.json Build Configuration
Verify production configuration in `angular.json`:

```json
{
  "projects": {
    "cx-frontend": {
      "architect": {
        "build": {
          "configurations": {
            "production": {
              "outputPath": "dist/cx-frontend/browser",
              "optimization": true,
              "sourceMap": false,
              "buildOptimizer": true,
              "budgets": [
                {
                  "type": "initial",
                  "maximumWarning": "2mb",
                  "maximumError": "5mb"
                }
              ]
            }
          }
        }
      }
    }
  }
}
```

---

## 🔧 TROUBLESHOOTING

### Issue: "Build Failed - Module not found"

**Solution:**
```bash
# Ensure all dependencies are in package.json
cd /app/cx-frontend
npm install
npm run build

# If successful locally, commit package-lock.json
git add package-lock.json
git commit -m "Update dependencies"
git push
```

### Issue: "Output directory not found"

**Solution:**
Check `angular.json` output path matches Vercel config:
```json
"outputPath": "dist/cx-frontend/browser"
```

### Issue: "404 on page refresh"

**Solution:**
Ensure `vercel.json` routes are configured (see above).
Angular needs catch-all route to `/index.html`.

### Issue: "API calls fail (CORS)"

**Solution:**
1. Check backend CORS settings include Vercel domain:
   ```python
   CORS_ORIGINS = [
       "https://cx.sieteic.com",
       "https://cx-frontend-xxx.vercel.app",
       "http://localhost:4200"
   ]
   ```

2. Verify `NG_APP_API_URL` environment variable is set correctly

### Issue: "Styles not loading"

**Solution:**
```bash
# Ensure Tailwind/styles are built
npm run build

# Check angular.json includes styles:
"styles": [
  "src/styles.css"
]
```

---

## ✅ POST-DEPLOYMENT CHECKLIST

After deployment, verify:

- [ ] Frontend loads at `https://cx.sieteic.com`
- [ ] Login page appears correctly
- [ ] Can login with credentials
- [ ] Dashboard loads after login
- [ ] API calls work (check Network tab)
- [ ] No console errors
- [ ] Images/assets load
- [ ] Responsive design works (mobile/tablet)
- [ ] Custom domain works
- [ ] SSL certificate is active (https)

---

## 📊 MONITORING

### Vercel Analytics
1. Go to project dashboard
2. Click **"Analytics"** tab
3. View:
   - Page views
   - Unique visitors
   - Top pages
   - Performance metrics

### Logs
```bash
# View deployment logs
vercel logs

# View logs for specific deployment
vercel logs [deployment-url]

# Follow logs in real-time
vercel logs --follow
```

### Performance
```bash
# Run Lighthouse
npx lighthouse https://cx.sieteic.com --view

# Target scores:
# - Performance: 90+
# - Accessibility: 90+
# - Best Practices: 90+
# - SEO: 90+
```

---

## 🔄 CONTINUOUS DEPLOYMENT

Vercel automatically deploys when you push to GitHub:

**Workflow:**
```
1. Commit changes to branch
   git add .
   git commit -m "Update feature"
   git push origin phase0-4-enhancementsfe

2. Vercel detects push
   → Builds automatically
   → Runs tests
   → Deploys to preview URL

3. Review preview deployment
   → Check functionality
   → Test features

4. Merge to main/production
   → Automatically deploys to production
   → Updates cx.sieteic.com
```

---

## 📞 SUPPORT

**Vercel Issues:**
- Documentation: https://vercel.com/docs
- Support: https://vercel.com/support

**Project Issues:**
- Check deployment logs
- Review build output
- Test locally first: `npm run build`

---

## 🎉 SUCCESS!

Your Angular frontend should now be live at:
- **Production:** https://cx.sieteic.com
- **Vercel URL:** https://cx-frontend-xxx.vercel.app

**Next Steps:**
1. Test all features
2. Configure monitoring/alerts
3. Set up error tracking (Sentry)
4. Enable Vercel Analytics
5. Set up custom domain email notifications

---

**Deployment Date:** [Auto-filled by Vercel]  
**Build Time:** ~2-3 minutes  
**Status:** ✅ Active
