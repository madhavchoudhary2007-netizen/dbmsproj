# Perfection loop
branch: perfection-loop
phase: 1 — correctness and security, in progress
cycle: 0 of 8
score: NOT_RUN

## Phase 0 baseline
- Architecture lock passed at boot, then ADR-002 cookie/CSRF contract was relocked at `8753bfed50769fe28099f5f400bf3f7a42223fc98bebddda0db16eb7d0ece31b` after focused five-lens review. Implementation remains open.
- Isolated `apexgrid-test` run (2026-10-21): 57 passed, 0 failed, 0 skipped; live acceptance passed against loopback API on port 18000. T-002 paginated `/events` to find the seeded round 3 event.
- Initial host baseline with DB URLs unset: ruff 641 violations (E501 353, B008 85, E701 53, E702 39, UP017 31, C901 12), ruff format 7 files, mypy strict 311 errors. Frontend typecheck and existing lint exit 0; strict zero-warning lint is pending a corrected command.
- Strict frontend lint with `@typescript-eslint/no-explicit-any` enabled: 45 errors, 0 warnings (2026-10-21); this is the ratchet baseline for explicit `any` removal.
- T-043 added seven database-independent auth characterization tests; focused run passed 7/7 and Ruff count improved from 641 to 639.
- T-044 pinned F-E01 with a strict xfail runtime-requirements check; `--runxfail` produced the expected failure while `python-jose` remains in requirements.
- T-012 added deterministic simulation boundaries (0/1 lap, fixed clock/seed, stop cleanup): 6 focused tests pass; Ruff remains 639. T-013 deployment-secret subprocess gate passes 5/5 cases without printing secret values.
- T-050 added eight strict cookie/CSRF reproducing tests; normal run 8 xfail, --runxfail 8 failed before implementation. Isolated-stack coverage baseline after T-050: 69 passed, 8 xfailed, 0 real skips; bootstrap 0%, config 88%, database 100%, main 72%, race_archive 97%, overall 72%.
- T-051/T-052/T-053 implemented cookie session/CSRF/Origin and WebSocket cookie transport. All eight G11 xfail markers plus T-060's three guard markers were retired after focused verification. The isolated suite and live acceptance passed with 80 tests, zero failed/skipped/xfailed (2026-10-22). Browser and acceptance fixture migration remains open, so G11 is not closed.
- T-054 frontend cookie API/provider: typecheck and two focused cookie journeys pass. Full browser gate after marker removal stopped at 10 responsive `/login` failures (269 passed before `--max-failures=10`); old fixtures return a user from `/me` on the login route. T-066 owns fixture migration; this browser gate is OPEN, not scored passing.
- T-066 migrated the responsive, accessibility, and touch fixtures to cookie-based `/me` state. Full Playwright gate then exited 0: 725 passed across five projects (2026-10-22). Live WS client remains open, so G11 is still open.
- T-064/T-055 migrated the live WebSocket client to cookie transport. The corrected test preserves Next's HMR socket and was proven failing on the old client and passing on the new client. Full Playwright gate exited 0: 730 passed across five projects (2026-10-22). Login JSON still exposes a bearer token to browser callers, and logout/CSRF browser coverage remains open, so G11 is not closed.
- T-067/T-068 removed bearer credentials from allowed-Origin browser login JSON while retaining no-Origin legacy API compatibility. Isolated backend gate exited 0: 82 passed, 0 failed/skipped/xfailed, plus live acceptance (2026-10-22). Logout/CSRF browser coverage remains open.
- T-069 added desktop browser logout success and 503 retry/CSRF checks (4 focused cases passed); T-070 removed the inert token helper with typecheck passing. Full browser matrix: 736 passed, 4 new mobile logout cases failed because the test did not open the mobile navigation; T-071 fixture repair queued. G11 remains open.
- T-071 opened the mobile navigation in both logout journeys without changing assertions. Acceptance reran all six focused desktop/mobile cases successfully (2026-10-22); full matrix remains to rerun.
- Full 740-case browser matrix then exposed two tablet-768 fixture failures: the menu exists only at CSS max-width 700px. Orchestrator corrected one test helper line; rerun exited 0 with 740 passed across five projects (2026-10-22). G11 backend/browser/acceptance gates are now green; cookie transport finding closed.
- T-073 added isolated F-DOM-01 strict xfail and numbered migration fixture. Normal focused run: 1 xfailed, 0 skipped; `--runxfail` failed because an unclassified driver received 2 bonus points (2026-10-22). Worker socket access was blocked; orchestrator reran both checks on disposable `apexgrid-test` and accepted the packet.
- Phase 0 closed after T-057/T-058: the isolated `db-baseline.sh` run passed 69 tests, separately reported 8 xfails and 0 real skips, and passed live acceptance; CI now runs all 11 full gates including deployment-secret regression and rejects unreachable registries. Browser smoke/responsive suite passed 715/715 across five projects and all 16 routes. Quality gates remain recorded red targets, not claimed passing.
- Host pytest: 31 passed, 26 skipped; coverage overall 44.58% (777/1743 lines), app module percentages: bootstrap 0.0, config 88.2, database 50.0, main 43.6, race_archive 97.1. These numbers are not an isolated-stack baseline.
- Docker and local sockets required scoped sandbox escalation; the isolated stack started and was seeded successfully.
- Existing Playwright config and 16-route smoke test require stronger authenticated journey coverage. Login keyboard audit and responsive run are open from prior work.

