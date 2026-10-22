# CURRENT_STATE
updated_at: 2026-10-22T12:00:00Z
git_head: 620f12f
branch: perfection-loop
architect_sha256: 3a1222665ebf8483e8be75e745c319df3e15a1034382d662687e309e9b417d7a
archetype: enterprise-saas (5 signals); developer-tool secondary (3)
last_eval_score: NOT_RUN (quality gates and role journeys remain open)

## Verified setup and contracts
- Boot and architecture lock pass (ADR-003 relock 9e0a5a3). Work stays on `perfection-loop`. Disposable databases use only Compose project `apexgrid-test`, ports 15432/27018. Never touch running databases, secrets or master.
- PostgreSQL owns official race data; MongoDB owns telemetry. ADR-001/002 authorize additive migrations, finding-backed contract changes, and cookie/CSRF browser auth. Existing routes/data are preserved.
- Host venv Python 3.14/Node 26 differs from backend container Python 3.12/frontend container Node 22. Runtime parity gate remains open.

## Verified gates and components
- Isolated backend gate after T-086: 92 passed, 0 failed/skipped/xfailed; live acceptance passed login, simulator, MongoDB, WebSocket, pits, standings, DBMS, generated races. T-074 additive 002 migration applied on disposable stack; F-DOM-01 and F-DOM-03 closed. `pip-audit` runtime requirements had no known vulnerabilities at last run.
- Browser matrix after T-080: 745/745 passed across five Chromium projects. Desktop axe/keyboard sweep covered all 16 routes. G11 cookie/CSRF transport and browser journeys are verified with isolated backend, live acceptance and full browser gates. Steward time/grid controls are disabled with accessible guidance; focused desktop/mobile journey passed.
- Cookie auth: session/CSRF cookies, Origin checks, protected-write signed CSRF, cookie WebSocket, browser credentialed fetch, cookie-only /me, server logout and user-only browser login JSON are implemented. No-Origin bearer API and legacy WebSocket clients remain supported. T-069 verifies logout CSRF request and retry on 503. `getToken` removed by T-070.
- Frontend typecheck and webpack production build passed at last run. Phase 0 CI/full-gates harness accepted; `.agent/commands.env` has real E2E and zero-warning lint commands.

## Ratchet and open risks
- Ruff 641 baseline -> 627 after T-094; mypy strict 311 baseline -> 261 after T-093; frontend strict lint 45 explicit-any errors. Ruff format 7 files at baseline. Coverage overall 72% isolated baseline; domain/service 90% target, overall 80% target remain open. Frontend npm audit had 7 high/2 moderate dev-tool findings; safe upgrade path open.
- F-ACE01 P2: login has no attempt throttling. T-006 twice failed: five-state fixtures need a route-specific applicability matrix before T-026..028. Role journeys, permissions matrix, simulator invariants, frontend visual states, docs, performance and evaluation score remain open in NEXT_STATE/queue.
- Phase 1 A/C/E P0/P1 findings closed after T-088: unsupported new time/grid sanctions are rejected and historical classifications, standings and archive are labelled provisional. Isolated backend 92/92 and browser 775/775 pass; live acceptance and typecheck pass. Phase 2 structure active; T-015 extracted sector performance helper and six simulation tests pass. T-016 restored Ruff count to 633 with eight focused tests passing. T-089 moved Simulation/MAX_SESSION_LAPS to simulation_core, six tests pass and Ruff 632. T-090 pinned six seeded CRUD read routes. T-091 pinned two seeded CRUD write/role journeys; T-092 moved CRUD read I/O into crud_repository; six seeded cases pass. T-093 typed DB/simulation boundaries: mypy strict 261, Ruff 630, 14 focused tests pass. T-094 moved CRUD create/update I/O to repository; three seeded cases pass, mypy 261, Ruff 627. T-095 delete guard characterization then T-096 delete split. Full isolated backend after T-089/T-090: 98 passed, zero failed/skipped/xfailed, live acceptance passed. ADR-003 full enforcement remains P2 Phase 3 work; F-DOM-04/05, F-ACE01 and F-E02 remain P2.

## Orchestrator direct edits and Taste review
- Product: one `frontend/package.json` build-script line switched Next build to webpack (e854d9b). No other product-source edits.
- Removed accepted G11 xfail marker lines in backend/browser tests after focused verification; each corresponding isolated backend/browser suite was rerun. Corrected signed-out login mock (one test line), live WS fixture (19 test lines), and logout test breakpoint (one line, 768→700) to match CSS. Removed F-DOM-01/03/02 guard and steward UI xfail markers; full backend/browser gates passed. Removed one T-081 provisional xfail marker after T-082 acceptance; full isolated gate passed 90/0/0. Taste after T-080/T-084: no new focal, palette, clutter or bloat defect; existing large-file/spacing debt remains queued. Retired two T-083 browser xfail markers after the full 765-case gate, and the T-085 archive marker after the 92-case isolated backend gate.
