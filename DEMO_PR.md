# Demo PR Selection

> Internal working document for tracking which PR is used in the live demo.

## 🏆 Primary Demo PR

**URL:** https://github.com/django/django/pull/18056
**Repo:** django/django
**Title:** Composite Primary Key support across the ORM
**Status:** Open (as of analysis date)
**Date analyzed:** 2026-05-16

### Stats
- **Files changed:** 43
- **Languages detected:** Python (primary), JSON (config)
- **Total additions / deletions:** To be verified during live analysis

### Analyzer results
- **Graph nodes:** 43 (one per changed file)
- **Graph edges:** ~10-15 (estimated based on import patterns)
- **Final clusters:** 4-8 (expected based on architectural layers)
- **Layers represented:** schema, backend, tests, config

### Expected Cluster breakdown
| # | Layer | Files | Sample files |
|---|---|---|---|
| 1 | schema | 3-5 | django/db/backends/base/schema.py, migrations |
| 2 | backend | 15-20 | django/db/models/base.py, django/db/models/options.py |
| 3 | backend | 8-12 | django/db/models/sql/compiler.py, query.py |
| 4 | tests | 10-15 | tests/composite_pk/test_create.py, test_query.py |
| 5 | config | 2-3 | JSON config files |

**Note:** Actual results may vary. Run local analysis to get precise numbers.

### Why this PR was chosen
- 43 files (good demo scale)
- Multiple architectural layers (schema, ORM internals, SQL compiler, tests)
- Real enterprise feature (composite PKs = Postgres/Oracle/SAP requirement)
- Django is universally recognized
- Python-heavy (parser strongest here)

### Demo narrative hook

> "I'm going to demo with a real PR from Django — pull request 18056.
>
> This PR introduces Composite Primary Key support across Django's ORM —
> a feature enterprise teams have requested for years to integrate
> with legacy Postgres, Oracle, and SAP databases.
>
> It touches 43 files across four architectural layers:
> database schema engine, ORM core, SQL compiler, and test suite.
>
> In a normal review process, a PR like this sits open for 3-5 weeks.
> Multiple senior engineers review it in parallel, but nobody can hold
> the full diff in their head. Subtle bugs slip through.
>
> Watch what PR Surgeon does in 30 seconds..."
>
> [Paste URL → Show real-time analysis → Display graph → Review sub-PRs]
>
> "...and now we have a safe, reviewable decomposition plan that respects
> the actual dependencies between these files. Schema changes first,
> then ORM internals, then tests. Each sub-PR is 5-10 files instead of 43."

---

## Backup PRs

### Backup 1: desbordante-core/pull/2
- URL: https://github.com/Tydik42/desbordante-core/pull/2
- Files: 61 (C++)
- Status: weak (parser limited for C++)

### Backup 2: feedback-v2/pull/9
- URL: https://github.com/diegomez/feedback-v2/pull/9
- Files: 64 (TypeScript, Next.js 14 to 15 upgrade)
- Status: weak (TS path aliases unresolved)

---

## Pre-recorded fallback (failsafe)

Location: demo_data/django_18056.json

If live network fails during demo: backend loads this JSON instead of
calling GitHub API. Generate this file after backend pipeline is complete.

---

## Analysis Instructions

### Running the analysis locally

1. Start backend and frontend (see README.md)
2. Navigate to http://localhost:3000
3. Click "Django: CompositePrimaryKey" example or paste the URL
4. Watch the analysis stages:
   - Fetching PR data from GitHub
   - Parsing 43 files
   - Building dependency graph
   - Detecting clusters
   - Enriching sub-PRs
5. Review results in the visualization

### Expected behavior

- **Analysis time:** 5-15 seconds (depends on GitHub API response)
- **Graph rendering:** React Flow with color-coded clusters
- **Sub-PR cards:** Clickable cards showing file lists and descriptions
- **Dark mode:** Toggle available in top-right corner

### Troubleshooting

**"No dependencies found":**
- This is expected for some PRs with minimal cross-file imports
- Django 18056 should show 10-15 edges
- Try a different PR if needed

**"GitHub API rate limit":**
- Add GITHUB_TOKEN to backend/.env
- Unauthenticated: 60 req/hour
- Authenticated: 5000 req/hour

**Graph not rendering:**
- Check browser console for errors
- Verify React Flow is installed: `npm install reactflow`
- Try refreshing the page

## Lessons learned during PR selection

### PRs tested

**✅ Works well:**
- django/18056 (43 files, Python): Good dependency graph, clear layers
- Large refactoring PRs with cross-file imports

**⚠️ Limited results:**
- django/16341 (5 files): Too small, minimal dependencies
- flask/5008 (1 file): Single file change, no graph
- Small bug fixes: Usually isolated changes

**❌ Parser limitations:**
- desbordante-core/2 (C++): Generic parser has lower accuracy
- feedback-v2/9 (TS): Path aliases not resolved, imports detected but not linked

### Parser accuracy by language

| Language | Parser Type | Accuracy | Notes |
|----------|-------------|----------|-------|
| Python | AST | ~95% | High accuracy, handles all import styles |
| JavaScript/TypeScript | Regex | ~85% | Good for standard imports, misses complex patterns |
| Go, Java, Ruby, etc. | Generic regex | ~70% | Functional but less precise |

### Key insights

1. **Best PRs for demo:** 30-100 files with clear architectural layers
2. **Import detection:** Works best when imports are in diff hunks
3. **Refactoring PRs:** Show more dependencies than bug fixes
4. **Language support:** Python and JS/TS are most reliable

### Future improvements

- Fetch full file content via GitHub API (not just diffs)
- Tree-sitter parsing for JS/TS (production-grade accuracy)
- Support for monorepo path aliases
- Better handling of dynamic imports
