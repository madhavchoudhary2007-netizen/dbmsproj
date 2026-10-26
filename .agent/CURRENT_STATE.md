# CURRENT_STATE
updated_at: 2026-10-26
branch: overhaul/neo-brutal
execution: RUNNING — implementation resumed on owner instruction 2026-10-26
verified_product_head: b7afc1b
last_product_task: T-44611
metadata_task: T-44587 active-document audit; see matching acceptance result/commit
architect_sha256: 0f2b5366fee89ec70d8340ab2e148ad676f0c64bf324f00af559c242cd4cc46c
target_harness: Antigravity; requested Gemini 3.8 Flash HIGH orchestrator / LOW workers; cap 2
observed_antigravity_binding: Antigravity session active; dual-lane dispatch with Flash LOW workers
archetype: Neo-Brutal Motorsport light, ADR-007
last_eval_score: no current overhaul score; old 51.2974 is obsolete

## Phase and evidence snapshot
Phase requirements are in docs/overhaul-plan.md; the table below is the current status, not a new task list.
| Phase | Status | Remaining completion proof |
|---|---|---|
| 0 Architecture | COMPLETE | Preserve lock/ADRs; do not repeat owner ADR-007 approval |
| 1 Baseline | COMPLETE | Final candidate still reruns quality gates |
| 2 Security | COMPLETE | Retain auth/security regression coverage |
| 3 Backend | COMPLETE | T-331..T-340 all implemented, tested, and strictly typed |
| 4 DBMS showcase | COMPLETE | T-350..358 endpoints, migrations 006..008, tests, UI panels & docs complete |
| 5 Frontend foundation | COMPLETE | Preserve approved tokens/fonts/primitives |
| 6 Shell | COMPLETE | Preserve shared feed/navigation/keyboard behavior |
| 7 Routes | IN_PROGRESS | T-390..393 dependencies, T-379 failures and remaining route proof |
| 8 Taste/motion | NOT_COMPLETE | T-400 audit and resulting fixes; keep known Taste backlog |
| 9 Tests | NOT_COMPLETE | Production/real-stack E2E, visual/motion/resilience, coverage |
| 10 DevOps/docs | NOT_COMPLETE | CI release gates and accurate runtime/demo docs |
| 11 Release | NOT_COMPLETE | Current full score>=95, all hard gates, cleanup and owner PR step |
- Accepted domains T-44575..80: race history, SQL/Mongo showcase, session/results, steward/pit writes, auth/users, telemetry/demo/pit strategy. Evidence in results/Git.
- Full disposable backend: T-44559 262 passed/0 failed/0 skipped. Recent extraction checks verified domain suites; milestone integration pending full DB rerun.
- Frontend bundle size: all 19 routes <= 170 KB initial JS gzip (max 161.53 KB, DBMS 154.74 KB). Standings T-389 passed 85/85; Live/Pit Wall 100/100.
- T-44581..98: Modularized resources/modals (<300 lines); main.py <= 120; static title & mobile drawer (1475/1475 Playwright green); 40px feed & red footer (80/80 palette green).
- T-44593 (3c6c08b): typed CRUD competition models in schemas_competition.py, wire-compatible.
- T-44595 (59bbf84): replaced per-packet insert_one with batched col.insert_many(ordered=False) in simulation_persist.py and offloaded blocking writes in simulation_runner.py to asyncio.to_thread.
- T-44596 (e99c07d): implemented schema_migrations ledger in migrations.py with SHA-256 checksum verification and existing-DB backfill; delegated bootstrap.py (36 lines).
- T-44599 (fc2d2d4): replaced N+1 driver queries in race_archive.py with MongoDB aggregation pipeline ($match, $sort, $group, $replaceRoot) and fallback; overview count switched to estimated_document_count; added LIMIT 200 to /api/dbms/races SQL; added compound index in lifespan.
- T-44600 (84ae834): handled in-flight navigation abort race in edge-resilience.spec.ts Lens 5 test; full Playwright E2E suite passed 1475/1475 green across all 5 viewports.
- T-44601 (949adc6): created migration 005_points_systems.sql with points_systems and points_system_positions, default F1 2025 points seed, championships.points_system_id, and dynamic recalculate_standings join; added PointsSystemOut and PointsSystemPositionOut schemas.
- T-44602 (8751eaa): authored test_points_system.py unit suite asserting migration 005 DDL, standard F1 points distribution (top 10 + 11+ zero), and PointsSystemOut / PointsSystemPositionOut schema validation (18/18 tests green).
- T-44603/4: JSON logging and request ID correlation middleware in core/observability.py; test_observability.py green.
- T-44605 (74ae818): multi-stage non-root Dockerfiles (app uid 10001, nextjs uid 1001), healthchecks, requirements.lock.
- T-44606 (12fb9fb): authored test_dbms_showcase.py contract test specifications and parameter validators.
- T-44607 (93fdba1): Phase 4 migrations 006 (views/MV), 007 (audit log/trigger), 008 (roles/RLS); schemas_showcase.py; dbms_showcase.py with 8 endpoints (isolation, deadlock, views, MV refresh, gaps, explain, audit, security); main.py 116 lines.
- T-44608 (5872a0d): authored test_migrations.py unit suite asserting SHA-256 checksums, version ordering, mismatch detection, and SQL file integrity (11/11 tests green).
- T-44609 (efe56d0): removed xfail decorators and expanded test coverage with edge-case/parameter validation in test_dbms_showcase.py (60/60 tests green).
- T-44610 (1bfe3fa): implemented typed client service and state hooks for DBMS showcase in frontend/lib/dbms-showcase.ts.
- T-44611 (d866b4d): created DbmsShowcase component (286 lines, <300) and integrated dynamically into dbms-workspace.tsx (280 lines, <300); route initial JS 154.74 KB (<= 170 KB limit).
- T-44612 (6a15c0c): authored dbms-showcase.test.mjs unit tests verifying all 8 client fetchers (77/77 runtime tests green).
- T-358 (b7afc1b): authored normalisation analysis, BCNF justifications, index rationale table, and backup/restore runbook in docs/database.md.

