# NEXT_STATE
updated_at: 2026-10-21T12:36:52Z
loop_iteration: 1 of 5

## Queue (top-down; no worker dispatched; <=3 target files and <=150 changed lines per task)
### T-001 — G01 repair dev install requirement
- worker: W2 | priority: P0 | pilot FAILED: envelope, worker DNS
- target_files: backend/requirements-dev.txt
- contract: correct HTTP client; preserve ranges
- verify: bash -c '! rg -q "httpx2" backend/requirements-dev.txt && .venv/bin/python -c "import httpx"'
### T-002 — G02 require full database baseline
- worker: W3 | priority: P0 | blocked: acceptance fixture assumes absent World Series round 3
- target_files: scripts/eval/db-baseline.sh
- contract: reject skipped DB tests; run acceptance
- verify: bash scripts/eval/db-baseline.sh
### T-003 — G03 establish route E2E harness
- worker: W3 | priority: P1
- target_files: playwright.config.ts, e2e/routes.spec.ts
- contract: register E2E-R01..R16
- verify: npx --yes playwright test --list
### T-004 — G04 typed five-state boundary
- worker: W2 | priority: P1
- target_files: frontend/lib/data-state.ts
- contract: typed five states with retry and retained data
- verify: npm --prefix frontend run typecheck
### T-005 — G04 shared partial-state rendering
- worker: W1 | priority: P1 | after: T-004
- target_files: frontend/components/ui.tsx
- contract: accessible partial notice retaining populated content
- verify: npm --prefix frontend run typecheck
### T-006 — G04 screen-state fixtures
- worker: W3 | priority: P1 | after: T-003
- target_files: e2e/states.spec.ts
- contract: cover applicable five states for all 16 routes; fail on missing state
- verify: npx --yes playwright test e2e/states.spec.ts
### T-007 — G05 keyboard and screen-reader audit
- worker: W3 | priority: P1 | after: T-003
- target_files: e2e/accessibility.spec.ts
- contract: tab/focus/labels/status checks on all routes
- verify: npx --yes playwright test e2e/accessibility.spec.ts
### T-008 — G06 viewport matrix
- worker: W3 | priority: P1 | after: T-003
- target_files: e2e/responsive.spec.ts
- contract: six viewport widths, no overflow or lost action
- verify: npx --yes playwright test e2e/responsive.spec.ts
### T-009 — G07 touch targets
- worker: W1 | priority: P1 | after: T-008
- target_files: frontend/app/globals.css
- contract: touched controls >=44x44px without breaking dense tables
- verify: npm --prefix frontend run build
### T-010 — G09 reduced motion
- worker: W1 | priority: P1 | pilot FAILED: build port denied
- target_files: frontend/app/globals.css
- contract: honor prefers-reduced-motion on spinners/transitions
- verify: bash scripts/eval/lint-motion.sh
### T-011 — G14 stale requests and recovery
- worker: W2 | priority: P1
- target_files: frontend/lib/api.ts
- contract: cancellation/retry primitive; no wire-contract change
- verify: npm --prefix frontend run typecheck
### T-012 — G15 deterministic timing boundaries
- worker: W3 | priority: P1
- target_files: backend/tests/test_api.py
- contract: fixed clock/seed tests for 0/1/72/73 laps, restart, sector progression
- verify: .venv/bin/pytest -q backend/tests/test_api.py -k simulation
### T-013 — G12 deployment secret guard
- worker: W3 | priority: P1
- target_files: scripts/eval/jwt-secret.sh
- contract: reject weak/missing JWT secret outside local mode; print no secret
- verify: bash scripts/eval/jwt-secret.sh
### T-014 — G11 token storage decision
- worker: W2 | priority: P1 | blocked: shared-deployment/auth decision
- target_files: frontend/components/auth.tsx, frontend/lib/api.ts
- contract: transport migration plan preserving server roles; no markup edits
- verify: npm --prefix frontend run typecheck
### T-015 — G13 simulation boundary extraction
- worker: W2 | priority: P1 | after: T-012
- target_files: backend/app/main.py, backend/app/simulation_core.py
- contract: behavior-preserving <=150-line extraction; no route/schema change
- verify: .venv/bin/pytest -q backend/tests/test_api.py -k simulation
### T-016 — G17 CI hard gates
- worker: W3 | priority: P1 | after: T-001,T-002,T-003
- target_files: .github/workflows/ci.yml, scripts/eval/full-gates.sh
- contract: install/typecheck/lint/all tests/build/E2E; skip is failure
- verify: bash -n scripts/eval/full-gates.sh
### T-017 — G08 spacing tokens
- worker: W1 | priority: P2 | after: T-010
- target_files: frontend/app/globals.css, frontend/tailwind.config.ts
- contract: add spacing scale in <=150 lines
- verify: npm --prefix frontend run build
### T-018 — G10 typography
- worker: W1 | priority: P2 | after: T-017
- target_files: frontend/app/globals.css, frontend/tailwind.config.ts
- contract: accessible sans/mono hierarchy
- verify: npm --prefix frontend run build
### T-019 — G16 runtime parity
- worker: W3 | priority: P2 | runtime versions verified; container source gates require builder stage
- target_files: scripts/eval/runtime-parity.sh
- contract: compare host/container Node and Python; run container gates
- verify: bash scripts/eval/runtime-parity.sh
### T-020 — G18 docs truth gate
- worker: W3 | priority: P2
- target_files: scripts/eval/docs-truth.sh
- contract: flag automated-E2E claims without configured tests
- verify: bash scripts/eval/docs-truth.sh
### T-021 — Acceptance self-owned fixtures
- worker: W3 | priority: P2
- target_files: scripts/acceptance.py
- contract: own named test championship/events, clean up; preserve assertions
- verify: .venv/bin/python scripts/acceptance.py
### T-022 — Spacing lint precision
- worker: W3 | priority: P2
- target_files: scripts/eval/lint-spacing.sh
- contract: ignore border widths, keep spacing checks
- verify: bash scripts/eval/lint-spacing.sh --self-test

## Blocked
- T-002: 57 DB tests pass; acceptance lacks fixture event.
- T-019: frontend runner lacks source; test in builder stage.
- T-014: decide whether shared/public deployment requires HttpOnly cookie auth.

## Done this iteration (pruned on compaction)
- none
