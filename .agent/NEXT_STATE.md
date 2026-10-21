# NEXT_STATE
updated_at: 2026-10-21T13:04:06Z
loop_iteration: 1 of 5

## Queue (top-down; no worker dispatched; <=3 target files and <=150 changed lines per task)
### T-002 — G02 require full database baseline
- worker: W3 | priority: P0 | blocked: acceptance fixture assumes absent World Series round 3
- target_files: scripts/eval/db-baseline.sh
- contract: reject skipped DB tests; run acceptance
- verify: bash scripts/eval/db-baseline.sh
### T-009 — G07 touch targets
- worker: W1 | priority: P1 | after: T-008
- target_files: frontend/app/globals.css
- contract: touched controls >=44x44px without breaking dense tables
- verify: npm --prefix frontend run build
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

### T-023 — TASTE-1 reduce UI module bloat
- worker: W1 | priority: P2 | after: T-005
- target_files: frontend/components/ui.tsx, frontend/components/data-table.tsx
- contract: extract cohesive table presentation so ui.tsx is <=300 lines; preserve exports and behavior
- verify: npm --prefix frontend run typecheck

### T-034 — TASTE-2 reduce special-pages module bloat
- worker: W1 | priority: P2 | after: T-032
- target_files: frontend/components/special-pages.tsx, frontend/components/pit-wall.tsx
- contract: extract cohesive PitWall presentation within 150 changed lines and preserve behavior; continue staged extraction until <=300 lines
- verify: npm --prefix frontend run typecheck

## Blocked
- T-006: twice FAILED. Initial packet omitted `special-pages.tsx`; retry asserted empty/partial states without a screen-specific filter/list contract. No test accepted; requires a route-specific applicability matrix before new work.
- T-026/T-027/T-028: depend on blocked T-006 state matrix.
- T-002: 57 DB tests pass; acceptance lacks fixture event.
- T-019: frontend runner lacks source; test in builder stage.
- T-014: decide whether shared/public deployment requires HttpOnly cookie auth.

## Done this iteration (pruned on compaction)
- T-033 ✓ bounded keyboard Tab focus audit; second browser rerun pending
- T-032 ✓ remaining table/strategy status roles
- T-008 ✓ offline responsive test; browser timeout needs triage
- T-031 ✓ footer contrast
- T-030 ✓ StateMessage roles
- T-029 ✓ focus audit fix
- Earlier accepted tasks are in git history (T-001/003/004/005/007/010/011/025).
