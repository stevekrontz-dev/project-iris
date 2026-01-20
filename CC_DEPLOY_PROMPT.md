# CC Task: IRIS Railway Deployment - Git History Reset

## Context
CW fixed TypeScript build errors but git push fails - repo is 4.24 GB due to history bloat (old videos, frames, JSON dumps). Current files are only ~400 MB. Need to squash history and push to GitHub so Railway can deploy.

## What CW Already Did
1. Fixed `apps/web/src/app/grants/page.tsx` - invalid `ringColor` CSS property
2. Fixed `apps/web/src/app/org-tree/page.tsx` - null ref check on svgRef
3. Committed locally: `555aade fix: TypeScript errors - ringColor CSS property and null ref check`
4. Build passes: `npm run build` in `apps/web` succeeds

## Your Task

### Step 1: Squash Git History (Orphan Branch)
```powershell
cd C:\dev\research\project-iris

# Create fresh branch with single commit  
git checkout --orphan fresh-main
git add -A
git commit -m "IRIS: Research collaboration platform - Railway deployment ready"

# Replace main
git branch -D main
git branch -m fresh-main main

# Force push to GitHub
git push origin main --force
```

### Step 2: Verify Push Succeeded
- Check https://github.com/stevekrontz-dev/project-iris shows the new commit
- Repo size should be ~400 MB (LFS handles the FAISS index)

### Step 3: Verify Railway Auto-Deploy Triggers
- Railway project: `iris` (production environment)
- Service: `project-iris` 
- Should auto-deploy when GitHub receives push
- Check Railway dashboard for build logs

## Railway Service Config (Verify These)
**For API service (FastAPI):**
- Root Directory: `apps/scraper/src/consortium`
- DATA_DIR env var: `/app` (already set)
- Uses Dockerfile in that directory

**For Web service (if adding later):**
- Root Directory: `apps/web`
- Uses nixpacks (auto-detect Next.js)
- Needs env: `NEXT_PUBLIC_API_URL` pointing to API service URL

## Files That Matter
- `apps/scraper/src/consortium/Dockerfile` - API container
- `apps/scraper/src/consortium/search_api.py` - FastAPI app
- `apps/scraper/src/consortium/data/consortium/vector_index/` - 308 MB FAISS index (in LFS)
- `apps/web/` - Next.js frontend (builds clean now)

## Success Criteria
1. GitHub repo is <500 MB
2. Railway deployment completes without error
3. API responds at `https://<service>.up.railway.app/stats`

## Backup Location
`C:\dev\research\project-iris-backup` has full copy if anything goes wrong
