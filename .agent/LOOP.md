# Perfection loop
branch: perfection-loop
phase: 0 — safety net, in progress
cycle: 0 of 8
score: NOT_RUN

## Phase 0 baseline
- Architecture lock passed at boot (`4cd5bc0272d02c031ca5ea833f1f07b200444efa866448f4549a5f68dab7ca73`).
- Isolated `apexgrid-test` run (2026-10-21): 57 passed, 0 failed, 0 skipped; live acceptance passed against loopback API on port 18000. T-002 paginated `/events` to find the seeded round 3 event.
- Initial host baseline with DB URLs unset: ruff 641 violations (E501 353, B008 85, E701 53, E702 39, UP017 31, C901 12), ruff format 7 files, mypy strict 311 errors. Frontend typecheck and existing lint exit 0; strict zero-warning lint is pending a corrected command.
- Strict frontend lint with `@typescript-eslint/no-explicit-any` enabled: 45 errors, 0 warnings (2026-10-21); this is the ratchet baseline for explicit `any` removal.
- T-043 added seven database-independent auth characterization tests; focused run passed 7/7 and Ruff count improved from 641 to 639.
- T-044 pinned F-E01 with a strict xfail runtime-requirements check; `--runxfail` produced the expected failure while `python-jose` remains in requirements.
- Host pytest: 31 passed, 26 skipped; coverage overall 44.58% (777/1743 lines), app module percentages: bootstrap 0.0, config 88.2, database 50.0, main 43.6, race_archive 97.1. These numbers are not an isolated-stack baseline.
- Docker and local sockets required scoped sandbox escalation; the isolated stack started and was seeded successfully.
- Existing Playwright config and 16-route smoke test require stronger authenticated journey coverage. Login keyboard audit and responsive run are open from prior work.

## Findings
- F-A11, area D, P1, closed by T-039: `/login` copyright text was 3.88:1 against `#0b0e12` (axe serious at `frontend/app/globals.css:1073`); `--muted` yields 6.44:1. `RUN_XFAIL=1` reproduced before and passed after; marker removed.
- F-A12, area D, P1, closed by T-040: browser test waited for visible actionable control before Tab; desktop accessibility sweep passed 16/16 afterward.
- F-A13, area D, P1, closed by T-041: responsive audit root redirect and login/mobile action fixtures corrected; desktop browser project passed 96/96 route-width cases.
- F-A14, area D, P1, closed by T-042: mobile-375 now uses Chromium with iPhone touch/viewport emulation. Its responsive matrix passed 96/96 and the full browser suite passed 640/640 across five projects.
- F-E01, area E, P0, closed by T-045: replaced `python-jose` 3.5.0 (unpatched critical [algorithm-confusion advisory](https://github.com/advisories/GHSA-3qf3-8w2g-rqmx)) with PyJWT 2.15.1. HS256 is explicitly allowed in both decode paths. Seven auth characterization checks and the security invariant pass; backend `pip-audit` reports no known vulnerabilities; isolated suite 65/0/0 and live acceptance pass.
- F-E02, area E, P2, open: `npm audit` reports 7 high and 2 moderate findings in the frontend dev-tool chain, through Tailwind 3 and `eslint-config-next`; suggested fixes are major dependency changes. Evaluate targeted safe upgrades before any major migration.
- F-D07, area D, P1, fix under verification: T-046 found 51 undersized controls at 375px across four routes. T-009 raised shared nav/button/select/login controls to >=44px; T-047 excluded only the injected Next.js Dev Tools button. Full browser suite passed 645/645 across five projects. T-048 will extend the touch audit from four to all 15 nonredirect routes.

## Full-gates baseline (isolated stack, 2026-10-21)
- 10 gates ran; 6 failed: ruff check (641), ruff format (7 files), mypy strict (311), frontend strict lint (45 explicit `any`), browser E2E (mobile-375 WebKit issue), supply-chain audit (3 findings in `python-jose`/`ecdsa`). DB-backed pytest+acceptance, frontend typecheck/build, and backend coverage passed. Browser E2E reported 512 passing cases before the missing-WebKit failures.
- After T-042, the full browser gate passed 640/640 cases in 1.1 minutes; remaining red gate count is five. The frontend audit, run separately, found 7 high and 2 moderate issues; the combined gate stops at the backend audit failure.

## Blocked
- None confirmed for the isolated database baseline. Browser and quality gates remain open.
