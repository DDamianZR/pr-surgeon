# PR Surgeon - Project Architecture

> Complete project structure and architecture documentation

## Project Structure

```
pr-surgeon/
├── frontend/                          # Next.js 14 + TypeScript
│   ├── app/
│   │   ├── page.tsx                   # Landing page (PR URL input)
│   │   ├── layout.tsx                 # Root layout with fonts
│   │   ├── globals.css                # Global styles + React Flow
│   │   └── analysis/
│   │       └── page.tsx               # Analysis results with graph
│   ├── components/                    # Reusable React components
│   ├── lib/
│   │   └── api.ts                     # Backend API client
│   ├── public/                        # Static assets
│   ├── .env.local.example             # Environment template
│   ├── package.json                   # Dependencies
│   ├── tsconfig.json                  # TypeScript config
│   ├── tailwind.config.ts             # Tailwind CSS config
│   └── next.config.mjs                # Next.js config
│
├── backend/                           # FastAPI + Python 3.11
│   ├── main.py                        # FastAPI app + endpoints
│   ├── services/
│   │   ├── github_client.py           # PyGithub wrapper
│   │   ├── dependency_analyzer.py     # Graph building + clustering
│   │   ├── decomposer.py              # Sub-PR creation logic
│   │   ├── llm_service.py             # Template/cached enrichment
│   │   └── parsers/
│   │       ├── python_parser.py       # AST-based Python parser
│   │       ├── js_parser.py           # Regex-based JS/TS parser
│   │       └── generic_parser.py      # Fallback for other languages
│   ├── models/
│   │   ├── pr.py                      # PR data models
│   │   ├── analysis.py                # Graph and cluster models
│   │   ├── subpr.py                   # Sub-PR models
│   │   └── api.py                     # API request/response models
│   ├── tests/
│   │   ├── test_github_client.py
│   │   ├── test_dependency_analyzer.py
│   │   ├── test_decomposer.py
│   │   ├── test_llm_service.py
│   │   ├── test_api_analyze.py
│   │   └── test_smoke.py
│   ├── .env.example                   # Environment template
│   ├── pyproject.toml                 # Python dependencies
│   └── pytest.ini                     # Test configuration
│
├── demo_data/                         # Pre-processed PR data
│   ├── django_18056_response.json     # Cached GitHub API response
│   └── enrichments/
│       └── 2512b7ab9393.json          # Cached enrichment data
│
├── bob_sessions/                      # ⭐ Bob development sessions
│   ├── 00_context_loading.md
│   ├── 01_context_loading.md
│   ├── 02_github_client.md
│   ├── 03_dependency_analyzer_architecture.md
│   ├── 04_dependency_analyzer_architecture.md
│   └── 05_backend.md
│
├── docs/                              # Additional documentation
│
├── AGENTS.md                          # Bob's persistent context
├── README.md                          # Main project documentation
├── SUBMISSION.md                      # Hackathon submission
├── DEMO_PR.md                         # Demo PR analysis guide
├── FRONTEND_INSTRUCTIONS.md           # Frontend setup guide
├── arquitectura.md                    # This file
├── LICENSE                            # MIT License
└── .gitignore                         # Git ignore rules
```

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    (Next.js 14 Frontend)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP POST /analyze
                             │ { pr_url: string }
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│                     (main.py endpoint)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ GitHubPRClient │
                    └────────┬───────┘
                             │
                             │ Fetch PR data
                             │ (files, diffs, metadata)
                             ▼
                    ┌────────────────────┐
                    │ DependencyAnalyzer │
                    └────────┬───────────┘
                             │
                ┌────────────┼────────────┐
                ▼            ▼            ▼
         ┌──────────┐ ┌──────────┐ ┌──────────┐
         │  Python  │ │   JS/TS  │ │ Generic  │
         │  Parser  │ │  Parser  │ │  Parser  │
         └────┬─────┘ └────┬─────┘ └────┬─────┘
              │            │            │
              └────────────┼────────────┘
                           │
                           │ Extract imports
                           │ Build dependency graph
                           ▼
                  ┌─────────────────┐
                  │ networkx.DiGraph│
                  │ (nodes + edges) │
                  └────────┬────────┘
                           │
                           │ Community detection
                           │ Layer classification
                           ▼
                  ┌─────────────────┐
                  │   File Clusters │
                  └────────┬────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ PRDecomposer │
                    └──────┬───────┘
                           │
                           │ Create sub-PRs
                           │ Topological ordering
                           ▼
                    ┌──────────────┐
                    │   Sub-PRs    │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  LLMService  │
                    └──────┬───────┘
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
         ┌─────────────┐      ┌─────────────┐
         │  Template   │      │    Cached   │
         │    Mode     │      │    Mode     │
         └──────┬──────┘      └──────┬──────┘
                │                    │
                └──────────┬─────────┘
                           │
                           │ Enrich with descriptions
                           ▼
                  ┌─────────────────┐
                  │ EnrichedSubPRs  │
                  └────────┬────────┘
                           │
                           │ JSON response
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    React Flow Visualization                     │
│              (Graph + Sub-PR cards + Details)                   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Frontend Components

