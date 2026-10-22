# NEXT_STATE
updated_at: 2026-10-22T08:49:30Z
loop_iteration: 1 of 5

## Queue (top-down; <=3 target files and <=150 changed lines per task)
### T-098 — API-09 analytics repository extraction
- worker: W2 | priority: P1 | after: T-097
- target_files: backend/app/main.py, backend/app/analytics_repository.py
- contract: move dashboard/analytics SQL to repository, preserve public HTTP and JSON contract
- verify: DATABASE_URL=postgresql://apexgrid:apexgrid@localhost:15432/apexgrid MONGODB_URL=mongodb://localhost:27018 MONGODB_DATABASE=apexgrid APP_ENV=local .venv/bin/pytest -q backend/tests/test_api.py -k dashboard_analytics_characterization
## Blocked
- T-006: twice FAILED. Initial packet omitted `special-pages.tsx`; retry asserted empty/partial states without a screen-specific filter/list contract. No test accepted; requires a route-specific applicability matrix before new work.
- T-026/T-027/T-028: depend on blocked T-006 state matrix.
- T-019: frontend runner lacks source; test in builder stage.
- T-014: split into ADR-002 backend/frontend/browser/acceptance packets T-050..055; implementation follows reproducing tests.

## Done this iteration (pruned on compaction)
- T-097 ✓ 91e2f9a; dashboard/analytics shape/filter/role characterization, 1 seeded case. Full isolated backend 102 passed, 0 skipped/failed.
- T-096 ✓ 28f1620; guarded generic CRUD delete moved to repository, 3 seeded cases, Ruff 615, mypy 261.
- T-095 ✓ 01f0e9c; seeded dependent delete 409/preserved row and missing 404 pinned; Ruff 627.
- T-094 ✓ 620f12f; CRUD create/update I/O moved to repository, 3 seeded cases, Ruff 627, mypy 261.
- T-093 ✓ 5bd74a5; mypy strict 317→261, Ruff 632→630, 14 focused cases pass.
- T-092 ✓ 4a18472; CRUD list/detail repository split, six seeded read tests pass, Ruff 632.
- T-091 ✓ 630b7d1; two seeded CRUD write/role characterization cases pass.
- T-089 ✓ ca212ff; Simulation/MAX_SESSION_LAPS moved to simulation_core, six tests pass, Ruff 632.
- T-090 ✓ 29bf2b5; six seeded CRUD list/detail status/shape/role cases pass.
- T-016 ✓ 66f325e; Ruff violations 645→633, eight focused tests pass.
- T-015 ✓ 432495a; extracted typed sector performance helper, six simulation tests pass.
- T-088 ✓ 73de4fd; archive provisional label, full browser 775/775, typecheck pass.
- T-001..T-086: accepted history and evidence in git/LOOP.md; latest T-086 648ddad archive API fix.
- T-087 ✓ 710e0cf; strict desktop/mobile archive UI xfails reproduced; ordinary views pass.
