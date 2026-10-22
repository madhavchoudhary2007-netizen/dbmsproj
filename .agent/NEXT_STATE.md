# NEXT_STATE
updated_at: 2026-10-22T12:00:00Z
loop_iteration: 1 of 5

## Queue (top-down; <=3 target files and <=150 changed lines per task)
### T-093 — Phase 2 mypy ratchet repair
- worker: W2 | priority: P1 | after: T-092
- target_files: backend/app/simulation_core.py, backend/app/crud_repository.py, backend/app/database.py
- contract: fix seven new strict typing errors without changing behavior; total <=311
- verify: count=$(.venv/bin/mypy --strict backend/app --show-error-codes --no-error-summary | python3 -c 'import sys; print(sum(": error:" in line for line in sys.stdin))'); test "$count" -le 311 && .venv/bin/pytest -q backend/tests/test_api.py -k simulation
## Blocked
- T-006: twice FAILED. Initial packet omitted `special-pages.tsx`; retry asserted empty/partial states without a screen-specific filter/list contract. No test accepted; requires a route-specific applicability matrix before new work.
- T-026/T-027/T-028: depend on blocked T-006 state matrix.
- T-019: frontend runner lacks source; test in builder stage.
- T-014: split into ADR-002 backend/frontend/browser/acceptance packets T-050..055; implementation follows reproducing tests.

## Done this iteration (pruned on compaction)
- T-092 ✓ 4a18472; CRUD list/detail repository split, six seeded read tests pass, Ruff 632.
- T-091 ✓ 630b7d1; two seeded CRUD write/role characterization cases pass.
- T-089 ✓ ca212ff; Simulation/MAX_SESSION_LAPS moved to simulation_core, six tests pass, Ruff 632.
- T-090 ✓ 29bf2b5; six seeded CRUD list/detail status/shape/role cases pass.
- T-016 ✓ 66f325e; Ruff violations 645→633, eight focused tests pass.
- T-015 ✓ 432495a; extracted typed sector performance helper, six simulation tests pass.
- T-088 ✓ 73de4fd; archive provisional label, full browser 775/775, typecheck pass.
- T-001..T-086: accepted history and evidence in git/LOOP.md; latest T-086 648ddad archive API fix.
- T-087 ✓ 710e0cf; strict desktop/mobile archive UI xfails reproduced; ordinary views pass.