#### `app/page.tsx` (Landing Page)
- PR URL input with validation
- Example PR cards
- Loading state management
- Dark mode toggle
- Navigation to analysis page

#### `app/analysis/page.tsx` (Analysis Page)
- React Flow graph rendering
- Sub-PR card list
- Detail panel for selected sub-PR
- Metadata display (files, clusters, duration)
- Dark mode support

#### `app/layout.tsx` (Root Layout)
- IBM Plex font loading
- Global metadata
- Dark mode class management

#### `lib/api.ts` (API Client)
- Type-safe backend communication
- Error handling
- Request/response transformation

### Backend Services

#### `GitHubPRClient`
**Purpose:** Fetch PR data from GitHub API

**Methods:**
- `fetch_pr(pr_url: str) -> PullRequestData`
- `_parse_pr_url(url: str) -> tuple[str, str, int]`
- `_fetch_file_content(file: GitFile) -> str`

**Dependencies:** PyGithub, python-dotenv

#### `DependencyAnalyzer`
**Purpose:** Build dependency graph and detect clusters

**Methods:**
- `analyze(files: list[FileChange]) -> AnalysisResult`
- `_build_graph(files, imports) -> DependencyGraph`
- `_detect_clusters(graph) -> list[FileCluster]`
- `_classify_layer(file_path: str) -> str`

**Dependencies:** networkx, language parsers

#### `PRDecomposer`
**Purpose:** Convert clusters into sub-PRs

**Methods:**
- `decompose(pr_data, analysis) -> list[SubPR]`
- `_cluster_to_subpr(cluster, file_map) -> SubPR`
- `_generate_title(layer, name) -> str`

**Dependencies:** hashlib for deterministic IDs

#### `LLMService`
**Purpose:** Enrich sub-PRs with descriptions

**Modes:**
- `template`: Deterministic string templates (default)
- `bob_pregenerated`: Load from cached JSON files
- `watsonx`: Live API calls (infrastructure ready)

**Methods:**
- `enrich_subprs(pr_url, sub_prs) -> list[EnrichedSubPR]`
- `_enrich_with_template(sub_pr) -> EnrichedSubPR`
- `_load_pregenerated(pr_url, sub_prs) -> list[EnrichedSubPR]`

### Language Parsers

#### `PythonParser`
- Uses stdlib `ast` module
- High accuracy (~95%)
- Handles all import styles (import, from, relative)

#### `JSParser`
- Regex-based import detection
- Good accuracy (~85%)
- Handles ES6 imports, require(), dynamic imports

#### `GenericParser`
- Regex patterns for common import syntax
- Functional accuracy (~70%)
- Supports: Go, Java, Ruby, Rust, C, C++, PHP

## Data Models

### Core Models (Pydantic v2)

