# NEXT_STATE
updated_at: 2026-10-22T19:17:29Z
loop_iteration: 1 of 5

## Queue (top-down; <=3 target files and <=150 changed lines per task)
### T-147 — Move pit strategy handler to APIRouter
- worker: W2 | priority: P2 | after: T-146
- target_files: backend/app/main.py, backend/app/pit_strategy_router.py
- contract: preserve route registration, direct pit_strategy test import, 404, Mongo partial behavior, live/history response and injection boundaries
- verify: focused pit strategy unit test; Ruff <=561 and mypy <=248
## Blocked
- T-006: twice FAILED. Initial packet omitted `special-pages.tsx`; retry asserted empty/partial states without a screen-specific filter/list contract. No test accepted; requires a route-specific applicability matrix before new work.
- T-026/T-027/T-028: depend on blocked T-006 state matrix.
- T-019: frontend runner lacks source; test in builder stage.
- T-014: split into ADR-002 backend/frontend/browser/acceptance packets T-050..055; implementation follows reproducing tests.

## Done this iteration (recent; older accepted evidence in git/LOOP.md)
- T-146 ✓ 0385a6e; pit strategy SQL reads moved to typed repository; focused 1 passed, Ruff 561/mypy 248; full isolated backend 118/0/0 and live acceptance passed.
- T-145 ✓ 2ff423e; fixture patches both main and future pit_repository SQL I/O boundaries, focused 1 passed, Ruff 561.
- T-144 ✓ f8e7e93; per-driver policy moved to pure service, focused 2 passed, Ruff 561/mypy 248; full backend 118/0/0 and live acceptance passed.
- T-143 ✓ c829c30; bounded pit Mongo reads moved to typed repository, focused 2 passed, Ruff 573/mypy 248.
- T-142 ✓ efd0261; seeded historical pit-strategy read contract 1 passed, Ruff 573.
- T-141 ✓ a8e25cf; Telemetry validation test imports schema module, focused 1 passed; full isolated backend 117/0/0 and live acceptance passed.
- T-140 ✓ 698dd2e; POST ingest moved to router, focused 2 passed, Ruff 573/mypy 248; full collection exposed stale test import.
- T-139 ✓ 57b488b; ingest write I/O moved to typed repository, seeded 1 passed, Ruff 582/mypy 252.
- T-138 ✓ e01de68; seeded ingest write contract 1 passed, exact-ID cleanup, Ruff 582.
- T-137 ✓ d006544; two GET handlers moved to telemetry router, seeded 1 passed, Ruff 582/mypy 252; full backend 116/0/0 and live acceptance passed.
- T-136 ✓ 029664e; old lifespan test mock targets get_pool, focused 1 passed; full isolated backend 116/0/0, live acceptance passed.
- T-135 ✓ e99d7ab; pool reopens for sequential lifespans, focused seeded tests 2 passed, Ruff 583/mypy 254; full gate exposed stale test mock.
- T-134 ✓ 2120ba9; two-lifespan strict xfail reproduced PoolClosed on second startup; Ruff 583.
- T-133 ✓ 2692cff; live GET repository extraction, seeded contract 1 passed, Ruff 583, mypy 254; full isolated gate exposed F-STRUCT-03.
- T-132 ✓ f1cc2b1; telemetry GET existence and Mongo query to typed repository, seeded contract 1 passed, Ruff 586, mypy 254; worker socket denied, orchestrator reran.
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
