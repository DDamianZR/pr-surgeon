# Frontend Drop-in Instructions

## What you're getting

Three files that replace the existing scaffolding placeholders in your `frontend/`:

1. **`frontend/app/page.tsx`** — Landing page (paste PR URL, examples, loading states)
2. **`frontend/app/analysis/page.tsx`** — Analysis result page with React Flow graph + sub-PR sidebar
3. **`frontend/app/layout.tsx`** — Root layout with improved metadata
4. **`frontend/app/globals.css`** — IBM Plex fonts + React Flow custom styling

Plus:
- **`frontend/.env.local.example`** — Environment template

## Installation steps (5 minutes)

### 1. Copy the files into your repo

In your project root (`BOB-IA-HACKATHON-2026/`):

```powershell
# Backup current frontend/app contents (just in case)
# Then overwrite with new files

# Make sure these directories exist
mkdir -Force frontend\app\analysis

# Copy the 4 files (download them and place at):
# frontend/app/page.tsx          (overwrites existing)
# frontend/app/analysis/page.tsx (NEW directory + file)
# frontend/app/layout.tsx        (overwrites existing)
# frontend/app/globals.css       (overwrites existing)
# frontend/.env.local.example    (new)
```

### 2. Create your local .env.local

```powershell
cd frontend
Copy-Item .env.local.example .env.local
```

`.env.local` is already in `.gitignore` (it's in the parent `.gitignore`).

### 3. Make sure dependencies are installed

```powershell
npm install
```

You should already have these from the scaffolding `package.json`:
- next@^14.2
- react@^18
- reactflow@^11
- lucide-react
- tailwindcss

If you get errors about missing packages, install:

```powershell
npm install reactflow lucide-react
```

### 4. Run the frontend

```powershell
npm run dev
```

Open http://localhost:3000

### 5. Critical: make sure backend is running too

In another terminal:

```powershell
cd backend
.venv\Scripts\activate
uvicorn main:app --reload
```

Backend must be at http://localhost:8000 (default in `.env.local`).

## What you should see

### Landing page (http://localhost:3000)
- White background with subtle blue grid pattern
- Header with PR Surgeon logo + "Built with IBM Bob" badge
- Hero text: "Decompose monster Pull Requests safely"
- Input field for PR URL
- "Analyze PR" button (IBM blue)
- 3 example PR cards below

### Analysis page (after clicking "Analyze PR")
- Top bar with PR metadata (files, sub-PRs count, layers, duration)
- Left: React Flow graph with sub-PR groups in distinct colors by layer
- Right: scrollable list of sub-PRs + selected sub-PR detail

### Live demo flow

1. Click "Django: CompositePrimaryKey" example
2. See sequential loading stages (Fetching → Parsing → Building graph → ...)
3. Page transitions to /analysis with rendered graph
4. Click any sub-PR card → details panel updates on the right

## Visual style guarantees

- **Fonts**: IBM Plex Sans for body, IBM Plex Mono for code/paths
- **Colors**: IBM Carbon palette (blue #0f62fe primary, layer-specific accents)
- **Layout**: Generous whitespace, sharp grid alignment, no rounded-pill chaos
- **Tone**: Enterprise developer tool — restrained, technical, confident

## Troubleshooting

### "Module not found: reactflow"
```powershell
cd frontend
npm install reactflow
```

### CORS error in browser console
Backend must allow `http://localhost:3000`. Already configured in `main.py` via CORS middleware. Verify the backend is running.

### Graph shows but no edges visible
This is expected for Django PR 18056 (only 10 edges in 43 nodes). The grouping by sub-PR container is the main visualization, not the inter-file edges.

### Sub-PR titles still look duplicated
Make sure Bob's name-fix task completed AND you restarted uvicorn (or it auto-reloaded). Re-run the test from PowerShell.

## After everything works locally

1. Commit:
```powershell
cd ..
git add .
git commit -m "feat(frontend): landing + analysis pages with React Flow"
git push
```

2. Deploy to Vercel:
   - Push to GitHub (done)
   - Go to https://vercel.com/new
   - Import the repo
   - Root directory: `frontend`
   - Framework: Next.js (auto-detect)
   - Environment variables: `NEXT_PUBLIC_API_URL` = your Railway backend URL (set after backend deploy)

3. Deploy backend to Railway:
   - https://railway.app/new
   - Deploy from GitHub
   - Root directory: `backend`
   - Build: `pip install -e ".[dev]"`
   - Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Add env vars: `GITHUB_TOKEN`, `LLM_MODE=bob_pregenerated`, `FRONTEND_URL=<your vercel url>`
