# NEXT_STATE
updated_at: 2026-10-22T14:15:00Z
loop_iteration: 1 of 5

## Queue (top-down; <=3 target files and <=150 changed lines per task)
### T-123 — Reproduce Uvicorn app.main import failure
- worker: W3 | priority: P0 | origin: F-STRUCT-02
- target_files: backend/tests/test_runtime_lease.py
- contract: strict subprocess expected-failure test imports app.main from backend cwd without adding repo root to PYTHONPATH
- verify: APP_ENV=local .venv/bin/pytest -q backend/tests/test_runtime_lease.py -k uvicorn_import_contract
## Blocked
- T-006: twice FAILED. Initial packet omitted `special-pages.tsx`; retry asserted empty/partial states without a screen-specific filter/list contract. No test accepted; requires a route-specific applicability matrix before new work.
- T-026/T-027/T-028: depend on blocked T-006 state matrix.
- T-019: frontend runner lacks source; test in builder stage.
- T-014: split into ADR-002 backend/frontend/browser/acceptance packets T-050..055; implementation follows reproducing tests.

## Done this iteration (pruned on compaction)
- T-122 ✓ 9e09f97; paused/running simulator guards pass, Ruff 600, mypy 259; marker retired, full isolated backend 111 passed. Live API startup failed import; F-STRUCT-02 queued.
- T-121 ✓ dee5f57; two strict simulator xfails accepted; --runxfail proves paused hang and running DB read after lease loss, Ruff 600.
- T-120 ✓ d5ebb3c; idle WS bounded check passed, Ruff 600, mypy 259; marker retired, full isolated backend 109 passed, zero skip/fail/xfail.
- T-119 ✓ 5dbed9a; strict idle WS xfail accepted; --runxfail retains subscriber after loss, Ruff 600.
- T-118 ✓ 883edc5; active WS pre-send guard --runxfail passed, Ruff 600, mypy 259; marker retired, full isolated backend 108 passed, zero skip/fail/xfail.
- T-117 ✓ 655b2a7; strict active WS xfail accepted; --runxfail delivers stale event, Ruff 600.
- T-116 ✓ 56f437e; WS handshake guard --runxfail passed, Ruff 600, mypy 259; marker retired, full isolated backend 107 passed, zero skip/fail/xfail.
- T-115 ✓ 5f5248a; strict WS xfail accepted; --runxfail gives 4401 rather than 1011, Ruff 600.
- T-114 ✓ d2a9613; HTTP fail-closed --runxfail passed, Ruff 600, mypy 259; marker retired, full isolated backend 106 passed, zero skip/fail/xfail.
- T-113 ✓ 86c4ecb; strict lease-loss HTTP xfail accepted; --runxfail sees health 200 after owner close, Ruff 602.
- T-112 ✓ 8c273d6; two lease tests moved to standalone module, full isolated backend 105 passed, zero skip/fail/xfail; Ruff 602.
- T-111 ✓ ec2546b; focused --runxfail 2 passed; full suite 103 passed/2 fixture conflict failures, T-112 queued.
- T-110 ✓ 7721eca; strict lifespan xfail accepted, --runxfail fails old startup with DID NOT RAISE; Ruff 602.
- T-109 ✓ 6ca5226; scoped --runxfail passed on apexgrid-test, Ruff 602, mypy 259; marker retired and full backend 104 passed, zero skip/fail/xfail.
- T-108 ✓ 43af11a; 1 strict xfail, 0 skip; --runxfail fails on missing lease module; Ruff 602.
- T-107 ✓ 1edbcbf; remaining request schemas extracted, 4 seeded/focused cases, Ruff 602, mypy 259.
- T-106 ✓ fcba18d; pit GET APIRouter, 3 focused seeded/route cases, Ruff 602, mypy 259.
- T-105 ✓ 072f240; OpenAPI route inventory repair, 2 cases, full isolated backend 103 passed, no skips/failures.
- T-104 ✓ ee93cac; dashboard/analytics APIRouter contract passed, Ruff 602, mypy 259; full backend revealed two route-inventory test assumptions, T-105 queued.
- T-103 ✓ 9212d0b; Telemetry model extracted, 8 no-skip focused cases, Ruff 603, mypy 259.
- T-102 ✓ 0802a3d; operations request models extracted, 9 cases, Ruff 603, mypy 259.
- T-101 ✓ 9604441; auth request models to schemas_auth, 8 focused cases, Ruff 603, mypy 261.
- T-100 ✓ c3f002e; pit box/reservation reads to repository; 3 focused cases, Ruff 603, mypy 261.
- T-099 ✓ efc9feb; seeded pit box/reservation read contract, 1 case, Ruff 605.
- T-098 ✓ f8adaf9; dashboard/analytics SQL to repository, 1 seeded case, Ruff 605, mypy 261.
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
