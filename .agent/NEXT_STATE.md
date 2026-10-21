# NEXT_STATE
updated_at: 2026-10-21T19:25:00Z
loop_iteration: 1 of 5

## Queue (top-down; no worker dispatched; <=3 target files and <=150 changed lines per task)
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
- T-014: ADR-001 authorizes cookie/CSRF migration; split into atomic frontend, backend and test tasks before dispatch.

## Done this iteration (pruned on compaction)
- T-049 ✓ 2baa5cd; search input touch size fixed, mobile all routes 15/15 and full browser 715/715
- T-016 ✓ 8f47108; CI/full gates accepted, baseline 5 reds remain after browser/backend security fixes
- T-048 ✓ 1d9c061; all-route touch audit found six filter inputs at 16.5px high
- T-047 ✓ 139e92f; dev-toolbar false positive excluded; full browser suite 645/645
- T-009 ✓ 8da6ff7; shared controls >=44px in enabled mobile browser check and production build
- T-046 ✓ fe207ca; RUN_XFAIL=1 reproduced 51 undersized targets across four routes
- T-045 ✓ 33f09ff; PyJWT replacement and 8 focused checks, backend audit green, isolated DB 65/0/0 + live acceptance
- T-044 ✓ 5a80981; security invariant xfails normally and fails with --runxfail
- T-043 ✓ 8ee4cbb; 7 auth characterization tests, Ruff ratchet 641→639
- T-042 ✓ 0d020d0; all browser E2E projects now pass 640/640
- T-041 ✓ 7f59af7; root/login/mobile fixture fixed, 96/96 desktop-project responsive cases passed
- T-040 ✓ d6e328e; desktop accessibility sweep 16/16
- T-036 ✓ 6fb9ba0; bounded 96-case/project responsive matrix, fixture follow-up required
- T-038 ✓ 4ee604b; contrast regression confirmed with RUN_XFAIL=1
- T-039 ✓ c52d74e; login contrast 6.44:1, build and login axe pass
- T-035 ✓ 45bab00; login keyboard assertion passes; axe contrast finding remains
- T-002 ✓ c6921bd; isolated stack 57 pass/0 skip and live acceptance passed
- T-037 ✓ 70fc6b5; isolated Compose stack accepted
- T-033 ✓ bounded keyboard Tab focus audit; second browser rerun pending
- T-032 ✓ remaining table/strategy status roles
- T-008 ✓ offline responsive test; browser timeout needs triage
- Earlier accepted tasks are in git history (T-001/003/004/005/007/010/011/025).
