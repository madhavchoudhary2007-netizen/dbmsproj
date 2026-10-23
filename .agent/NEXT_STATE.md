# NEXT_STATE
updated_at: 2026-10-23T08:15:00Z
loop_iteration: 0 of 8

## Queue (owner override; top-down; <=3 target files and <=150 changed lines per task)
### T-189 — assert zero console errors and unhandled rejections in routes.spec.ts
- worker: W3 | priority: P1 | origin: EVAL score F-6
- target_files: frontend/e2e/routes.spec.ts
- contract: assert absence of console.error and page errors in routes.spec.ts for all 16 routes
- verify: PLAYWRIGHT_PORT=32145 npm --prefix frontend exec -- playwright test --config frontend/playwright.config.ts routes.spec.ts --project=desktop-1440
### T-190 — add reducedMotion E2E assertion in frontend/e2e/accessibility.spec.ts
- worker: W3 | priority: P1 | origin: EVAL score A-7
- target_files: frontend/e2e/accessibility.spec.ts
- contract: emulate reducedMotion and verify animation-duration and matchMedia on routes
- verify: PLAYWRIGHT_PORT=32145 npm --prefix frontend exec -- playwright test --config frontend/playwright.config.ts accessibility.spec.ts --project=desktop-1440
### T-191 — update performance evaluation with verified invariants P-4
- worker: W3 | priority: P1 | origin: EVAL score P-4
- target_files: .agent/eval/performance.json
- contract: record P-4 passed from 136/136 backend unit tests and 82% coverage
- verify: python3 -c "import json; d=json.load(open('.agent/eval/performance.json')); assert any(c['id']=='P-4' and c['passed'] for c in d['checks'])"

## Blocked
- T-006: twice FAILED. Initial packet omitted `special-pages.tsx`; retry asserted empty/partial states without a screen-specific filter/list contract. No test accepted; requires a route-specific applicability matrix before new work.
- T-026/T-027/T-028: depend on blocked T-006 state matrix.
- T-019: frontend runner lacks source; test in builder stage.
- T-014: split into ADR-002 backend/frontend/browser/acceptance packets T-050..055; implementation follows reproducing tests.

## Done this iteration (recent; older accepted evidence in git/LOOP.md)
- T-188 ✓ 5b90310; typed TableDataResponse columns, plan nodes, and overview in dbms-workspace.tsx; typecheck 0 errors.
- T-187 ✓ 2874cc0; typed RaceSnapshot, drivers, timing, and DataTable rows in race-database.tsx.
- T-186 ✓ 81cadea; typed NavItem and NavGroup in shell.tsx eliminating string | LucideIcon ambiguity.
- T-185 ✓ 74b9811; added APP_ENV='local' to backend coverage invocation; 136/136 tests pass at 82% coverage.
- T-184 ✓ 0218106; eliminated 25 explicit any in special-pages.tsx; zero eslint errors/warnings.
- T-183 ✓ 6aa0756; eliminated 9 explicit any in dbms-workspace.tsx.
- T-182 ✓ 8f5f73e; eliminated 6 explicit any in shell.tsx and race-database.tsx.
- T-181 ✓ 63e1125; eliminated 5 explicit any in lib/api.ts.
- T-180 ✓ c7f2d45; scored edge dimension E-1..E-5; responsive 320/5120 passes, other checks open.
- T-179 ✓ 5a9941a; scored performance dimension P-1..P-6; Lighthouse not installed (NOT_RUN), bundle/invariants/axe open.
- T-178 ✓ d1e4d57; scored aesthetic dimension A-1..A-7; spacing lint 154 hits, banned/motion clean, palette/focal/motion open.
- T-177 ✓ d7e7385; recorded functional F-1..F-6 results; typecheck and build pass, lint and coverage replay open.
