# NEXT_STATE
updated_at: 2026-10-26
branch: overhaul/neo-brutal
execution: RUNNING
phase: 3 backend / 7 routes; no current score

## Queue

### Lane 1: W2 backend

#### T-44581 — Simulation, live WebSocket, and DBMS lock domain dependency injection and router consolidation
- worker: W2 | priority: P1 | origin: T-331/T-332 structural milestone
- target_files: backend/app/api/simulation.py, backend/app/api/live.py, backend/app/api/dbms_lock.py, backend/app/main.py
- contract: Move simulation, live WebSocket, and DBMS lock routes into domain APIRouters using FastAPI dependency injection (get_race_telemetry, get_simulations, get_bus, admin, admin_steward_dependency, get_race_db). Mount routers directly in main.py. Preserve factory functions, exact OpenAPI contracts, and unique route registrations.
- boundaries: Up to 4 target files, <=350 changed lines. No edits outside target files; no API/OpenAPI breaking changes; no database migrations.
- verify: PYTHONPATH=backend:. APP_ENV=local .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py backend/tests/test_simulation_replay.py backend/tests/test_api.py -k "test_runtime_route_registrations or test_current_openapi or test_websocket_bus" && APP_ENV=local .venv/bin/mypy --strict backend/app && APP_ENV=local .venv/bin/ruff check backend/app && APP_ENV=local .venv/bin/ruff format --check backend/app

#### T-44582 — CRUD resources domain dependency injection
- worker: W2 | priority: P1 | origin: T-331/T-332 structural milestone
- target_files: backend/app/api/crud.py, backend/app/crud_resources.py, backend/app/main.py
- contract: CRUD-only Depends providers/direct mounts; preserve contracts; remove forwarding lambdas.
- boundaries: Up to 3 target files, <=250 changed lines. No mixing with simulation or runtime lifecycle.
- verify: PYTHONPATH=backend:. APP_ENV=local .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py backend/tests/test_api.py -k "test_runtime_route_registrations or test_current_openapi" && APP_ENV=local .venv/bin/mypy --strict backend/app && APP_ENV=local .venv/bin/ruff check backend/app && APP_ENV=local .venv/bin/ruff format --check backend/app

#### T-44583 — Simulation lifecycle & service extraction (main.py <= 120 lines gate)
- worker: W2 | priority: P1 | origin: T-331/T-332 structural milestone entrypoint gate
- target_files: backend/app/core/simulation_service.py, backend/app/main.py
- contract: Extract lifecycle helpers; wire runtime.simulations in lifespan; main.py<=120 structural entrypoint gate.
- boundaries: Up to 2 target files, <=250 changed lines.
- verify: PYTHONPATH=backend:. APP_ENV=local .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py backend/tests/test_simulation_replay.py && APP_ENV=local .venv/bin/mypy --strict backend/app && APP_ENV=local .venv/bin/ruff check backend/app && APP_ENV=local .venv/bin/ruff format --check backend/app

#### T-331-T-332-GATE — Structural & DI domain milestone integration gate
- worker: O (orchestrator) | priority: P1 | origin: domain milestone gate
- scope: Full apexgrid-test integration, zero skips; snapshot/mypy/ruff/format. Then T-333..340.

### Lane 2: W1 frontend

#### T-44585 — Repair documented 15 desktop A3 layout failures (T-379)
- worker: W1 | priority: P1 | origin: Phase 7 T-379
- target_files: frontend/components/pages/ and affected route layouts
- contract: Repair measured T-379 desktop A3 defects; preserve palette bands, targets, typography, hooks/features. Before dispatch name exact bounded files; no logic/API/test edits. Root owns browser verification.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-neobrutal.sh

## Documentation checkpoint
### T-44586 — Antigravity delivery contract and current handoff reconciliation
- worker: O | priority: P1 | origin: ADR-015
- target_files: .agent/ANTIGRAVITY_BRIEF.md, .agent/CURRENT_STATE.md, .agent/NEXT_STATE.md, .agent/START_HERE.md, .agent/adr/ADR-014-efficient-delivery-workflow.md, .agent/adr/ADR-015-antigravity-domain-delivery.md, .agent/packets/T-44581.md, .agent/packets/T-44586.md, .agent/protocol/antigravity.md, .agent/protocol/compaction.md, .agent/protocol/delivery-workflow.md, .agent/protocol/evaluation.md, .agent/protocol/packets.md, .agent/protocol/roles.md, .agent/protocol/state-files.md, AGENTS.md, DECISIONS.md, NEXT_STEPS.md, PROJECT_CONTEXT.md, README.md, docs/architecture.md, docs/overhaul-plan.md, .agent/results/T-44586.json
- contract: Docs only; preserve pending T-44581 unchanged and all gates; HIGH/LOW binding UNVERIFIED.
- boundaries: Markdown only, no dispatch; T-44581 capture is not product acceptance.
- verify: Exact documentation verifier in .agent/packets/T-44586.md and .agent/results/T-44586.json; whitespace, boot, protected sections, scope and pending-packet hash.

## Resume when authorized
- START_HERE.md + antigravity.md; reconcile pending T-44581 ownership before retry. No accepted-domain repeats. T-44582 CRUD and T-44583 lifecycle stay separate.
- Inspect pytest collection: global -k can deselect required cases. Root owns apexgrid-test domain gates; missing proof stays unverified. T-333..340 remain required.

## Blocked / deferred
- T-379:15 desktop A3 failures;1020/1100 mocked is not full success.
- TASTE-382-BLOAT:resource-page>300 lines; TASTE-381-1:4 dashboard accents vs max3.
- P-3 DBMS:260.10KiB vs170; Live161.29 passes. No threshold changes.
- T-021:show named disposable fixture/cleanup plan before dispatch; never real data.
- Standings:prior-rank source absent; no fabricated deltas. Remaining work: overhaul-plan.md + queue.md. Accepted T-44575..80 stay accepted; hashes/evidence in CURRENT_STATE/Git/results.
