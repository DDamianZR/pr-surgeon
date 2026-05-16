pr-surgeon/
├── frontend/                          # Next.js 14 + TypeScript
│   ├── app/page.tsx                   # Input PR URL
│   ├── app/analysis/[id]/page.tsx     # Resultado con grafo
│   └── components/
│       ├── DependencyGraph.tsx        # React Flow visualization
│       ├── PRCard.tsx                 # Cada sub-PR propuesto
│       └── DiffViewer.tsx             # Preview de cambios
├── backend/                           # FastAPI
│   ├── main.py                        # Endpoints: /analyze, /decompose, /export
│   ├── services/
│   │   ├── github_client.py           # PyGithub para obtener PR + diff
│   │   ├── dependency_analyzer.py     # AST parsing para imports/refs
│   │   ├── decomposer.py              # Algoritmo de agrupamiento
│   │   └── llm_service.py             # watsonx.ai + fallback
│   └── models/                        # Pydantic models
├── bob_sessions/                      # ⭐ Evidencia jurado
│   ├── 01_scaffolding.md
│   ├── 02_dependency_analyzer.md
│   ├── 03_decomposer_algorithm.md
│   ├── 04_frontend_graph.md
│   └── screenshots/
├── demo_data/                         # 2-3 PRs reales preprocesados (failsafe)
├── AGENTS.md                          # /init de Bob
├── README.md
└── SUBMISSION.md