## Findings
- F-DOM-01, area A, P1, open: unclassified session results earn pole/fastest-lap points through unconditional terms in `recalculate_standings` (`backend/migrations/001_initial.sql:264`); T-073/T-074 test-first fix queued.
- F-DOM-02, area A, P1, open: approved time/grid penalties are stored but do not affect official classification or starting order (`backend/app/main.py:707-745,800-801`); define enforcement rule and test before fix.
- F-DOM-03, area A, P1, open: result upserts allow classified position gaps (`backend/app/main.py:727-744`); test and enforce at publication boundary.
- F-DOM-04, area A, P2, open: telemetry insert/broadcast accepts duplicate and older packets (`backend/app/main.py:914-932`); test ordering/idempotency.
- F-DOM-05, area A, P2, open: production simulator uses global random state without persisted seed (`backend/app/main.py:1451-1455,1661`); test restart/replay determinism.
- F-ACE01, area C/E, P2, open: `/api/auth/login` does not throttle repeated invalid guesses (`backend/app/main.py:509-529`); the independent Phase 1 audit in `.agent/audit/phase1-ace.md` records evidence and the required per-account/per-source limit.
- F-A11, area D, P1, closed by T-039: `/login` copyright text was 3.88:1 against `#0b0e12` (axe serious at `frontend/app/globals.css:1073`); `--muted` yields 6.44:1. `RUN_XFAIL=1` reproduced before and passed after; marker removed.
- F-A12, area D, P1, closed by T-040: browser test waited for visible actionable control before Tab; desktop accessibility sweep passed 16/16 afterward.
- F-A13, area D, P1, closed by T-041: responsive audit root redirect and login/mobile action fixtures corrected; desktop browser project passed 96/96 route-width cases.
- F-A14, area D, P1, closed by T-042: mobile-375 now uses Chromium with iPhone touch/viewport emulation. Its responsive matrix passed 96/96 and the full browser suite passed 640/640 across five projects.
- F-E01, area E, P0, closed by T-045: replaced `python-jose` 3.5.0 (unpatched critical [algorithm-confusion advisory](https://github.com/advisories/GHSA-3qf3-8w2g-rqmx)) with PyJWT 2.15.1. HS256 is explicitly allowed in both decode paths. Seven auth characterization checks and the security invariant pass; backend `pip-audit` reports no known vulnerabilities; isolated suite 65/0/0 and live acceptance pass.
- F-E02, area E, P2, open: `npm audit` reports 7 high and 2 moderate findings in the frontend dev-tool chain, through Tailwind 3 and `eslint-config-next`; suggested fixes are major dependency changes. Evaluate targeted safe upgrades before any major migration.
- F-D07, area D, P1, closed by T-009/T-047: 51 undersized shared mobile controls fixed; injected Next.js toolbar excluded from product audit.
- F-D08, area D, P1, closed by T-049: `.search input` was 177.5×16.5px on six table routes at 375px; wrapper and input now 44px high. RUN_XFAIL=1 passed all 15 mobile routes; marker removed; full browser matrix passed 715/715 across five projects.
- F-F01, area F, P1, closed by T-057: pytest JUnit encodes deliberate strict G11 xfails as `skipped type=pytest.xfail`; the parser reports them separately while rejecting real skips. Five synthetic checks and isolated-stack gate pass (69 passed, 8 xfailed, 0 skipped; live acceptance passed).

## Full-gates baseline (isolated stack, 2026-10-21)
- 10 gates ran; 6 failed: ruff check (641), ruff format (7 files), mypy strict (311), frontend strict lint (45 explicit `any`), browser E2E (mobile-375 WebKit issue), supply-chain audit (3 findings in `python-jose`/`ecdsa`). DB-backed pytest+acceptance, frontend typecheck/build, and backend coverage passed. Browser E2E reported 512 passing cases before the missing-WebKit failures.
- After T-042, the full browser gate passed 640/640 cases in 1.1 minutes; remaining red gate count is five. The frontend audit, run separately, found 7 high and 2 moderate issues; the combined gate stops at the backend audit failure.

## Blocked
- None confirmed for the isolated database baseline. Browser and quality gates remain open.
