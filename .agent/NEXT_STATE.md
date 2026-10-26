# NEXT_STATE
updated_at: 2026-10-26
branch: overhaul/neo-brutal
execution: RUNNING
phase: 3 backend / 7 routes; no current score

## Queue (root must prepare exact packets before dispatch)
### T-44596 — Migration ledger
- worker: W2 | priority: P1 | origin: Phase 3 T-335 schema_migrations ledger
- target_files: backend/app/bootstrap.py, backend/app/migrations.py
- contract: Create schema_migrations(version, checksum, applied_at) ledger table; apply migrations in version order inside a transaction; verify SHA256 file checksums and raise on mismatch; backfill 001-003 for existing databases where tables already exist; preserve bootstrap entrypoint and <=120 line ceiling.
- verify: PYTHONPATH=backend:. APP_ENV=local .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py backend/tests/test_simulation_replay.py backend/tests/test_telemetry_ordering.py backend/tests/test_telemetry_ingest_contract.py backend/tests/test_api.py -k "test_runtime_route_registrations or test_current_openapi or test_websocket_bus or f_dom_05 or test_app_lifespan or test_restarting_simulator" && APP_ENV=local .venv/bin/mypy --strict backend/app && APP_ENV=local .venv/bin/ruff check backend/app && APP_ENV=local .venv/bin/ruff format --check backend/app

### T-44598 — Mobile navigation drawer accessibility & background inert/hidden state
- worker: W1 | priority: P1 | origin: W3C modal dialog a11y & Playwright shell-navigation
- target_files: frontend/components/shell.tsx
- contract: Add aria-hidden={isMobile && open ? true : undefined} and inert={isMobile && open ? true : undefined} to .main-shell background container to ensure background content is properly hidden from accessibility tree when the mobile navigation drawer is open; preserve all styling, tokens, and keep shell.tsx strictly < 300 lines.
- verify: npm --prefix frontend exec -- playwright test --config frontend/playwright.config.ts frontend/e2e/shell-navigation.spec.ts && npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-neobrutal.sh

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
