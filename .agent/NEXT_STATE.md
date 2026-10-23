# NEXT_STATE
updated_at: 2026-10-23T05:09:31Z
loop_iteration: 0 of 8

## Queue (owner override; top-down; <=3 target files and <=150 changed lines per task)
### T-170 — Restore mypy ratchet after login limiter
- worker: W2 | priority: P2 | origin: T-169
- target_files: backend/app/login_limiter.py
- contract: remove new tuple-index mypy error without behavior change; global strict count <=222
- verify: .venv/bin/mypy --strict backend/app/login_limiter.py
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
- T-169 ✓ 4e88ceb; focused 6/6; full isolated backend 127/0/0 and live acceptance; mypy +1 repair T-170.
- T-168 ✓ 098a9c2; 4 pass/2 strict xfail, --runxfail exposed successful-login 429.
- T-163 ✓ 2bb95f8; focused 4/4, full isolated 90 pass/35 fail from counting successful logins; repair T-168/169.
- T-162 ✓ 6963b4f; 1 pass/3 strict xfails; --runxfail proved 3 missing-429 failures.
- T-161 ✓ 97c7268; session action characterization passed.
- T-160 ✓ 8b60194; membership router/repository split accepted, full isolated backend 120/0/0.
