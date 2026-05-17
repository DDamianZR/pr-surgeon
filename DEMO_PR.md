# Demo PR Selection

> Internal working document for tracking which PR is used in the live demo.

## 🏆 Primary Demo PR

**URL:** https://github.com/django/django/pull/18056
**Repo:** django/django
**Title:** Composite Primary Key support across the ORM
**Status:** [merged / closed / open — verify on GitHub]
**Date analyzed:** 2026-05-16

### Stats
- **Files changed:** 43
- **Languages detected:** Python (primary), JSON (config)
- **Total additions / deletions:** [fill in after analysis]

### Analyzer results (after fix)
- **Graph nodes:** 43
- **Graph edges:** [fill in, expected 8-15]
- **Final clusters:** [fill in, expected 4-8]
- **Layers represented:** schema, backend, tests

### Cluster breakdown
| # | Layer | Files | Sample files |
|---|---|---|---|
| 1 | schema | [n] | django/db/backends/base/schema.py |
| 2 | backend | [n] | django/db/models/base.py |
| 3 | backend | [n] | django/db/models/sql/compiler.py |
| 4 | tests | [n] | tests/composite_pk/test_create.py |

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
> Multiple senior engineers review it in parallel, but nobody understands
> the full diff. Let me show you what PR Surgeon does in 30 seconds."

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

## Lessons learned during PR selection

PRs tested that didn't work and why:
- django/16341 (5 files): too small, patch-only parsing yielded 0 edges
- django/17320 (2 files): too small
- flask/5008 (1 file): too small
- desbordante-core/2 (C++): parser too weak
- feedback-v2/9 (TS): JS parser found imports but path aliases didn't resolve

Parser limitations identified:
- Patch field from PyGithub contains only diff hunks, not full file content
- Imports usually outside diff hunks for non-refactor PRs
- Django 18056 worked because it's a wide-reaching refactor with imports in many diffs

Future v2 improvement: fetch full file content via repo.get_contents() for any PR.
