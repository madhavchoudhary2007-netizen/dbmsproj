# NEXT_STATE
updated_at: 2026-10-24
phase: 3 T331 + 7 route redesign; Phases0–2,5–6 COMPLETE; no current score

## Queue
### T-44294 W3 — OPEN
- target_files: frontend/e2e/login-layout.spec.ts
- contract: T380 correct newly added login test ink fixture to the actual approved pure black palette.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

### T-44293 W1 — OPEN
- target_files: frontend/components/nb/button.tsx
- contract: T380 fix native aria-busy forwarding in NbButton discovered by held-request login regression.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

### T-44292 W2 — OPEN
- target_files: backend/app/demo_names.py, backend/app/main.py
- contract: T331 move deterministic demo driver-name generation into typed module, preserving RNG draw order and name pools.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_api.py -k "seeded or demo_car" && .venv/bin/ruff check backend/app backend/tests && .venv/bin/ruff format --check backend/app/main.py backend/app/demo_names.py

## Blocked
- None currently. Owner5.6/high override2bc94fb verified byfreshsuccessfulworkers.

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44291 accepted52e84a0; verify0.
- T-44290 accepted6d32c9e; verify0.
- T-44287 accepted3e715d5; verify0.
- T-44289 accepted523cd33; verify0.
- Phase6 T370/T371 complete;481 browser checks and build/static0.
- Login route redesigned,70genericbrowserchecks pass; mobilecontainment/TASTE fixes remain beforeT380 closure.
- Dashboard exactmove complete; SessionPage split underway (T379), existingbehavior retained.
- Backend latest full231pass0skip/livePASS after097578f; main1424lines, T331 remains.
- Detailed accepted IDs/evidence in CURRENT_STATE, git and .agent/results.
