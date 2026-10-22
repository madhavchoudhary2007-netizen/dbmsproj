# NEXT_STATE
updated_at: 2026-10-22T12:00:00Z
loop_iteration: 1 of 5

## Queue (top-down; <=3 target files and <=150 changed lines per task)
### T-064 — G11 live WebSocket browser reproducer
- worker: W3 | priority: P0 | after: T-066
- target_files: frontend/e2e/live-cookie-ws.spec.ts
- contract: strict expected-failure live route journey proves cookie WebSocket opens without a JWT subprotocol
- verify: PLAYWRIGHT_PORT=32173 npm --prefix frontend exec -- playwright test --config frontend/playwright.config.ts e2e/live-cookie-ws.spec.ts --project=desktop-1440
### T-055 — G11 live WebSocket cookie client
- worker: W2 | priority: P0 | after: T-064
- target_files: frontend/components/special-pages.tsx
- contract: live WS connects by cookie without JWT subprotocol or localStorage token gate
- verify: npm --prefix frontend run typecheck
### T-015 — G13 simulation boundary extraction
- worker: W2 | priority: P1 | after: T-012
- target_files: backend/app/main.py, backend/app/simulation_core.py
- contract: behavior-preserving <=150-line extraction; no route/schema change
- verify: .venv/bin/pytest -q backend/tests/test_api.py -k simulation
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
- Historical browser matrix passed 715/715 before cookie migration; current full run stopped at 10 stale responsive login fixtures after 269 passes. Backend runtime audit clean. Frontend dev dependency audit and quality debt remain.
- T-006: twice FAILED. Initial packet omitted `special-pages.tsx`; retry asserted empty/partial states without a screen-specific filter/list contract. No test accepted; requires a route-specific applicability matrix before new work.
- T-026/T-027/T-028: depend on blocked T-006 state matrix.
- T-019: frontend runner lacks source; test in builder stage.
- T-014: split into ADR-002 backend/frontend/browser/acceptance packets T-050..055; implementation follows reproducing tests.

## Done this iteration (pruned on compaction)
- T-057 ✓ 6a80027; JUnit gate allows xfails, rejects skips/failures/malformed reports; 5 synthetic checks
- T-058 ✓ fb3da98; CI runs deployment-secret gate and fails unreachable audit
- T-050 ✓ cf80374; 8 strict cookie/CSRF xfails reproduced, Ruff 639
- T-051 ✓ 9aa67ed; session/CSRF cookies and cookie /me, 3 --runxfail checks
- T-060 ✓ 83f6dfb; three strict guard xfails reproduced with --runxfail
- T-059 ✓ verification passed; audit found F-ACE01 P2 login throttling (audit committed with T-060)
- T-052 ✓ 4353aaa; six CSRF/logout/Origin cases pass, isolated suite 78 passed/2 WS xfailed/0 skipped
- T-053 ✓ 7b63377; WS cookie/Origin and legacy auth tests pass; all G11 markers retired, isolated suite 80 passed/0 skipped/0 xfailed
- T-061 ✓ a47d81a; three test E501 signatures wrapped; runtime ratchet repair T-062 next
- T-062 ✓ a3d3322; G11 runtime formatting reduced Ruff count to 633; focused 12 tests pass
- T-063 ✓ d2e22b3; two browser cookie-auth defects reproduced with RUN_XFAIL=1
- T-054 ✓ a11619b; focused cookie browser journeys and typecheck pass; broad browser suite exposed stale login fixtures
- T-066 ✓ 724e732; fixtures migrated, full Playwright matrix 725 passed with exit 0
- Earlier accepted tasks and evidence are in git history and LOOP.md.
