# NEXT_STATE
updated_at: 2026-10-21T15:00:00Z
loop_iteration: 1 of 5

## Queue (top-down; no worker dispatched; <=3 target files and <=150 changed lines per task)
### T-038 — Reproduce login contrast defect
- worker: W3 | priority: P1 | origin: F-A11
- target_files: frontend/e2e/accessibility.spec.ts
- contract: add switchable strict expected failure for login axe contrast; preserve all assertions
- verify: npm --prefix frontend exec -- playwright test --config frontend/playwright.config.ts --list frontend/e2e/accessibility.spec.ts
### T-039 — Fix login copyright contrast
- worker: W1 | priority: P1 | after: T-038 | origin: F-A11
- target_files: frontend/app/globals.css
- contract: use accessible color token for login copyright text, contrast >=4.5:1
- verify: npm --prefix frontend run build
### T-036 — Responsive audit timeout
- worker: W3 | priority: P1 | origin: T-008 browser run
- target_files: frontend/e2e/responsive.spec.ts
- contract: split six widths into bounded cases without weakening overflow/action assertions; keep read-only traffic
- verify: npm --prefix frontend exec -- playwright test --config frontend/playwright.config.ts --list frontend/e2e/responsive.spec.ts
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
### T-014 — G11 token storage migration
- worker: W2 | priority: P1 | authorized: ADR-001; split implementation before dispatch
- target_files: frontend/components/auth.tsx, frontend/lib/api.ts
- contract: plan cookie/CSRF migration with matching backend/tests; preserve server roles; no code change in this reconciliation
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
## Blocked
- F-A11: login keyboard fixture repaired; axe now exposes one serious contrast issue at `.login-copyright`.
- T-006: twice FAILED. Initial packet omitted `special-pages.tsx`; retry asserted empty/partial states without a screen-specific filter/list contract. No test accepted; requires a route-specific applicability matrix before new work.
- T-026/T-027/T-028: depend on blocked T-006 state matrix.
- T-019: frontend runner lacks source; test in builder stage.
- T-014: ADR-001 authorizes cookie/CSRF migration; split into atomic frontend, backend and test tasks before dispatch.

## Done this iteration (pruned on compaction)
- T-035 ✓ 45bab00; login keyboard assertion passes; axe contrast finding remains
- T-002 ✓ c6921bd; isolated stack 57 pass/0 skip and live acceptance passed
- T-037 ✓ 70fc6b5; isolated Compose stack accepted
- T-033 ✓ bounded keyboard Tab focus audit; second browser rerun pending
- T-032 ✓ remaining table/strategy status roles
- T-008 ✓ offline responsive test; browser timeout needs triage
- Earlier accepted tasks are in git history (T-001/003/004/005/007/010/011/025).
