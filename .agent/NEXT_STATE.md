# NEXT_STATE
updated_at: 2026-10-26
branch: overhaul/neo-brutal
execution: RUNNING
phase: 3 backend / 7 routes; no current score

## Queue (root must prepare exact packets before dispatch)
### T-44613 — Live WebSocket Auth, Dual-Namespace Unification, and Runtime State Fallbacks
- worker: W2 | priority: P1 | origin: Phase 3 / Phase 9 Backend Test Hardening & Dual-Namespace Compatibility
- target_files: backend/app/auth_router.py, backend/app/core/legacy_compat.py, backend/app/core/request_auth.py, backend/app/core/runtime.py, backend/app/core/websocket_runtime.py, backend/app/database.py, backend/app/token_revocation.py
- contract: Dynamic delegation in legacy_compat/request_auth/auth_router/websocket_runtime; module namespace aliasing in database/token_revocation/auth_router; module-level fallbacks in runtime.py; passes test_runtime_lease, test_contract_goldens, test_token_revocation_db, test_logout_revocation, test_auth_revocation_edges, test_runtime_dependencies.
- verify: APEXGRID_TEST_STACK=1 DATABASE_URL='postgresql://apexgrid:apexgrid@localhost:15432/apexgrid' MONGODB_URL='mongodb://localhost:27018' MONGODB_DATABASE=apexgrid APP_ENV=local PYTHONPATH=backend:. .venv/bin/pytest -q backend/tests/test_runtime_lease.py backend/tests/test_contract_goldens.py backend/tests/test_token_revocation_db.py backend/tests/test_logout_revocation.py backend/tests/test_auth_revocation_edges.py backend/tests/test_runtime_dependencies.py && .venv/bin/mypy --strict backend/app && .venv/bin/ruff format --check backend/app backend/tests && .venv/bin/ruff check backend/app backend/tests

### T-44611 — DBMS Showcase UI tab and workspace integration
- worker: W1 | priority: P1 | origin: Phase 4 T-393 / T-351..T-357 Showcase UI workspace integration
- target_files: frontend/components/dbms-showcase.tsx, frontend/components/dbms-workspace.tsx
- contract: Create dbms-showcase.tsx rendering isolation demo, deadlock demo, views/MV refresh, window function analytics gaps, query explain, audit, and security panels using Nb primitives and dbms-showcase client; dynamically import in dbms-workspace.tsx; strictly < 300 lines each.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint

### T-44612 — DBMS showcase client runtime unit tests
- worker: W3 | priority: P1 | origin: Phase 4 T-350 / T-393 client runtime unit tests
- target_files: frontend/e2e/runtime/dbms-showcase.test.mjs
- contract: Create dbms-showcase.test.mjs testing all client fetcher functions in frontend/lib/dbms-showcase.ts against mocked API dispatch and query parameter construction.
- verify: npm --prefix frontend run test:runtime

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
