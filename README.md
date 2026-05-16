# PR Surgeon ⚕️

> Decompose monster Pull Requests into safe, reviewable sub-PRs. Powered by IBM Bob.

[![IBM Bob Hackathon](https://img.shields.io/badge/IBM%20Bob-Hackathon%202026-0f62fe)](https://lablab.ai/ai-hackathons/ibm-bob-hackathon)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Live Demo**: [pr-surgeon.vercel.app](https://pr-surgeon.vercel.app) <!-- replace -->
**Video**: [Watch the 4-minute demo](https://...) <!-- replace -->

---

## The Problem

Enterprise migrations produce monster Pull Requests of 300+ files. These PRs sit open for 4–8 weeks, cost $15K–25K per PR in engineer time, and routinely ship subtle regressions because no human can hold the full diff in their head.

## The Solution

PR Surgeon takes a monster PR URL and returns a safe decomposition plan:

1. **Parse** the PR diff and changed files
2. **Analyze** real inter-file dependencies (imports, references, inheritance)
3. **Cluster** tightly-coupled files using community detection
4. **Decompose** into 5–7 sub-PRs respecting architectural layers
5. **Enrich** each sub-PR with watsonx.ai Granite: title, description, risk, reviewers

What was a 4-week review marathon becomes a 5-day mergeable plan.

## Why Only Bob Can Build This

Decomposing a PR is a **whole-repo-context** problem. You cannot solve it with snippet-level autocomplete. IBM Bob's repository awareness is the foundation that makes the analysis trustworthy.

## Demo

![PR Surgeon demo](docs/demo.gif) <!-- if you have time, otherwise screenshot -->

Paste a PR URL → see the dependency graph → review the proposed sub-PRs → export the plan.

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
- Frontend: Next.js 14, TypeScript, React Flow, shadcn/ui, Tailwind
- LLM: IBM watsonx.ai Granite 3-8B Instruct
- Deploy: Railway + Vercel

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
- pnpm
- A GitHub personal access token (for higher rate limits)
- IBM watsonx.ai API key (optional — fallback templates included)

### Backend
```bash
cd backend
cp .env.example .env  # fill in GITHUB_TOKEN and WATSONX_API_KEY
uv venv && source .venv/bin/activate
uv pip install -e .
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
cp .env.local.example .env.local  # set NEXT_PUBLIC_API_URL
pnpm install
pnpm dev
```

Open http://localhost:3000.

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

## License

MIT — see [LICENSE](./LICENSE).

## Acknowledgments

Built for the IBM Bob Hackathon 2026 hosted by [lablab.ai](https://lablab.ai). Thanks to the IBM Bob team for the developer access and to the lablab.ai community for the support.
