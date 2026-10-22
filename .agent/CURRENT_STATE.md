# CURRENT_STATE
updated_at: 2026-10-22T18:37:28Z
git_head: 029664e
branch: perfection-loop
architect_sha256: c9780b9cd1ffe91fcb0fbf369b4b136205eb5c1ffb82e8cf199e42cca18c69c5
archetype: enterprise-saas (5 signals); developer-tool secondary (3)
last_eval_score: NOT_RUN (quality gates and role journeys remain open)

## Verified setup and contracts
- Boot and architecture lock pass (ADR-004 relock 07954ad). Work stays on `perfection-loop`. Disposable databases use only Compose project `apexgrid-test`, ports 15432/27018. Never touch running databases, secrets or master.
- PostgreSQL owns official race data; MongoDB owns telemetry. ADR-001/002 authorize additive migrations, finding-backed contract changes, and cookie/CSRF browser auth. Existing routes/data are preserved.
- Host venv Python 3.14/Node 26 differs from backend container Python 3.12/frontend container Node 22. Runtime parity gate remains open.

## Verified gates and components
- Isolated backend gate after T-086: 92 passed, 0 failed/skipped/xfailed; live acceptance passed login, simulator, MongoDB, WebSocket, pits, standings, DBMS, generated races. T-074 additive 002 migration applied on disposable stack; F-DOM-01 and F-DOM-03 closed. `pip-audit` runtime requirements had no known vulnerabilities at last run.
- Browser matrix after T-080: 745/745 passed across five Chromium projects. Desktop axe/keyboard sweep covered all 16 routes. G11 cookie/CSRF transport and browser journeys are verified with isolated backend, live acceptance and full browser gates. Steward time/grid controls are disabled with accessible guidance; focused desktop/mobile journey passed.
- Cookie auth: session/CSRF cookies, Origin checks, protected-write signed CSRF, cookie WebSocket, browser credentialed fetch, cookie-only /me, server logout and user-only browser login JSON are implemented. No-Origin bearer API and legacy WebSocket clients remain supported. T-069 verifies logout CSRF request and retry on 503. `getToken` removed by T-070.
- Frontend typecheck and webpack production build passed at last run. Phase 0 CI/full-gates harness accepted; `.agent/commands.env` has real E2E and zero-warning lint commands.

## Ratchet and open risks
- Ruff 641 baseline -> 602 after T-104; mypy strict 311 baseline -> 259 after T-102; frontend strict lint 45 explicit-any errors. Ruff format 7 files at baseline. Coverage overall 72% isolated baseline; domain/service 90% target, overall 80% target remain open. Frontend npm audit had 7 high/2 moderate dev-tool findings; safe upgrade path open.
- F-ACE01 P2: login has no attempt throttling. T-006 twice failed: five-state fixtures need a route-specific applicability matrix before T-026..028. Role journeys, permissions matrix, simulator invariants, frontend visual states, docs, performance and evaluation score remain open in NEXT_STATE/queue.
- Phase 1 A/C/E P0/P1 findings closed after T-088. Phase 2 structure active: CRUD, analytics, pit, user and telemetry GET repositories; auth/operations/telemetry/competition/simulation schemas; analytics, pit read and user APIRouters. ADR-004 lease primitive, lifespan ownership, HTTP/WS and simulator guards accepted. T-124 package-relative import accepted; strict T-123 marker retired. F-STRUCT-01/02 closed. T-125 auth/user contract and T-126..T-130 user extractions passed focused seeded checks on apexgrid-test; full isolated backend after T-130 passed 114, zero skip/fail/xfail, live acceptance passed. T-131/T-132 telemetry/live seeded read contract passed 1/1 with scoped Mongo cleanup. Ruff 586, mypy 254. ADR-003 full enforcement and P2 findings remain.
- T-133 live GET reads moved to typed telemetry repository; seeded contract passed 1/1 on apexgrid-test, Ruff 583, mypy 254. Full isolated suite then found F-STRUCT-03: global psycopg pool cannot reopen for a later TestClient lifespan (114 passed, 1 failed); T-134 reproducer and W2 repair are next. Live acceptance did not run because the gate stopped.
- T-134 strict two-lifespan regression accepted: ordinary seeded run 1 xfailed; --runxfail fails specifically on second lifespan PostgreSQL down/PoolClosed; Ruff 583. T-135 repairs database pool lifecycle, then marker retirement and full isolated gate are required.
- T-135 pool recreation/current-pool accessor accepted: both focused seeded contracts passed with --runxfail, Ruff 583, mypy 254. T-134 marker retired (two test lines, orchestrator). Full isolated gate then passed 115 and failed one legacy lifespan unit fixture because it monkeypatches removed `main.pool`; T-136 updates that mock to `main.get_pool`, preserving assertions. Live acceptance awaits full gate.
- T-136 updated the legacy test mock without changing assertions; focused test and unmarked two-lifespan regression pass. Full isolated backend now passes 116, zero failures/skips/xfails, and live acceptance passes. F-STRUCT-03 closed. Phase 2 next: T-137 read-only telemetry/live router extraction.

## Orchestrator direct edits and Taste review
- Product: one `frontend/package.json` build-script line switched Next build to webpack (e854d9b). No other product-source edits.
- Removed accepted G11 xfail marker lines in backend/browser tests after focused verification; each corresponding isolated backend/browser suite was rerun. Corrected signed-out login mock (one test line), live WS fixture (19 test lines), and logout test breakpoint (one line, 768→700) to match CSS. Removed F-DOM-01/03/02 guard and steward UI xfail markers; full backend/browser gates passed. Removed one T-081 provisional xfail marker after T-082 acceptance; full isolated gate passed 90/0/0. Taste after T-080/T-084: no new focal, palette, clutter or bloat defect; existing large-file/spacing debt remains queued. Retired lease markers T-108/110/113/115/117/119/121/123 after their focused/full backend gates; last full backend count 112. T-125 test fixture needed a generated-ID correction and one line to keep cleanup defined if creation fails; worker socket was blocked, orchestrator reran on apexgrid-test.
