# CURRENT_STATE
updated_at: 2026-10-26
branch: overhaul/neo-brutal
execution: RUNNING — implementation resumed on owner instruction 2026-10-26
verified_product_head: 6af6b78
last_product_task: T-44580
metadata_task: T-44586 Antigravity docs; see matching acceptance result/commit (not product completion)
architect_sha256: 36df162b44e313caf9dcf220514dc703f4d490000d8f05ffe667b149807b1c11
target_harness: Antigravity; requested Gemini 3.8 Flash HIGH orchestrator / LOW workers; cap 2
observed_antigravity_binding: UNVERIFIED — this Codex documentation session cannot attest Antigravity UI settings; no config changes
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
- Backend strict mypy reached zero in T-44565. T-44575 passed root acceptance (commit 1da3f59): race-history domain migrated to FastAPI APIRouter and Depends(get_race_db, get_race_telemetry, admin, current_user), assembly glue folded, 6 regression/characterization tests passed, strict mypy/ruff/format clean.
- T-44576 passed root acceptance (commit d0336d8): DBMS showcase routes (dbms_sql and dbms_mongo) migrated to domain APIRouters with FastAPI Depends injection (get_race_db, get_race_telemetry, get_mongo_db, admin), assembly lambdas in main.py folded, route registration uniqueness and snapshot contract verified.
- T-44577 passed root acceptance (commit cf15062): race operations and results routes (session_action, results_read, results_write) migrated to domain APIRouters with FastAPI Depends injection (get_race_db, get_simulations, get_bus, current_user, admin_steward), lambda blocks folded, contracts and registrations verified.
- T-44578 passed root acceptance (commit cc6102b): stewarding and pit-write operations routes (stewards and pit_write) migrated to domain APIRouters with FastAPI Depends injection (get_race_db, get_bus, get_simulations, require_roles), assembly glue folded, incident/pit tests verified.
- T-44579 passed root acceptance (commit fc3a1fb): authentication and user management routes (auth_router and user_router) migrated to domain APIRouters with FastAPI Depends injection (get_race_db, current_user, admin_user), mounted directly in main.py, 24 tests passed (login throttle, logout revocation, route registration, OpenAPI contracts).
- T-44580 passed root acceptance (commit 6af6b78): telemetry, demo race, and pit strategy routes migrated to domain APIRouters with FastAPI Depends injection (get_race_telemetry, get_race_db, get_simulations, get_bus, current_user, admin_steward), mounted directly in main.py, 20 tests passed.
- Latest full disposable backend evidence: T-44559, 262 passed/0 failed/0 skipped plus live acceptance. Subsequent extraction-only task checks did not rerun the full stack; milestone integration is not claimed current. Latest shell DB URLs were unset; no DB contacted during recent tasks.
- Frontend production build passed after T-44560. Live initial JS 161.29 KiB passes; DBMS 260.10 KiB fails unchanged 170 KiB cap. Standings T-389 root gate passed 85/85; latest Live/Pit Wall focused run 100/100. These are scoped results, not a final release score.
- T-44567 Standings typography: five E2E-R11 viewports passed, frontend lint/four design scripts passed, focused Taste review found no new defect. All accepted task details/hashes are in Git and .agent/results.

## Current risks and open work
- Complete the T-331/T-332 structural/DI milestone by real domain boundaries; recent four assembly-only modules added 215 lines while main fell only 764 ->732. Reconcile/fold such glue toward final ownership rather than creating more wrappers. T-44573 is superseded before dispatch.
- T-379 retains 15 desktop A3 layout failures; never label its full suite passed. Resource-page bloat and dashboard four-accent Taste findings remain. DBMS showcase/route work, motion, full E2E/performance, CI/docs and final evaluation remain.
- Standings delta arrows require an actual prior-rank source absent from the current API; never fabricate deltas or alter API without its ADR.
- T-021 acceptance fixture still depends on existing championship round 3; it needs a self-contained named test championship/cleanup plan shown before dispatch. Only disposable apexgrid-test may receive test writes/migrations; never real DB/data/volumes.
- Host Python3.14/Node26 differ from Docker3.12/22; production frontend image has no source/lint config, so host evidence is not container parity proof. Worker clone Next resolution failed previously; root-owned browser runs passed.

## Current process decision
- Documentation-only T-44586 under ADR-015: no implementation workers dispatched. Preserve pending T-44581 packet unchanged; its live worker status is unknown to this session. Accepted T-44575..80 remain accepted; task-only checks do not close integration debt.
- Orchestrator direct product edits: 0. Docs/manual preflight enforce command equality and scope; current scripts do not guarantee model obedience.
- Dual-lane execution active: Lane 1 (W2) drives Phase 3 backend domain tranches; Lane 2 (W1) addresses measured Phase 7 frontend layout defects (e.g. desktop A3 failures) concurrently on disjoint files.
- Checks chosen by risk, not arbitrary time limits. Lifecycle/lease/auth/persistence changes genuinely require those tests; run DB checks on disposable stack through orchestrator.
- Integration gates run at domain milestones (not just whole phases) to prevent failure accumulation.
- Separate bounded CRUD tranche and simulation/runtime tranche; never combine unrelated concerns merely to hit line counts.
- `main.py <= 120 lines` is the entrypoint gate for the T-331/T-332 structural milestone, NOT Phase 3 completion. Phase 3 still requires T-333..T-340 with their own evidence.
- Reuse exact evidence; avoid duplicate runs, exploratory audits, and throwaway wrappers. Progress measured by requirements and defects closed.

- T-44586 acceptance initially rejected its own result JSON as outside Markdown scope; explicitly named that metadata artifact and reran. No product gate changed.
