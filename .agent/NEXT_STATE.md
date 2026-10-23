# NEXT_STATE
updated_at: 2026-10-23T05:04:42Z
loop_iteration: 0 of 8

## Queue (owner override; top-down; <=3 target files and <=150 changed lines per task)
### T-168 — F-ACE01 successful-login regression
- worker: W3 | priority: P2 | origin: full isolated gate after T-163
- target_files: backend/tests/test_login_throttle.py
- contract: strict xfail proving repeated valid logins and shared-source valid users remain allowed; preserve prior throttle assertions
- verify: APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_login_throttle.py
### T-169 — F-ACE01 count failed attempts only
- worker: W2 | priority: P2 | after: T-168
- target_files: backend/app/auth_router.py, backend/app/login_limiter.py
- contract: reserve atomically, release successful attempts by own token, retain per-account/source failed-attempt throttle
- verify: APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q --runxfail backend/tests/test_login_throttle.py
### T-164 — F-DOM-04 ordered telemetry reproduction
- worker: W3 | priority: P2 | after: F-E02
- target_files: backend/tests/test_telemetry_ordering.py
- contract: strict expected-failure tests for duplicate and older per-driver packets, plus unaffected distinct driver/lap progression
- verify: APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_telemetry_ordering.py
### T-165 — F-DOM-04 ingest ordering fix
- worker: W2 | priority: P2 | after: T-164
- target_files: backend/app/telemetry_repository.py, backend/app/telemetry_router.py
- contract: reject or idempotently ignore duplicate/older packets before Mongo insert and WebSocket publish; preserve wire shape unless ADR
- verify: APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q --runxfail backend/tests/test_telemetry_ordering.py
### T-166 — F-DOM-05 replay seed reproduction
- worker: W3 | priority: P2 | after: T-165
- target_files: backend/tests/test_simulation_replay.py
- contract: strict expected-failure seeded replay/persistence test; deterministic generated lap, gap and pit outputs after restart
- verify: APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_simulation_replay.py
### T-167 — F-DOM-05 persisted simulation seed
- worker: W2 | priority: P2 | after: T-166
- target_files: backend/app/main.py, backend/app/simulation_core.py, backend/migrations/003_simulation_seed.sql
- contract: additive seed persistence on disposable stack and per-session RNG; replay same race after restart without changing prior rows
- verify: APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q --runxfail backend/tests/test_simulation_replay.py

## Blocked
- T-006: twice FAILED. Initial packet omitted `special-pages.tsx`; retry asserted empty/partial states without a screen-specific filter/list contract. No test accepted; requires a route-specific applicability matrix before new work.
- T-026/T-027/T-028: depend on blocked T-006 state matrix.
- T-019: frontend runner lacks source; test in builder stage.
- T-014: split into ADR-002 backend/frontend/browser/acceptance packets T-050..055; implementation follows reproducing tests.

## Done this iteration (recent; older accepted evidence in git/LOOP.md)
- T-163 ✓ 2bb95f8; focused 4/4, full isolated 90 pass/35 fail from counting successful logins; repair T-168/169.
- T-162 ✓ 6963b4f; 1 pass/3 strict xfails; --runxfail proved 3 missing-429 failures.
- T-161 ✓ 97c7268; session action characterization passed.
- T-160 ✓ 8b60194; membership router/repository split accepted, full isolated backend 120/0/0.
