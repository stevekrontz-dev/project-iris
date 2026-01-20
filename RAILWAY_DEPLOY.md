# IRIS RAILWAY DEPLOYMENT GUIDE

## Overview
IRIS deploys as 2 Railway services:
1. **iris-web** - Next.js frontend (apps/web)
2. **iris-api** - FastAPI search service (apps/scraper/src/consortium)

The email service is optional - briefings use Gmail compose directly.

## Step 1: Create Railway Project

1. Go to https://railway.app and sign in
2. Click "New Project" 
3. Choose "Empty Project"
4. Name it "iris"

## Step 2: Deploy the API Service

### Option A: Deploy from GitHub (Recommended)

1. Push this repo to GitHub
2. In Railway, click "+ New Service" → "GitHub Repo"
3. Select your repo
4. Set **Root Directory**: `apps/scraper/src/consortium`
5. Railway will auto-detect the Dockerfile
6. Add Environment Variable:
   - `DATA_DIR` = `/app`
7. Deploy!

### Option B: Deploy via Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project  
railway link

# Deploy API
cd apps/scraper/src/consortium
railway up
```

### Important: Upload Data Files

The vector index (~360MB) needs to be included. Two options:

**Option 1: Include in repo** (simpler)
- Add `data/` folder to git
- Remove from .gitignore if needed

**Option 2: Use Railway volumes** (better for large files)
- Create a volume in Railway
- Upload data files via CLI:
```bash
railway volume create iris-data
# Then mount at /app/data
```

## Step 3: Deploy the Web Service

1. In Railway, click "+ New Service" → "GitHub Repo"
2. Select the same repo
3. Set **Root Directory**: `apps/web`
4. Add Environment Variables:
   - `NEXT_PUBLIC_API_URL` = `https://iris-api-production-xxxx.up.railway.app`
   (Use the URL from your API service)
5. Deploy!

## Step 4: Set Up Custom Domain (Optional)

1. In each service, go to Settings → Domains
2. Add custom domain like `iris.yourdomain.com`
3. Update DNS records as instructed

## Environment Variables Reference

### iris-api
```
DATA_DIR=/app
PORT=8000
```

### iris-web  
```
NEXT_PUBLIC_API_URL=https://your-api-url.railway.app
NEXT_PUBLIC_EMAIL_API_URL=https://your-email-url.railway.app (optional)
```

## Estimated Costs

Railway free tier includes:
- $5/month credits
- ~500 hours of runtime

IRIS estimated usage:
- API: ~$3-5/month (light usage)
- Web: ~$2-3/month
- Total: ~$5-8/month for low-traffic demos

## Troubleshooting

### API won't start
- Check that data files exist at `/app/data/consortium/vector_index/`
- Verify FAISS index loads: check Railway logs

### Web can't connect to API
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check CORS settings in search_api.py (currently allows all origins)

### Slow initial load
- First request loads the ML model (~10-15s)
- Subsequent requests are fast (<500ms)
- Consider Railway's "sleep after inactivity" setting

## Quick Test After Deploy

```bash
# Test API
curl https://your-api.railway.app/stats

# Test search
curl "https://your-api.railway.app/search?q=neural+networks&limit=5"
```
