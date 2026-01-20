# Project IRIS - Status Document
## Last Updated: December 16, 2025 @ 9:15 PM

### WHAT IS PROJECT IRIS?
- **Name:** IRIS (Intelligent Research Information System)
- **Purpose:** AI-powered research collaboration platform for KSU
- **Model:** Transparent AI, no IP claims, institution-funded
- **Key differentiator:** 100% on-premise AI (Ollama) - full data privacy

---

## PROJECT LOCATION
```
C:\Users\Steve\Projects\project-iris\
```

---

## CURRENT SESSION PROGRESS (Dec 16, 2025 - 9:15 PM)

### COMPLETED - Full Data Pipeline
| Task | Status | Details |
|------|--------|---------|
| Parallel Scrape | DONE | 4 scrapers (A-F, G-L, M-R, S-Z) |
| Merge & Dedupe | DONE | `faculty_all.json` - 1,289 unique profiles |
| PostgreSQL Import | DONE | 1,289 researchers, 73 colleges, 219 departments |
| Fix Names | DONE | Re-scraped from profile URLs - 1,284 fixed |
| Update DB Names | DONE | Database updated with corrected names |
| Vector Embeddings | DONE | 1,243 researchers with nomic-embed-text (768-dim) |

### BLOCKED - Google Scholar Enrichment
- `scholarly` library blocked by Google anti-bot protection
- **Workaround needed:** Proxies, Selenium, or alternative API (Semantic Scholar, ORCID)

### PostgreSQL - RUNNING IN DOCKER
```bash
docker ps  # Container: iris-postgres
```
- **Image:** pgvector/pgvector:pg16
- **Port:** 5432
- **Database:** iris
- **User:** postgres / postgres
- **Features:** pgvector extension for embeddings

### GPU - ACTIVE
- **Card:** NVIDIA GeForce RTX 2060 SUPER (8GB VRAM)
- **Usage:** ~2GB (Ollama)
- **Status:** Ready for embedding generation

### Ollama - RUNNING
- `gemma3:4b` (LLM - 4.3B params)
- `nomic-embed-text` (embeddings - 137M params)
- Using GPU acceleration

### App Ready
- `npm run dev` works at http://localhost:3000
- KSU branding applied

---

## CHECK SCRAPE PROGRESS
```bash
# Check if Python scrapers still running
tasklist | grep python

# Check output files
ls -la C:\Users\Steve\Projects\project-iris\apps\scraper\output\

# Check scraper logs
tail -20 C:\Users\Steve\Projects\project-iris\apps\scraper\output\scraper.log
```

---

## AFTER SCRAPE COMPLETES

### Merge Output Files
```bash
cd C:\Users\Steve\Projects\project-iris\apps\scraper
python -c "
import json
from pathlib import Path

all_profiles = []
for f in Path('output').glob('faculty_*.json'):
    if 'enriched' not in f.name and 'all' not in f.name:
        data = json.load(open(f))
        all_profiles.extend(data)
        print(f'{f.name}: {len(data)} profiles')

# Dedupe by net_id
seen = set()
unique = []
for p in all_profiles:
    if p['net_id'] not in seen:
        seen.add(p['net_id'])
        unique.append(p)

json.dump(unique, open('output/faculty_all.json', 'w'), indent=2)
print(f'Total unique: {len(unique)}')
"
```

### Run Google Scholar Enrichment
```bash
python enrich_scholar.py output/faculty_all.json output/faculty_enriched.json --max-pubs 20
```

### Import to PostgreSQL
```bash
# Connect to database
docker exec -it iris-postgres psql -U postgres -d iris

# Or use Prisma
cd packages/database
npx prisma db push
```

---

## UI/Design Updates
- **KSU Brand Colors:** Gold #FDBB30, Black #0B1315, Grey #C5C6C8
- **"Modern Scholarly" Design** implemented:
  - White backgrounds (not dark mode)
  - Serif fonts for headlines
  - Minimal gold accents (data highlights only)
  - No emoji icons - text abbreviations (RO, CM, GS, PN)
  - Professional academic aesthetic

---

## MCP Servers - INSTALLED & CONFIGURED
Installed globally via npm:
```
@modelcontextprotocol/server-filesystem@2025.11.25
@modelcontextprotocol/server-postgres@0.6.2
@modelcontextprotocol/server-puppeteer@2025.5.12
@modelcontextprotocol/server-github@2025.4.8
@modelcontextprotocol/server-memory@2025.11.25
```

Configuration: `.mcp.json` in project root

**IMPORTANT:** Restart Claude Code to activate MCPs.

---

