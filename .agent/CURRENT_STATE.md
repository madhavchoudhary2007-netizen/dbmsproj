# CURRENT_STATE
updated_at: 2026-10-26
branch: overhaul/neo-brutal
execution: RUNNING — implementation resumed on owner instruction 2026-10-26
verified_product_head: 6201515
last_product_task: T-44589
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
| 3 Backend | IN_PROGRESS | Combined T-331/T-332 final domains; T-333..340 requirements and full integration |
| 4 DBMS showcase | NOT_COMPLETE | T-350..358 additions, isolated tests and teacher documentation |
| 5 Frontend foundation | COMPLETE | Preserve approved tokens/fonts/primitives |
| 6 Shell | COMPLETE | Preserve shared feed/navigation/keyboard behavior |
| 7 Routes | IN_PROGRESS | T-390..393 dependencies, T-379 failures and remaining route proof |
| 8 Taste/motion | NOT_COMPLETE | T-400 audit and resulting fixes; keep known Taste backlog |
| 9 Tests | NOT_COMPLETE | Production/real-stack E2E, visual/motion/resilience, coverage |
| 10 DevOps/docs | NOT_COMPLETE | CI release gates and accurate runtime/demo docs |
| 11 Release | NOT_COMPLETE | Current full score>=95, all hard gates, cleanup and owner PR step |
- Accepted domains T-44575..80: race history, SQL/Mongo showcase, session/results, steward/pit writes, auth/users, telemetry/demo/pit strategy. Evidence in results/Git; latest product6af6b78.
- Latest full disposable backend evidence: T-44559, 262 passed/0 failed/0 skipped plus live acceptance. Subsequent extraction-only task checks did not rerun the full stack; milestone integration is not claimed current. Latest shell DB URLs were unset; no DB contacted during recent tasks.
- Frontend production build passed after T-44560. Live initial JS 161.29 KiB passes; DBMS 260.10 KiB fails unchanged 170 KiB cap. Standings T-389 root gate passed 85/85; latest Live/Pit Wall focused run 100/100. These are scoped results, not a final release score.
- T-44567 Standings typography: five E2E-R11 viewports passed, frontend lint/four design scripts passed, focused Taste review found no new defect. All accepted task details/hashes are in Git and .agent/results.
- T-44585 passed root acceptance (commit 16e17a3): desktop race-control marquee enlarged to 64px (.nb-shell .race-control-feed in shell.css) at min-width 1000px, addressing desktop A3 red palette deficit across all shell routes; frontend typecheck, zero-warning lint, and four design linters passed cleanly. Root E2E palette gate (e2e/palette.spec.ts) re-measured at 1440px: 80 passed / 0 failed in 11.9s across all 16 routes, resolving all 15 desktop A3 failures.
- T-44581 passed root acceptance (commit 2b04eaf): simulation, live WebSocket, and DBMS lock modules refactored to domain APIRouters using FastAPI dependency injection (get_simulations, get_bus, admin, require_roles, get_race_db), mounted directly in main.py, backwards-compatible factory functions and handler aliases preserved, 8 tests passed (snapshot, route registration uniqueness, simulation replay, simulation control), strict mypy/ruff/format clean.
- T-44582 passed root acceptance (commit 3d214f9): CRUD resource routing refactored to domain APIRouter using FastAPI dependency injection (current_user, admin, get_race_db, get_race_telemetry), eliminated 15-lambda forwarding block in main.py, directly mounted crud_router, preserved backwards compatibility for create_crud_router and register_resources, 7 tests passed, strict mypy/ruff/format clean.
- T-44589 passed root acceptance (commit 6201515): replaced violet accent on open_incidents stat card with yellow in dashboard.tsx, resolving TASTE-381-1 four-accent defect and limiting dashboard face accents to approved <= 3 (red, yellow, mint); typecheck, lint, and four design linters passed cleanly.

## Current risks and open work
- Complete only remaining T-331/T-332 domains and required integration; do not repeat accepted T-44575..80 or create line-count wrappers. T-44573 remains superseded. Historical assembly counts are not the current module map.
- T-379 desktop A3 layout failures: all 15 resolved and verified green (80/80 passed in palette.spec.ts). TASTE-381-1 dashboard four-accent defect resolved. Remaining route work: resource-page bloat (TASTE-382), motion and full journey coverage.
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