```python
# models/pr.py
class FileChange:
    filename: str
    status: str  # added, modified, removed
    additions: int
    deletions: int
    patch: str | None
    content: str | None

class PullRequestData:
    url: str
    title: str
    number: int
    files: list[FileChange]
    total_files: int

# models/analysis.py
class Import:
    source: str
    target: str
    import_type: str

class GraphNode:
    id: str
    label: str
    layer: str

class DependencyEdge:
    source: str
    target: str

class DependencyGraph:
    nodes: list[GraphNode]
    edges: list[DependencyEdge]

class FileCluster:
    id: str
    files: list[str]
    layer: str
    size: int

class AnalysisResult:
    graph: DependencyGraph
    clusters: list[FileCluster]
    total_files: int
    total_edges: int

# models/subpr.py
class SubPR:
    id: str
    title: str
    files: list[str]
    layer: str
    merge_order: int

class EnrichedSubPR(SubPR):
    description: str
    risk_level: str
    estimated_review_time: str
    suggested_reviewers: list[str]
    testing_recommendations: list[str]
```

## Technology Stack

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript 5.3
- **UI Library:** React 18
- **Styling:** Tailwind CSS 3.4
- **Graph:** React Flow 11
- **Icons:** Lucide React
- **Animations:** Framer Motion
- **Markdown:** react-markdown

### Backend
- **Framework:** FastAPI 0.110+
- **Language:** Python 3.11
- **Validation:** Pydantic v2
- **GitHub API:** PyGithub 2.1+
- **Graph:** networkx 3.2+
- **Logging:** loguru 0.7+
- **Testing:** pytest 8.0+

### Development Tools
- **Package Manager (Python):** pip, venv
- **Package Manager (Node):** npm
- **Linting:** ESLint (frontend), mypy (backend)
- **Type Checking:** TypeScript, Python type hints

## API Endpoints

### `POST /analyze`
**Request:**
```json
{
  "pr_url": "https://github.com/owner/repo/pull/123"
}
```

**Response:**
```json
{
  "pr_data": { ... },
  "analysis": { ... },
  "sub_prs": [ ... ],
  "metadata": {
    "total_files": 43,
    "total_clusters": 5,
    "layers": ["schema", "backend", "tests"],
    "analysis_duration_ms": 1234
  },
  "react_flow_data": {
    "nodes": [ ... ],
    "edges": [ ... ]
  }
}
```

### `GET /health`
**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

## Environment Variables

### Backend (`.env`)
```env
GITHUB_TOKEN=ghp_xxxxx              # GitHub personal access token
LLM_MODE=template                   # template | bob_pregenerated | watsonx
WATSONX_API_KEY=xxxxx              # Optional: for watsonx mode
FRONTEND_URL=http://localhost:3000  # For CORS
```

### Frontend (`.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing Strategy

### Backend Tests
- **Unit tests:** Each service in isolation
- **Integration tests:** API endpoints with mocked GitHub
- **Fixtures:** Sample PR data in `tests/fixtures/`
- **Coverage:** Core logic (parsers, analyzer, decomposer)

### Test Commands
```bash
cd backend
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest -k test_name       # Run specific test
pytest --cov              # Coverage report
```

## Deployment Architecture (In Progress)

### Frontend (Vercel)
- **Build:** `npm run build`
- **Output:** `.next/` static files
- **Environment:** `NEXT_PUBLIC_API_URL`

### Backend (Railway)
- **Build:** `pip install -e ".[dev]"`
- **Start:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Environment:** `GITHUB_TOKEN`, `LLM_MODE`, `FRONTEND_URL`

## Performance Considerations

### Frontend
- React Flow degrades past ~500 nodes
- Consider node collapsing for large PRs
- Dark mode uses CSS variables (no re-render)

### Backend
- GitHub API rate limits: 60/hour (unauth), 5000/hour (auth)
- No repo cloning (API-only approach)
- Caching for demo data in `demo_data/`

## Security Considerations

- GitHub tokens stored in `.env` (gitignored)
- CORS configured for specific origins
- No user authentication (MVP scope)
- Input validation via Pydantic models

## Future Architecture Improvements

1. **Caching Layer:** Redis for analysis results
2. **Queue System:** Celery for long-running analyses
3. **Database:** PostgreSQL for saved analyses
4. **Authentication:** JWT-based user accounts
5. **WebSockets:** Real-time analysis progress
6. **CDN:** Static asset optimization
7. **Monitoring:** Sentry for error tracking
8. **Analytics:** Posthog for usage metrics

---

**Last Updated:** 2026-05-17
**Version:** 1.0.0 (MVP)