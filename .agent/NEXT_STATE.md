# NEXT_STATE
updated_at: 2026-10-22T20:54:39Z
loop_iteration: 1 of 5

## Queue (top-down; <=3 target files and <=150 changed lines per task)
### T-156 — Extract login route into APIRouter
- worker: W2 | priority: P2 | after: T-155
- target_files: backend/app/main.py, backend/app/auth_router.py
- contract: move login handler into a typed router while preserving cookie, bearer, Origin and main.fetch_one monkeypatch behavior; me/logout stay for the next packet
- verify: existing auth/cookie characterization tests; Ruff <=553, mypy <=226
## Blocked
- T-006: twice FAILED. Initial packet omitted `special-pages.tsx`; retry asserted empty/partial states without a screen-specific filter/list contract. No test accepted; requires a route-specific applicability matrix before new work.
- T-026/T-027/T-028: depend on blocked T-006 state matrix.
- T-019: frontend runner lacks source; test in builder stage.
- T-014: split into ADR-002 backend/frontend/browser/acceptance packets T-050..055; implementation follows reproducing tests.

## Done this iteration (recent; older accepted evidence in git/LOOP.md)
- T-155 ✓ 10f5c1d; DELETE route/orchestration moved into demo APIRouter; focused 5/5; full isolated backend 119/0/0 and live acceptance, Ruff 553/mypy 226.
- T-154 ✓ 5808275; ordered DELETE SQL moved to same-cursor repository helper; focused 4/4 on apexgrid-test, Ruff 554/mypy 227.
- T-153 ✓ cfe68ef; typed same-cursor DELETE preflight, four focused contracts passed; Ruff 555/mypy 227.
- T-152 ✓ df03eb2; POST moved to APIRouter, three focused checks passed; Ruff 556/mypy 227.
- T-151 ✓ bf608f2; creation SQL transaction moved to typed repository; 2 seeded tests passed, Ruff 558/mypy 248; full backend 119/0/0 and live acceptance passed.
- T-150 ✓ ed6bcaa; seeded persistence contract passed 1/1 on apexgrid-test after worker socket denial; Ruff 558.
- T-149 ✓ 4cae401; list GET moved to APIRouter. Worker socket denial and one Ruff regression corrected; seeded 1 passed, Ruff 558/mypy 248; full isolated backend 118/0/0 and live acceptance passed.
- T-148 ✓ 2a76b13; demo race read SQL moved to typed repository; seeded 1 passed after mypy repair, Ruff 558/mypy 248; full isolated backend 118/0/0 and live acceptance passed.
- T-147 ✓ 77e05b9; pit strategy GET moved to APIRouter and re-exported, focused 1 passed, Ruff 559/mypy 248; full isolated backend 118/0/0 and live acceptance passed.
- T-146 ✓ 0385a6e; pit strategy SQL reads moved to typed repository; focused 1 passed, Ruff 561/mypy 248; full isolated backend 118/0/0 and live acceptance passed.
- T-145 ✓ 2ff423e; fixture patches both main and future pit_repository SQL I/O boundaries, focused 1 passed, Ruff 561.
- T-144 ✓ f8e7e93; per-driver policy moved to pure service, focused 2 passed, Ruff 561/mypy 248; full backend 118/0/0 and live acceptance passed.
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
- T-001..T-124: accepted history and evidence in git/LOOP.md.
