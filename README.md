# PR Surgeon ⚕️

> Decompose monster Pull Requests into safe, reviewable sub-PRs. Powered by IBM Bob.

[![IBM Bob Hackathon](https://img.shields.io/badge/IBM%20Bob-Hackathon%202026-0f62fe)](https://lablab.ai/ai-hackathons/ibm-bob-hackathon)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue)](https://www.typescriptlang.org/)

**Status**: 🚧 Local development complete, deployment in progress
**Video**: Coming soon

---

## The Problem

Enterprise migrations produce monster Pull Requests of 300+ files. These PRs sit open for 4–8 weeks, cost $15K–25K per PR in engineer time, and routinely ship subtle regressions because no human can hold the full diff in their head.

## The Solution

PR Surgeon takes a monster PR URL and returns a safe decomposition plan:

1. **Parse** the PR diff and changed files
2. **Analyze** real inter-file dependencies (imports, references, inheritance)
3. **Cluster** tightly-coupled files using community detection
4. **Decompose** into 5–7 sub-PRs respecting architectural layers
5. **Enrich** each sub-PR with intelligent descriptions, risk assessment, and reviewer suggestions

What was a 4-week review marathon becomes a 5-day mergeable plan.

## Why Only Bob Can Build This

Decomposing a PR is a **whole-repo-context** problem. You cannot solve it with snippet-level autocomplete. IBM Bob's repository awareness is the foundation that makes the analysis trustworthy.

## Demo

**Local Demo Available**: Run the application locally to analyze real Pull Requests from GitHub.

**Demo Flow**:
1. Paste a PR URL (e.g., Django's Composite Primary Key PR)
2. Watch real-time analysis stages (Fetching → Parsing → Building graph → Clustering)
3. View interactive dependency graph with React Flow
4. Review proposed sub-PRs with descriptions and merge order
5. Export the decomposition plan

**Screenshot**: Coming soon

## Architecture

```
                 ┌────────────┐
PR URL ────────► │  Next.js   │ ◄──── React Flow visualization
                 │  Frontend  │
                 └─────┬──────┘
                       │
                       ▼
                 ┌────────────┐
                 │  FastAPI   │
                 │  Backend   │
                 └─────┬──────┘
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
  ┌──────────┐  ┌──────────────┐ ┌──────────┐
  │  GitHub  │  │  Dependency  │ │ watsonx  │
  │  Client  │  │   Analyzer   │ │ Granite  │
  └──────────┘  └──────┬───────┘ └──────────┘
                       │
                       ▼
                ┌──────────────┐
                │  Decomposer  │
                │  (networkx)  │
                └──────────────┘
```

**Stack**:
- Backend: Python 3.11, FastAPI, PyGithub, networkx, Pydantic v2
- Frontend: Next.js 14, TypeScript, React Flow, Tailwind CSS
- LLM: Template-based enrichment (watsonx.ai integration ready)
- Parsers: Python (AST), JavaScript/TypeScript, Generic fallback for 8+ languages
- Deploy: Local development (Railway + Vercel deployment in progress)

## How Bob Was Used

This project was built in 18 hours by a solo developer with IBM Bob as the primary development partner. Every Bob session is exported in [`bob_sessions/`](./bob_sessions/) with the full transcript.

Key uses:
- **Scaffolding**: entire monorepo in one Bob session
- **Algorithm design**: dependency clustering iterated across 3 sessions
- **Frontend**: React Flow component generated and refined with Bob
- **Documentation**: AGENTS.md and this README co-authored with Bob

See [`AGENTS.md`](./AGENTS.md) for the persistent context Bob uses.

## Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- npm or pnpm
- A GitHub personal access token (recommended for higher rate limits)
- Windows PowerShell or Unix-like terminal

### Backend Setup

**Windows PowerShell:**
```powershell
cd backend
Copy-Item .env.example .env
# Edit .env and add your GITHUB_TOKEN (optional but recommended)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn main:app --reload
```

**Unix/Linux/macOS:**
```bash
cd backend
cp .env.example .env
# Edit .env and add your GITHUB_TOKEN
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn main:app --reload
```

Backend will run at http://localhost:8000

### Frontend Setup

```bash
cd frontend
cp .env.local.example .env.local
# Edit .env.local if needed (default: http://localhost:8000)
npm install
npm run dev
```

Frontend will run at http://localhost:3000

### Verify Installation

1. Backend health check: http://localhost:8000/health
2. API docs: http://localhost:8000/docs
3. Frontend: http://localhost:3000

## Project Structure

```
pr-surgeon/
├── backend/
│   ├── main.py
│   ├── services/
│   │   ├── github_client.py
│   │   ├── dependency_analyzer.py
│   │   ├── decomposer.py
│   │   └── llm_service.py
│   ├── models/
│   └── tests/
├── frontend/
│   ├── app/
│   ├── components/
│   └── lib/
├── bob_sessions/           ⭐ All Bob sessions exported
├── demo_data/              # Pre-processed PRs for reliable demo
├── AGENTS.md               # Bob's persistent context
├── SUBMISSION.md           # Hackathon submission details
└── README.md
```

## Troubleshooting

### Backend Issues

**"Module not found" errors:**
```powershell
pip install -e ".[dev]"
```

**GitHub API rate limit:**
- Add a GitHub personal access token to `.env`
- Unauthenticated: 60 requests/hour
- Authenticated: 5000 requests/hour

**Port already in use:**
```powershell
uvicorn main:app --reload --port 8001
```

### Frontend Issues

**"Cannot connect to backend":**
- Verify backend is running at http://localhost:8000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`

**React Flow not rendering:**
- Clear browser cache
- Verify `reactflow` is installed: `npm install reactflow`

### Analysis Issues

**"No dependencies found":**
- Some PRs have minimal cross-file dependencies
- Try the Django Composite Primary Key example (43 files, well-connected)

**Parser errors:**
- Python and JS/TS parsers are most robust
- Other languages use generic import detection (lower accuracy)

## Current Status

✅ **Implemented:**
- GitHub PR fetching and parsing
- Dependency analysis with AST parsing (Python) and regex (JS/TS)
- Graph-based clustering with networkx
- Sub-PR decomposition with layer-aware ordering
- Template-based enrichment
- React Flow visualization with dark mode
- Full test suite

🚧 **In Progress:**
- Deployment to Railway + Vercel
- Demo video production
- watsonx.ai Granite integration (template fallback working)

📋 **Planned:**
- GitHub App for inline PR suggestions
- GitLab/Bitbucket support
- Tree-sitter parsing for improved accuracy
- Multi-user collaboration features

## License

MIT — see [LICENSE](./LICENSE).

## Acknowledgments

Built for the IBM Bob Hackathon 2026 hosted by [lablab.ai](https://lablab.ai).

Special thanks to:
- IBM Bob team for repository-aware AI development tools
- lablab.ai community for hackathon support
- Django, Desbordante, and other open-source projects used for testing
