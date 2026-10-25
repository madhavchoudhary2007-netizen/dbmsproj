# NEXT_STATE
updated_at: 2026-10-25
phase: 3 T331 + 7 route redesign; Phases0–2,5–6 COMPLETE; no current score

## Queue
### T-44328 W2 — OPEN
- target_files: backend/app/main.py, backend/app/simulation_lifecycle.py
- contract: T331 move exact sync_simulation_lifecycle into typed simulation_lifecycle module, retain legacy wrapper.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py backend/tests/test_simulation_replay.py && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_api.py -k "simulation_stop or simulation_pause or reset" && .venv/bin/ruff check backend/app backend/tests && .venv/bin/ruff format --check backend/app/main.py backend/app/simulation_lifecycle.py

### T-44327 W1 — OPEN
- target_files: frontend/components/pages/pit-wall.tsx
- contract: T379 stage exact PitWall presentation page under pages/pit-wall.tsx; keep legacy source until separate wire.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint

### T-44326 W2 — OPEN
- target_files: frontend/lib/use-analytics.ts
- contract: T379 stage exact Analytics state/effects/search and derived rows into use-analytics hook; leave original presentation unchanged.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint

## Blocked
- None currently. Owner switched workers to gpt-6-luna/high; T44318 interrupted before edits, fresh worker required.

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44325 accepted5c977c3; verify0.
- T-44324 accepteda54f000; verify0.
- T-44323 accepted480ae39; verify0.
- T-44322 accepteddc23dbc; verify0.
- T-44321 accepted8d44b1f; verify0.
- T-44318 accepted3b7ca06; verify0.
- T-44320 accepted4645e52; verify0.
- T-44319 acceptedba3fa7c; verify0.
- T-44316 acceptedf2ef65e; verify0.
- T-44317 acceptede0e553d; verify0.
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
- Backend latest full231pass0skip/livePASS afterb0972ed; main1220lines, T331 remains.
- Detailed accepted IDs/evidence in CURRENT_STATE, git and .agent/results.
