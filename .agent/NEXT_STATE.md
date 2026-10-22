# NEXT_STATE
updated_at: 2026-10-22T12:00:00Z
loop_iteration: 1 of 5

## Queue (top-down; <=3 target files and <=150 changed lines per task)
### T-089 — Move Simulation state to simulation_core
- worker: W2 | priority: P1 | after: T-015/T-016
- target_files: backend/app/main.py, backend/app/simulation_core.py
- contract: re-export Simulation and MAX_SESSION_LAPS from main; preserve behavior
- verify: .venv/bin/pytest -q backend/tests/test_api.py -k simulation
### T-090 — API-02 CRUD read characterization
- worker: W3 | priority: P1 | parallel with T-089
- target_files: backend/tests/test_api.py
- contract: pin seeded list/detail read status and shapes before CRUD router extraction
- verify: DATABASE_URL=postgresql://apexgrid:apexgrid@localhost:15432/apexgrid MONGODB_URL=mongodb://localhost:27018 MONGODB_DATABASE=apexgrid APP_ENV=local .venv/bin/pytest -q backend/tests/test_api.py -k crud_read_characterization
## Blocked
- T-006: twice FAILED. Initial packet omitted `special-pages.tsx`; retry asserted empty/partial states without a screen-specific filter/list contract. No test accepted; requires a route-specific applicability matrix before new work.
- T-026/T-027/T-028: depend on blocked T-006 state matrix.
- T-019: frontend runner lacks source; test in builder stage.
- T-014: split into ADR-002 backend/frontend/browser/acceptance packets T-050..055; implementation follows reproducing tests.

## Done this iteration (pruned on compaction)
- T-016 ✓ 66f325e; Ruff violations 645→633, eight focused tests pass.
- T-015 ✓ 432495a; extracted typed sector performance helper, six simulation tests pass.
- T-088 ✓ 73de4fd; archive provisional label, full browser 775/775, typecheck pass.
- T-001..T-086: accepted history and evidence in git/LOOP.md; latest T-086 648ddad archive API fix.
- T-087 ✓ 710e0cf; strict desktop/mobile archive UI xfails reproduced; ordinary views pass.
