# CURRENT_STATE
updated_at: 2026-10-22T20:32:20Z
git_head: 77e05b9
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
- Ruff 641 baseline -> 561 after T-144; mypy strict 311 baseline -> 248 after T-140; frontend strict lint 45 explicit-any errors. Ruff format 7 files at baseline. Coverage overall 72% isolated baseline; domain/service 90% target, overall 80% target remain open. Frontend npm audit had 7 high/2 moderate dev-tool findings; safe upgrade path open.
- F-ACE01 P2: login has no attempt throttling. T-006 twice failed: five-state fixtures need a route-specific applicability matrix before T-026..028. Role journeys, permissions matrix, simulator invariants, frontend visual states, docs, performance and evaluation score remain open in NEXT_STATE/queue.
- Phase 1 A/C/E P0/P1 findings closed after T-088. Phase 2 structure active: CRUD, analytics, pit, user and telemetry repositories; auth/operations/telemetry/competition/simulation schemas; analytics, pit read, user and telemetry APIRouters. ADR-004 single-process lease guards accepted; F-STRUCT-01/02 closed. ADR-003 full enforcement and P2 findings remain.
- T-133..T-136: F-STRUCT-03 psycopg pool could not reopen across app lifespans; strict regression reproduced it, W2 recreated the pool, test fixture updated without weaker assertions. Full isolated backend and live acceptance passed; finding closed.
- T-137..T-141: telemetry GET/live/ingest reads and writes moved to typed repository/router with seeded characterization. T-141 updated stale test schema import. Full isolated backend now passes 117 tests, zero failures/skips/xfails; live acceptance passes login, simulator, MongoDB, WebSocket, pits, standings, DBMS and generated races. Ruff 573, mypy 248. Next Phase 2 task: characterize pit strategy before splitting its oversized handler.
- T-142 pit-strategy seeded historical read contract passed 1/1 without fixture mutation, Ruff 573. T-143 extracts bounded Mongo pit telemetry read into pit_repository while preserving live/historical decisions.
- T-143 moved bounded latest packets and stop-history aggregation to typed pit_repository; seeded historical and live unit tests passed 2/2, Ruff 573/mypy 248. Full isolated gate pending after next pit-strategy split.
- T-144..T-147 split pit strategy policy, Mongo reads, SQL reads and GET handler into service/repository/router with preserved direct test import. After T-147: Ruff 559/mypy 248; full disposable backend 118 passed, zero failures/skips/xfails, live acceptance passed. Next T-148 extracts demo race read SQL.

## Orchestrator direct edits and Taste review
- Product: one `frontend/package.json` build-script line switched Next build to webpack (e854d9b). No other product-source edits.
- Removed accepted G11 xfail marker lines in backend/browser tests after focused verification; each corresponding isolated backend/browser suite was rerun. Corrected signed-out login mock (one test line), live WS fixture (19 test lines), and logout test breakpoint (one line, 768→700) to match CSS. Removed F-DOM-01/03/02 guard and steward UI xfail markers; full backend/browser gates passed. Removed one T-081 provisional xfail marker after T-082 acceptance; full isolated gate passed 90/0/0. Taste after T-080/T-084: no new focal, palette, clutter or bloat defect; existing large-file/spacing debt remains queued. Retired lease markers T-108/110/113/115/117/119/121/123 after their focused/full backend gates; last full backend count 112. T-125 test fixture needed a generated-ID correction and one line to keep cleanup defined if creation fails; worker socket was blocked, orchestrator reran on apexgrid-test.
