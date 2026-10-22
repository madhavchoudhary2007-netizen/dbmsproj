# NEXT_STATE
updated_at: 2026-10-22T14:18:45Z
loop_iteration: 1 of 5

## Queue (top-down; <=3 target files and <=150 changed lines per task)
### T-132 — Extract telemetry GET read I/O
- worker: W2 | priority: P2 | after: T-131
- target_files: backend/app/main.py, backend/app/telemetry_repository.py
- contract: preserve GET /api/telemetry 404, list shape, sorting, filter, limit and role; typed read boundary
- verify: T-131 seeded contract on apexgrid-test, Ruff <=588, mypy <=254
## Blocked
- T-006: twice FAILED. Initial packet omitted `special-pages.tsx`; retry asserted empty/partial states without a screen-specific filter/list contract. No test accepted; requires a route-specific applicability matrix before new work.
- T-026/T-027/T-028: depend on blocked T-006 state matrix.
- T-019: frontend runner lacks source; test in builder stage.
- T-014: split into ADR-002 backend/frontend/browser/acceptance packets T-050..055; implementation follows reproducing tests.

## Done this iteration (recent; older accepted evidence in git/LOOP.md)
- T-131 ✓ 9c633e9; seeded telemetry/live read contract passed 1/1 with scoped Mongo cleanup, Ruff 588; worker socket denied and orchestrator reran.
- T-130 ✓ 1a9738b; five user routes moved to APIRouter, 4 focused seeded/route checks passed; Ruff 588, mypy 254; full isolated backend 114 passed and live acceptance passed.
- T-129 ✓ 68f5c8a; user DELETE checks/write moved into one repository transaction, 3 seeded checks passed, Ruff 588, mypy 259; full isolated backend 114 passed, live acceptance passed.
- T-128 ✓ 39770df; user PATCH validation/hash/UPDATE moved to typed repository, 3 seeded checks passed, Ruff 591, mypy 259; orchestrator reran after worker socket denial.
- T-127 ✓ 1f2fe12; user creation hashing and INSERT moved to typed repository; seeded contract 2 passed, Ruff 599, mypy 259. Worker socket denied; orchestrator reran.
- T-126 ✓ d2201f5; user list/detail SQL moved to typed repository; seeded contract 2 passed on apexgrid-test, Ruff 600, mypy 259. Worker socket denied; orchestrator reran after type repair.
- T-125 ✓ e410407; seeded auth/user contract 2 passed on apexgrid-test, Ruff 600. Worker socket denied; orchestrator reran, corrected generated-ID fixture and cleanup definition before acceptance.
- T-124 ✓ ffac0c8; backend-cwd import passes; marker retired; isolated backend 112 passed, zero skips/failures/xfails, live acceptance passed. F-STRUCT-01/02 closed.
- T-123 ✓ 0930e54; strict backend-cwd import xfail accepted, --runxfail fails on missing backend package; Ruff 600.
- T-122 ✓ 9e09f97; paused/running simulator guards pass, Ruff 600, mypy 259; marker retired, full isolated backend 111 passed. Live API startup failed import; F-STRUCT-02 queued.
- T-121 ✓ dee5f57; two strict simulator xfails accepted; --runxfail proves paused hang and running DB read after lease loss, Ruff 600.
- T-001..T-120: accepted history and evidence in git/LOOP.md.
