# NEXT_STATE
updated_at: 2026-10-21T18:48:00Z
loop_iteration: 1 of 5

## Queue (top-down; <=3 target files and <=150 changed lines per task)
### T-053 — G11 WebSocket cookie and Origin
- worker: W2 | priority: P0 | after: T-052
- target_files: backend/app/main.py
- contract: session cookie WS accepted with allowed Origin; disallowed Origin rejected for all WS; legacy subprotocol remains
- verify: .venv/bin/pytest -q backend/tests/test_api.py --runxfail -k 'cookie_auth_websocket'
### T-059 — Phase 1 A/C/E backend audit
- worker: W3 | priority: P1 | origin: Phase 1
- target_files: .agent/audit/phase1-ace.md
- contract: evidence-based authorization, SQL, transaction, validation, rate-limit and WS findings
- verify: test -s .agent/audit/phase1-ace.md
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
- Browser matrix passed 715/715 across five Chromium projects; backend runtime audit clean. Frontend dev dependency audit and quality debt remain.
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
- Earlier accepted tasks and evidence are in git history and LOOP.md.