## COMPLETED TASKS

### 1. Expert Panel Report
- 6 experts reviewed ethical model
- File: `docs/expert-panel-report.html`

### 2. Pitch Materials
- Main deck: `docs/ksu-pitch-deck.html`
- VP Research: `docs/pitches/pitch-vp-research.html`
- Provost: `docs/pitches/pitch-provost.html`
- CIO: `docs/pitches/pitch-cio.html`
- Faculty: `docs/pitches/pitch-faculty.html`

### 3. Platform Foundation
- **Next.js 16** app in `apps/web/`
- **Prisma schema** (45+ tables) in `packages/database/prisma/schema.prisma`
- **IRIS AI engine** in `packages/ai/src/index.ts`
- **Faculty scraper** in `apps/scraper/`
- **Google Scholar enrichment** in `apps/scraper/enrich_scholar.py`

### 4. IRIS Components (Visible AI)
- `apps/web/src/components/iris/IRISThinking.tsx` - AI processing animation (scholarly white card style)
- `apps/web/src/components/iris/IRISMatchExplainer.tsx` - Transparent match explanations (no emojis)
- `apps/web/src/app/page.tsx` - Landing page with KSU branding

---

## PENDING TASKS

1. ~~**Full Faculty Scrape**~~ - DONE (1,289 profiles)
2. ~~**Set up PostgreSQL**~~ - DONE (Docker: iris-postgres)
3. ~~**Merge Scrape Results**~~ - DONE (faculty_all.json)
4. ~~**Import Data to DB**~~ - DONE (1,289 researchers imported)
5. ~~**Fix Names**~~ - DONE (1,284 names corrected)
6. ~~**Generate Embeddings**~~ - DONE (1,243 with nomic-embed-text 768-dim)
7. **Google Scholar Enrichment** - BLOCKED (anti-bot protection)
8. **Profile Pages** - Build individual faculty profile pages
9. **Search/Discovery** - Implement researcher search with pgvector
10. **AI Matching** - Connect IRIS engine to faculty data

---

## HOW TO RESUME

### Start the App
```bash
cd C:\Users\Steve\Projects\project-iris
npm run dev
```

### Run Full Faculty Scrape
```bash
cd C:\Users\Steve\Projects\project-iris\apps\scraper
python scrape_faculty.py
```

### Run Google Scholar Enrichment
```bash
cd C:\Users\Steve\Projects\project-iris\apps\scraper
python enrich_scholar.py output/faculty_all.json output/faculty_enriched.json --max-pubs 20
```

### Start Ollama (if needed)
```bash
"C:\Users\Steve\AppData\Local\Programs\Ollama\ollama.exe" serve
```

---

## KEY FILES

| File | Purpose |
|------|---------|
| `apps/web/src/app/page.tsx` | Main landing page (scholarly design) |
| `apps/web/src/components/iris/IRISThinking.tsx` | AI processing animation |
| `apps/web/src/components/iris/IRISMatchExplainer.tsx` | Match explanation card |
| `apps/scraper/scrape_faculty.py` | KSU faculty web scraper |
| `apps/scraper/enrich_scholar.py` | Google Scholar enrichment |
| `apps/scraper/output/faculty_partial_A.json` | Scraped faculty data (letter A) |
| `packages/database/prisma/schema.prisma` | Database schema |
| `packages/ai/src/index.ts` | IRIS AI engine |
| `.mcp.json` | MCP server configuration |

---

## DESIGN DECISIONS

1. **AI Name:** IRIS (Intelligent Research Information System)
2. **Design Style:** "Modern Scholarly" - white backgrounds, serif fonts, minimal gold
3. **Icons:** Text abbreviations (RO, CM, GS, PN) not emojis
4. **Brand Colors:** KSU Gold #FDBB30, Black #0B1315, Grey #C5C6C8
5. **AI Strategy:** 100% transparent, visible processing, full explanations
6. **Data Privacy:** On-premise Ollama, no external APIs for sensitive data
7. **Pricing:** $75K-$150K/year institutional, free for researchers

---

## TECH STACK

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind |
| Backend | Next.js API Routes, Node.js |
| Database | PostgreSQL + pgvector |
| ORM | Prisma |
| AI (Local) | Ollama + gemma3:4b + nomic-embed-text |
| AI (Cloud) | OpenAI (fallback) |
| Scraper | Python + BeautifulSoup + scholarly |
| MCP Servers | filesystem, postgres, puppeteer, github, memory |

---

## WORKSTATION NOTES

- Powerful workstation with GPU
- Can use GPU for Ollama acceleration
- MCPs installed and ready to activate on restart
