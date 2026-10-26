# NEXT_STATE
updated_at: 2026-10-26
branch: overhaul/neo-brutal
execution: RUNNING
phase: 3 T-331/T-332 consolidated milestone + remaining phase 7; no current overhaul score

## Queue

### T-44575 — Race-history domain dependency injection and router consolidation
- worker: W2 | priority: P1 | origin: T-331/T-332 structural milestone
- target_files: backend/app/api/race_archive.py, backend/app/api/laps.py, backend/app/api/race_history_routes.py, backend/app/main.py
- contract: Move race-history reads into domain APIRouters using FastAPI dependency injection (get_database, get_telemetry, require_roles("admin"), current_user). Fold intermediate assembly glue. Preserve exact OpenAPI contract, route uniqueness, and compatibility with test monkeypatches and exported aliases.
- boundaries: Up to 4 target files, <=350 changed lines. No edits outside target files; no API/OpenAPI breaking changes; no database migrations or new dependencies.
- verify: APP_ENV=local .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py backend/tests/test_api.py -k "test_archive_provisional or test_historical_archive or test_simulation_keeps or test_demo_car_numbers or test_restarting_simulator" && APP_ENV=local .venv/bin/mypy --strict backend/app && APP_ENV=local .venv/bin/ruff check backend/app && APP_ENV=local .venv/bin/ruff format --check backend/app

## Documentation checkpoint
A matching T-44574 acceptance commit/result makes this checkpoint complete; never redispatch it as implementation.

### T-44574 — Reconcile delivery documentation and pause
- worker: O | priority: P1 | origin: owner 2026-10-26 documentation optimization
- target_files: AGENTS.md, docs/overhaul-plan.md, DECISIONS.md, README.md, PROJECT_CONTEXT.md, PROJECT_STATE.md, NEXT_STEPS.md, docs/architecture.md, .agent/ARCHITECT.md, .agent/adr/ADR-014-efficient-delivery-workflow.md, .agent/protocol/delivery-workflow.md, .agent/protocol/architect.md, .agent/protocol/bootstrap.md, .agent/protocol/compaction.md, .agent/protocol/design-ux.md, .agent/protocol/design-visual.md, .agent/protocol/evaluation.md, .agent/protocol/lenses.md, .agent/protocol/packets.md, .agent/protocol/perfection-loop.md, .agent/protocol/roles.md, .agent/protocol/state-files.md, .agent/CURRENT_STATE.md, .agent/NEXT_STATE.md, .agent/packets/T-44574.md, .agent/START_HERE.md
- contract: Documentation-only policy reconciliation; preserve design section, phase task IDs, rubric/thresholds and all pending work. No implementation until owner start.
- boundaries: ADR-014 explicit Markdown sweep; no product/tests/scripts/config/DB edits. Orchestrator-owned docs exception.
- verify: Exact documentation verifier recorded in .agent/results/T-44574.json (whitespace, lock, budget, protected requirements, doc links and allowed file set).

## Resume after start work
- New model: follow START_HERE.md steps1–6. The owner start instruction lifts the pause; update state to RUNNING without asking again.
- Reconcile T-44574 acceptance and verified product head28c196f; inspect live workers/in-flight diffs; boot once. T-44573 assembly-only extraction was not dispatched and is superseded, not completed.
- Draft the first coherent T-331/T-332 domain packet toward final DI using existing characterization tests/providers. Review four recent assembly-only modules for folding; retain main.py<=120 final gate and API behavior. No speculative extra wrappers or repeated setup.
- Use disjoint independent frontend/QA work as the second lane where real prerequisites allow; at most two workers. Domain milestone full isolated suite remains required.

## Blocked / deferred (retain all)
- T-379 parent gate:15 desktop A3 layout failures; previous1020/1100 mocked result is not full success.
- TASTE-382-BLOAT: resource-page.tsx>300 lines; genuine responsibility split after flow coverage.
- TASTE-381-1: four dashboard face accents exceed approved max3; supporting-colour repair before A-5.
- P-3 DBMS:260.10KiB vs170KiB; optimize heavy lazy views after Phase4/T-393, threshold unchanged. Live161.29KiB passes.
- T-021 fixture self-containment: named disposable test championship/events, full assertions/cleanup; show plan before dispatch. Never modify real data.
- Standings delta: no authoritative prior-rank field; no fabricated data. All other remaining tasks are in overhaul-plan.md and existing queue/backlog records; accepted implementation is not repeated.

## Recent accepted product tasks
- T-44572 28c196f; T-44571 db57c59; T-44570 d134e39; T-44569 ed947dd; T-44568 b5f7f0e.
