# NEXT_STATE
updated_at: 2026-10-26
branch: overhaul/neo-brutal
execution: RUNNING
phase: 3 backend / 7 routes; no current score

## Queue (root must prepare exact packets before dispatch)
### T-44603 — Observability: structured JSON logging and X-Request-ID correlation
- worker: W2 | priority: P1 | origin: Phase 3 T-338 observability and request correlation
- target_files: backend/app/core/observability.py, backend/app/core/application.py
- contract: Create observability.py with request_id_ctx, JSONLogFormatter, and RequestCorrelationMiddleware; mount correlation middleware in create_application; strict mypy clean.
- verify: PYTHONPATH=backend:. APP_ENV=local .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py backend/tests/test_simulation_replay.py backend/tests/test_api.py -k "test_runtime_route_registrations or test_current_openapi or test_websocket_bus or f_dom_05 or test_app_lifespan or test_restarting_simulator" && APP_ENV=local .venv/bin/mypy --strict backend/app && APP_ENV=local .venv/bin/ruff check backend/app && APP_ENV=local .venv/bin/ruff format --check backend/app

### T-44604 — Observability and correlation test suite
- worker: W3 | priority: P1 | origin: Phase 3 T-338 QA unit tests
- target_files: backend/tests/test_observability.py
- contract: Author unit tests in test_observability.py verifying JSONLogFormatter JSON keys, request_id context propagation, middleware header echoing/generation, and /health/live; never touch product source.
- verify: PYTHONPATH=backend:. APP_ENV=local .venv/bin/pytest -q backend/tests/test_observability.py && APP_ENV=local .venv/bin/mypy --strict backend/tests/test_observability.py

## Documentation checkpoint
### T-44587 — Active document authority audit
- worker: O | priority: P1 | origin: owner docs audit; ADR-016
- target_files: .agent/ANTIGRAVITY_BRIEF.md, .agent/ARCHITECT.md, .agent/CURRENT_STATE.md, .agent/DOC_AUTHORITY.md, .agent/E1_APPLICABILITY_MATRIX.md, .agent/FINAL_REPORT.md, .agent/LOOP.md, .agent/NEXT_STATE.md, .agent/START_HERE.md, .agent/adr/ADR-007-neo-brutal-motorsport-light-overhaul.md, .agent/adr/ADR-016-document-authority-audit.md, .agent/archive/pre-overhaul/E1_APPLICABILITY_MATRIX.md, .agent/archive/pre-overhaul/FINAL_REPORT-agent.md, .agent/archive/pre-overhaul/FINAL_REPORT-root.md, .agent/archive/pre-overhaul/LOOP.md, .agent/archive/pre-overhaul/backlog.md, .agent/archive/pre-overhaul/perfection-loop.md, .agent/archive/pre-overhaul/queue.md, .agent/backlog.md, .agent/packets/T-44587.md, .agent/protocol/antigravity.md, .agent/protocol/archetypes.md, .agent/protocol/architect.md, .agent/protocol/bootstrap.md, .agent/protocol/compaction.md, .agent/protocol/delivery-workflow.md, .agent/protocol/design-ux.md, .agent/protocol/design-visual.md, .agent/protocol/lenses.md, .agent/protocol/packets.md, .agent/protocol/perfection-loop.md, .agent/protocol/roles.md, .agent/protocol/state-files.md, .agent/queue.md, .agent/results/T-44587.json, .claude/rules/frontend.md, .claude/skills/compact-state/SKILL.md, .claude/skills/evaluate/SKILL.md, AGENTS.md, DECISIONS.md, FINAL_REPORT.md, NEXT_STEPS.md, PROJECT_CONTEXT.md, README.md, docs/api.md, docs/architecture.md, docs/contracts.md, docs/database.md, docs/demo-guide.md, docs/flow-audit-2026-10-06.md, docs/overhaul-plan.md, frontend/AGENTS.md
- contract: Docs/own result only; preserve live work, pending packet bytes and all gates. Retire conflicting historical follow-directions, relock operational notes.
- verify: Exact documentation verifier in packet/result T-44587; not a product test/score.

## Integration debt / deferred
- Full apexgrid-test backend suite, zero skips + snapshot/mypy/ruff/format required at each domain boundary; latest full T-44559 262pass/0skip is not current DI integration. T-335..340 in progress.
- T-379: 80/80 palette pass; 85/85 a11y pass; 15/15 race-control-feed pass; 100% component files < 300 lines; 100% routes < 170 KB initial JS.
- P-3 DBMS 154.74 KiB <= 170 KB; all 19 routes pass bundle limit. Standings prior-rank source absent: no fabricated deltas.
- T-021:show named disposable fixture/cleanup plan before dispatch. Other deferred findings: queue.md; unclosed requirements: overhaul-plan.md. No old phase caps or completed-domain repeats.
