# NEXT_STATE
updated_at: 2026-10-26
branch: overhaul/neo-brutal
execution: RUNNING for owner-authorized implementation; current request is docs only
phase: 3 backend / 7 routes; no current score

## Queue (root must prepare exact packets before dispatch)
### T-44581 — Simulation/live/DBMS-lock DI
- worker: W2 | priority: P1 | origin: T-331/T-332
- target_files: backend/app/api/simulation.py, backend/app/api/live.py, backend/app/api/dbms_lock.py, backend/app/main.py
- contract: Final domain routers/providers; preserve factory aliases, routes, OpenAPI and behavior; <=350 changed lines, no migration.
- verify: PYTHONPATH=backend:. APP_ENV=local .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py backend/tests/test_simulation_replay.py backend/tests/test_api.py -k "test_runtime_route_registrations or test_current_openapi or test_websocket_bus or f_dom_05 or test_simulation_stop_clears_pending_pit_reservations" && APP_ENV=local .venv/bin/mypy --strict backend/app && APP_ENV=local .venv/bin/ruff check backend/app && APP_ENV=local .venv/bin/ruff format --check backend/app; root owns apexgrid-test integration gate. Packet repaired under packets.md.
### T-44582 — CRUD DI
- worker: W2 | priority: P1 | after: T-44581/domain gate
- target_files: backend/app/api/crud.py, backend/app/crud_resources.py, backend/app/main.py
- contract: CRUD-only providers/direct mounts, <=250 changed lines, no contract changes.
- verify: Prepare exact offline snapshot/registration + mypy/ruff/format packet; root disposable integration. No dispatch before packet approved.
### T-44583 — Simulation lifecycle extraction
- worker: W2 | priority: P1 | after: CRUD/domain gate
- target_files: backend/app/core/simulation_service.py, backend/app/main.py
- contract: Lifecycle only, <=250 lines; main.py<=120 structural entrypoint gate, not all Phase 3.
- verify: Prepare exact offline replay/snapshot/registration + mypy/ruff/format packet; root disposable integration.
### T-44585 — Measured desktop A3 repairs
- worker: W1 | priority: P1 | origin: T-379
- target_files: frontend/app/styles/shell.css
- contract: Enlarge desktop race-control marquee to legal 64px for readable primary feed and approved red palette band across shell pages. Preserve mobile 40px, classes/copy/states verbatim.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-neobrutal.sh

## Documentation checkpoint
### T-44587 — Active document authority audit
- worker: O | priority: P1 | origin: owner docs audit; ADR-016
- target_files: .agent/ANTIGRAVITY_BRIEF.md, .agent/ARCHITECT.md, .agent/CURRENT_STATE.md, .agent/DOC_AUTHORITY.md, .agent/E1_APPLICABILITY_MATRIX.md, .agent/FINAL_REPORT.md, .agent/LOOP.md, .agent/NEXT_STATE.md, .agent/START_HERE.md, .agent/adr/ADR-007-neo-brutal-motorsport-light-overhaul.md, .agent/adr/ADR-016-document-authority-audit.md, .agent/archive/pre-overhaul/E1_APPLICABILITY_MATRIX.md, .agent/archive/pre-overhaul/FINAL_REPORT-agent.md, .agent/archive/pre-overhaul/FINAL_REPORT-root.md, .agent/archive/pre-overhaul/LOOP.md, .agent/archive/pre-overhaul/backlog.md, .agent/archive/pre-overhaul/perfection-loop.md, .agent/archive/pre-overhaul/queue.md, .agent/backlog.md, .agent/packets/T-44587.md, .agent/protocol/antigravity.md, .agent/protocol/archetypes.md, .agent/protocol/architect.md, .agent/protocol/bootstrap.md, .agent/protocol/compaction.md, .agent/protocol/delivery-workflow.md, .agent/protocol/design-ux.md, .agent/protocol/design-visual.md, .agent/protocol/lenses.md, .agent/protocol/packets.md, .agent/protocol/perfection-loop.md, .agent/protocol/roles.md, .agent/protocol/state-files.md, .agent/queue.md, .agent/results/T-44587.json, .claude/rules/frontend.md, .claude/skills/compact-state/SKILL.md, .claude/skills/evaluate/SKILL.md, AGENTS.md, DECISIONS.md, FINAL_REPORT.md, NEXT_STEPS.md, PROJECT_CONTEXT.md, README.md, docs/api.md, docs/architecture.md, docs/contracts.md, docs/database.md, docs/demo-guide.md, docs/flow-audit-2026-10-06.md, docs/overhaul-plan.md, frontend/AGENTS.md
- contract: Docs/own result only; preserve live work, pending packet bytes and all gates. Retire conflicting historical follow-directions, relock operational notes.
- verify: Exact documentation verifier in packet/result T-44587; not a product test/score.

## Integration debt / deferred
- Full apexgrid-test backend suite, zero skips + snapshot/mypy/ruff/format required at each domain boundary; latest full T-44559 262pass/0skip is not current DI integration. T-333..340 remain after structural milestone.
- T-379:15 A3 failures;1020/1100 mocked not full pass. TASTE-382-BLOAT resource-page>300; TASTE-381-1 dashboard4 accents vsmax3.
- P-3 DBMS260.10KiB vs170; Live161.29 passes. Standings prior-rank source absent: no fabricated deltas.
- T-021:show named disposable fixture/cleanup plan before dispatch. Other deferred findings: queue.md; unclosed requirements: overhaul-plan.md. No old phase caps or completed-domain repeats.
