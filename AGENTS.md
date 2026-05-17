# AGENTS.md — PR Surgeon

> Context document for IBM Bob and any AI development partner working on this codebase.

## Project Overview

**PR Surgeon** is an enterprise developer tool that decomposes monster Pull Requests (300+ files, typical in legacy migrations) into a series of small, reviewable, mergeable sub-PRs that respect real inter-file dependencies.

**Why this exists**: A 400-file PR in a Fortune 500 codebase blocks engineering for 4–8 weeks because no human can hold the full diff in their head. PR Surgeon uses repository-aware AI (IBM Bob + watsonx.ai Granite) to produce a safe decomposition plan in seconds.

**Built for**: IBM Bob Hackathon 2026, team Dievalivann, solo developer.

## Architecture

Monorepo with two main services:

```
pr-surgeon/
├── backend/        # FastAPI + Python 3.11
└── frontend/       # Next.js 14 + TypeScript
```

### Backend responsibilities
- Fetch PR data from GitHub via PyGithub
- Parse changed files into ASTs (Python: stdlib `ast`; JS/TS: regex-based import detection)
- Build a directed dependency graph (`networkx.DiGraph`) where nodes are files and edges are import/reference relationships
- Detect clusters of tightly-coupled files using `greedy_modularity_communities`
- Decompose the PR into sub-PRs respecting topological order (schema → backend → frontend → tests)
- Enrich sub-PRs with template-based or cached descriptions, risk assessment, reviewer suggestions

### Frontend responsibilities
- Single-page input: paste PR URL
- Visualization page: React Flow dependency graph + sub-PR cards
- Export the decomposition plan as JSON, markdown, or GitHub Actions workflow

### Data flow
```
PR URL → GitHubPRClient → DependencyAnalyzer → PRDecomposer → LLMService → Frontend
                                    ↓                              ↓
                            Language Parsers              Template/Cache Mode
                         (Python, JS/TS, Generic)
```

## Key Conventions

### Python (backend)
- Python 3.11 with strict type hints everywhere
- Pydantic v2 for all data contracts at service boundaries
- `loguru` for structured logging (JSON output configurable)
- All services are classes with focused public methods + private helpers
- Tests live in `backend/tests/`, run with `pytest`
- Minimal global state; services instantiated per request in FastAPI
- Environment variables via `python-dotenv`

### TypeScript (frontend)
- Next.js 14 App Router (not Pages Router)
- shadcn/ui components only, no custom design system
- Tailwind CSS; no inline styles
- React Server Components by default; `'use client'` only when needed
- API calls go through a typed client in `lib/api.ts`

### Naming
- Backend: `snake_case` for files/functions/vars, `PascalCase` for classes
- Frontend: `PascalCase` for components and component files, `camelCase` for everything else
- Sub-PR IDs are deterministic hashes of `(pr_url, file_set)` so they are stable across re-runs

## Common Tasks

### Add a new language to the dependency analyzer
1. Create `backend/services/parsers/<lang>_parser.py` implementing the `Parser` protocol
2. Implement `extract_imports(source: str, file_path: str) -> List[Import]`
3. Register it in `DependencyAnalyzer._register_parsers()`
4. Add test fixtures in `backend/tests/fixtures/<lang>/`
5. Write unit tests covering: simple imports, relative imports, edge cases

### Add a new sub-PR enrichment field
1. Extend `EnrichedSubPR` model in `backend/models/subpr.py`
2. Update template logic in `LLMService._enrich_with_template()` to include the new field
3. If using cached mode, update the JSON structure in `demo_data/enrichments/`
4. Update the frontend to render the new field in sub-PR cards

### Run locally

**Backend (Windows PowerShell):**
```powershell
cd backend
.venv\Scripts\Activate.ps1
uvicorn main:app --reload
```

**Backend (Unix/Linux/macOS):**
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

**Run tests:**
```bash
cd backend
pytest
```

## Gotchas

1. **Rate limits**: GitHub API has 60 req/hour unauthenticated, 5000/hour with token. Always provide `GITHUB_TOKEN` in `.env` for production use.

2. **No repo cloning**: We fetch file content via GitHub API only. This means we only see changed files in the PR, not the full repository context. Import resolution is limited to files within the PR.

3. **LLM Service modes**:
   - `template` (default): Deterministic string templates, no API calls, instant
   - `bob_pregenerated`: Loads from cached JSON files in `demo_data/enrichments/`
   - Future: `watsonx` mode for live IBM watsonx.ai Granite API calls

4. **TypeScript/JavaScript parsing is regex-based** for MVP. Acceptable accuracy (~85% precision on import detection) but should migrate to `tree-sitter-typescript` in v2 for production use.

5. **Topological sort ordering**: Multiple valid orderings exist. We prioritize: schema → config → backend → frontend → tests → docs. Within each layer, smaller clusters merge first.

6. **React Flow performance**: Degrades past ~500 nodes. For very large PRs (300+ files), consider implementing node collapsing or pagination.

7. **Parser coverage**: Python parser uses AST (high accuracy). JS/TS uses regex (good accuracy). Other languages use generic regex patterns (lower accuracy but functional).

8. **File path resolution**: Relative imports are resolved within the PR's file set only. Absolute imports to external packages are ignored.

## How Bob is used in this project

Bob is the primary development partner for this project. Specifically:

- **Scaffolding**: the entire monorepo structure was generated by Bob in session 01.
- **Algorithm design**: the dependency clustering algorithm was iterated with Bob across 3 sessions, exploring trade-offs between community detection methods.
- **Frontend**: the React Flow component was written by Bob with iterative refinement.
- **Documentation**: this AGENTS.md is co-authored with Bob.

Sessions are exported to `bob_sessions/` with descriptive names. Each file documents the prompt, Bob's response, and what was kept/discarded.

## Implementation Status

### ✅ Completed (v1)
- GitHub PR fetching via PyGithub
- Dependency analysis with graph building
- Python AST parser (high accuracy)
- JavaScript/TypeScript regex parser (good accuracy)
- Generic parsers for 8+ languages (Go, Java, Ruby, Rust, C, C++, PHP)
- Community detection clustering with networkx
- Layer-aware decomposition (schema → backend → frontend → tests)
- Template-based sub-PR enrichment
- React Flow visualization with dark mode
- Full test suite with pytest
- FastAPI backend with CORS
- Next.js 14 frontend with TypeScript

### 🚧 In Progress
- Deployment to Railway (backend) + Vercel (frontend)
- Demo video production
- watsonx.ai Granite integration (infrastructure ready, API integration pending)

### 📋 Future Work (v2)
- **Execution**: Actually create sub-PRs as branches in GitHub via GitHub API
- **GitLab/Bitbucket support**: Extend `GitHubPRClient` to support other platforms
- **Tree-sitter parsing**: Replace regex-based JS/TS parser with tree-sitter for production accuracy
- **GitHub App**: Native PR comments suggesting decomposition inline
- **Multi-user collaboration**: Real-time editing of decomposition plans
- **Authentication**: User accounts and saved analyses
- **Advanced clustering**: ML-based clustering considering semantic similarity, not just imports

These are intentional scope cuts to deliver a working MVP within the hackathon timeline.