## Current risks and open work
- Complete only remaining T-331/T-332 domains and required integration; do not repeat accepted T-44575..80 or create line-count wrappers. T-44573 remains superseded. Historical assembly counts are not the current module map.
- T-379 desktop A3 layout failures: all 15 resolved and verified green (80/80 passed in palette.spec.ts). TASTE-381-1 dashboard four-accent and TASTE-382 resource-page bloat resolved. Remaining route work: motion and full journey coverage.
- Standings delta arrows require an actual prior-rank source absent from the current API; never fabricate deltas or alter API without its ADR.
- T-021 acceptance fixture still depends on existing championship round 3; it needs a self-contained named test championship/cleanup plan shown before dispatch. Only disposable apexgrid-test may receive test writes/migrations; never real DB/data/volumes.
- Host Python3.14/Node26 differ from Docker3.12/22; production frontend image has no source/lint config, so host evidence is not container parity proof. Worker clone Next resolution failed previously; root-owned browser runs passed.

## Current process decision
- Dual-lane execution active: Lane 1 (W2) actively executing T-44582 (CRUD DI); Lane 2 ready for remaining frontend tasks.
- Checks chosen by risk, not arbitrary time limits. Lifecycle/lease/auth/persistence changes genuinely require those tests; run DB checks on disposable stack through orchestrator.
- Integration gates run at domain milestones (not just whole phases) to prevent failure accumulation.
- Separate bounded CRUD tranche and simulation/runtime tranche; never combine unrelated concerns merely to hit line counts.
- `main.py <= 120 lines` is the entrypoint gate for the T-331/T-332 structural milestone, NOT Phase 3 completion. Phase 3 still requires T-333..T-340 with their own evidence.
- Reuse exact evidence; avoid duplicate runs, exploratory audits, and throwaway wrappers. Progress measured by requirements and defects closed.
