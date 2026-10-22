# CURRENT_STATE
updated_at: 2026-10-21T18:40:00Z
git_head: 417d0d2
branch: perfection-loop
architect_sha256: 8753bfed50769fe28099f5f400bf3f7a42223fc98bebddda0db16eb7d0ece31b
archetype: enterprise-saas (5 signals); developer-tool secondary (3)
last_eval_score: NOT_RUN (quality gates and journey coverage remain open)

## Verified setup and contracts
- Boot and architecture lock pass. The branch is `perfection-loop`; isolated databases use only Compose project `apexgrid-test`, ports 15432/27018. Do not touch regular databases or secrets.
- Existing PostgreSQL schema and API wire fields remain authoritative (`docs/contracts.md`). MongoDB owns telemetry; PostgreSQL owns official race records. ADR-001 permits additive migrations and finding-backed contract changes with separate ADRs.
- Generated race lap cap 72; lap increments after sector three. SQL guards state transitions, pit overlap, results, and penalties.
- Host venv Python 3.14/Node 26 versus backend container Python 3.12/frontend container Node 22; frontend runner image lacks source/config for in-container typecheck/lint.

## Verified gates and components
- Isolated backend suite: 69 passed, 8 strict xfailed, 0 real skips; live acceptance passed PostgreSQL/MongoDB/WebSocket/pits/standings/DBMS/generated races. Backend runtime `pip-audit -r backend/requirements.txt`: no known vulnerabilities.
- Browser suite: 715/715 passed across five Chromium projects after all-route 375px touch-target audit. Desktop axe/keyboard sweep 16/16. Typecheck and webpack production build pass.
- Phase 0 CI/full-gates harness accepted in T-016. Remaining red quality gates: Ruff 639 violations, format 7 files, mypy strict 311 errors, frontend strict lint 45 explicit-any errors, frontend npm audit 7 high/2 moderate dev-tool findings. Backend coverage target and full route journeys remain unverified.
- `.agent/commands.env` now names the real Playwright E2E command and zero-warning frontend lint; CI already runs all gates through `full-gates.sh`.
- Existing 16 routes and DBMS views remain IN_REVIEW for five UI states and role journeys. `ViewState<T>` typed boundary is VERIFIED; shared partial notice is not wired to screens.

## Ratchet and open risks
- Ruff baseline 641→639 before T-052; T-061/T-062 reduced current count to 633. Mypy 311; strict lint 45. Spacing lint has off-scale CSS and border-width false positives; motion/banned lint pass.
- T-006 twice failed: generic five-state fixtures overasserted empty/partial states without a route-specific applicability matrix. T-026..028 depend on it. T-014 cookie/CSRF migration (ADR-001) needs separate backend/frontend/test packets.
- Frontend dev-tool advisories need a safe upgrade path; `npm audit fix --dry-run` offers only in-range `eslint-config-next` and selector-parser updates, and Tailwind 4 is major.
- Runtime parity, permissions matrix, simulator invariants, role journeys, full evaluation score, and docs audit remain open. `NEXT_STATE.md` is the queue.
- T-012 simulation boundaries passed 6 focused tests with Ruff steady at 639; T-013 deployment-secret gate passed 5 subprocess cases. ADR-002 plans browser cookie/CSRF migration; architecture relocked at 8753bfed after focused five-lens review, implementation unstarted.
- T-060 accepted: three strict G11 cookie-write/Origin tests xfail normally and fail with --runxfail (all return 200 before the fix). T-059 audit found F-ACE01 P2: login has no attempt throttling; its verify passed, and its audit file was included in T-060's broad .agent commit.
- T-052 accepted at 4353aaa and T-053 at 7b63377: cookie writes validate Origin/signed CSRF, logout clears cookies, cookie WS validates Origin; legacy bearer and WS subprotocol still work. T-061 at a47d81a wrapped three Ruff E501 test signatures. After orchestrator removed all remaining G11 xfail markers, disposable-stack backend gate passed 80 tests, 0 skips/xfails, plus live acceptance.
- T-063 at d2e22b3 added two strict browser cookie-auth reproductions; RUN_XFAIL=1 confirms cookie-only startup skips /me and login writes localStorage. Frontend API/provider and WS client remain to migrate.
- T-054 accepted at a11619b: browser fetch sends credentials and CSRF; provider probes /me, login skips token storage, logout requires server success. The two focused cookie browser journeys pass. Full Playwright run reached 269 passed then stopped at 10 responsive `/login` failures: older fixtures return authenticated /me for login and hide the form; T-066 fixture migration queued. Live WS client still pending.
- T-066 accepted at 724e732: three audit fixtures use cookie-based /me and a signed-out login response. Full Playwright matrix exits 0 with 725/725 passed across five projects. Live WS browser reproduction and client migration are next.
- T-064/T-055 accepted at cc828eb/f09d80f. Corrected the browser WebSocket fixture to preserve Next's own socket; with RUN_XFAIL=1 it failed on the old token gate and passed on the new cookie client. Marker removed; full Playwright matrix exits 0 with 730/730. Browser login response still includes a bearer token despite ADR-002; T-067 is next.
- T-067 accepted at a103d2f: strict xfail reproduces browser Origin login JSON leaking access_token/token_type, while no-Origin legacy token assertion passes. Ruff remains 633. T-068 backend response fix is next.
- T-068 accepted at 417d0d2: allowed-Origin login returns `{user}` only; no-Origin legacy token response remains. Ruff 633. Removed xfail; isolated backend suite 82 passed/0 skips/xfails, plus live acceptance. Browser logout/CSRF verification is next.
- Phase 0 complete; 16-route browser smoke, isolated database and live acceptance, characterization tests, quality metrics, CI gates and deployment-secret regression are in place. T-050's eight strict cookie/CSRF xfails reproduce with --runxfail; coverage overall 72%, main 72%, database 100%, config 88%, race_archive 97%, bootstrap 0%. T-051 added session/CSRF cookies and cookie /me; legacy bearer JSON remains until coordinated frontend migration.

## Orchestrator direct edits and Taste review
- Product source: one `frontend/package.json` build-script line switched Next build to webpack due Turbopack bind failure (logged at e854d9b). No other product-source edits.
- Removed accepted strict xfail markers and unused pytest import from security/touch tests (6 test lines total), then reran full suites. T-009/T-049 CSS changes added no dependency, abstraction, palette, or new focal action; no new Taste defect in their diff. Existing large-file/spacing debt remains queued.
- Removed 8 accepted G11 xfail marker lines in backend/tests/test_api.py after T-052; isolated DB and live acceptance rerun passed.
- Removed 2 accepted WebSocket xfail marker lines in backend/tests/test_api.py after T-053; isolated DB and live acceptance rerun passed.
- Removed 2 accepted G11 browser expected-failure markers after T-054. Corrected the signed-out login fixture (one test line); both focused journeys then passed.
- Corrected the W3 live WebSocket fixture (19 test lines) to preserve Next dev's socket and confirmed old-client failure/new-client pass; removed its accepted xfail marker after T-055. Full browser suite passed.
