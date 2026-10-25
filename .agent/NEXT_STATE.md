# NEXT_STATE
updated_at: 2026-10-25
phase: 3 T331 + 7 route redesign; Phases0–2,5–6 COMPLETE; no current score

## Queue
### T-44318 W2 — OPEN
- target_files: frontend/lib/use-pit-wall.ts
- contract: T379 stage exact PitWall state/effects/actions into use-pit-wall hook; do not wire presentation yet.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint

### T-44316 W1 — OPEN
- target_files: frontend/components/special-pages.tsx
- contract: T379 wire byte-identical standalone StewardDesk via compatibility reexport; remove old function and imports used only by it.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint

### T-44317 W2 — OPEN
- target_files: backend/app/main.py, backend/app/session_measurements.py
- contract: T331 move exact ensure_session_reset_allowed and clear_session_measurements bodies into typed session_measurements module; retain legacy main wrappers.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_api.py -k "reset or simulation_stop" && .venv/bin/ruff check backend/app backend/tests && .venv/bin/ruff format --check backend/app/main.py backend/app/session_measurements.py

## Blocked
- None currently. Owner5.6/high override2bc94fb verified byfreshsuccessfulworkers.

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44315 accepted7bc73c9; verify0.
- T-44314 accepted45cbcad; verify0.
- T-44313 accepted0f39a4b; verify0.
- T-44312 acceptedb0972ed; verify0.
- T-44311 accepted3989f9d; verify0.
- T-44310 acceptedf51818a; verify0.
- T-44309 accepted8ac6fa2; verify0.
- T-44308 accepted304ebe7; verify0.
- T-44307 accepted03ab0d5; verify0.
- T-44306 accepted478cffa; verify0.
- T-44305 acceptedfe21209; verify0.
- T-44304 accepted2be7bec; verify0.
- T-380 accepted0a3e206; verify0.
- T-44303 accepted6e88345; verify0.
- T-44302 accepted8e88bb7; verify0.
- T-44301 accepted2f422c0; verify0.
- T-44299 acceptedbd3f9c2; verify0.
- T-44300 acceptedc44f8ed; verify0.
- T-44298 acceptedbcf158f; verify0.
- T-44297 acceptedc533c35; verify0.
- T-44296 acceptedc8d5a5a; verify0.
- T-44295 accepted77d775d; verify0.
- T-44294 acceptedc659147; verify0.
- T-44293 accepted0d7dd28; verify0.
- T-44292 accepted1a2b573; verify0.
- T-44291 accepted52e84a0; verify0.
- T-44290 accepted6d32c9e; verify0.
- T-44287 accepted3e715d5; verify0.
- T-44289 accepted523cd33; verify0.
- Phase6 T370/T371 complete;481 browser checks and build/static0.
- Login parentT380 accepted0a3e206; root80browserchecks and build/types/lint0.
- Dashboard exactmove complete; SessionPage split complete, Steward split underway (T379), existingbehavior retained.
- Backend latest full231pass0skip/livePASS afterb0972ed; main1264lines, T331 remains.
- Detailed accepted IDs/evidence in CURRENT_STATE, git and .agent/results.
