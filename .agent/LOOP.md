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
- Host pytest: 31 passed, 26 skipped; coverage overall 44.58% (777/1743 lines), app module percentages: bootstrap 0.0, config 88.2, database 50.0, main 43.6, race_archive 97.1. These numbers are not an isolated-stack baseline.
- Docker and local sockets required scoped sandbox escalation; the isolated stack started and was seeded successfully.
- Existing Playwright config and 16-route smoke test require stronger authenticated journey coverage. Login keyboard audit and responsive run are open from prior work.

## Findings
- F-A11, area D, P1, closed by T-039: `/login` copyright text was 3.88:1 against `#0b0e12` (axe serious at `frontend/app/globals.css:1073`); `--muted` yields 6.44:1. `RUN_XFAIL=1` reproduced before and passed after; marker removed.
- F-A12, area D, P1, closed by T-040: browser test waited for visible actionable control before Tab; desktop accessibility sweep passed 16/16 afterward.
- F-A13, area D, P1, closed by T-041: responsive audit root redirect and login/mobile action fixtures corrected; desktop browser project passed 96/96 route-width cases.
- F-A14, area D, P1, open: full browser gate failed 128 cases in the mobile-375 project because WebKit was missing; after installing it, the login 320px keyboard action still failed in WebKit while the same case passed in mobile-320 Chromium. The required matrix is viewport coverage, so T-042 will align the iPhone emulator to Chromium; WebKit testing can be a separately scoped cross-browser gate.

## Full-gates baseline (isolated stack, 2026-10-21)
- 10 gates ran; 6 failed: ruff check (641), ruff format (7 files), mypy strict (311), frontend strict lint (45 explicit `any`), browser E2E (mobile-375 WebKit issue), supply-chain audit (3 findings in `python-jose`/`ecdsa`). DB-backed pytest+acceptance, frontend typecheck/build, and backend coverage passed. Browser E2E reported 512 passing cases before the missing-WebKit failures.

## Blocked
- None confirmed for the isolated database baseline. Browser and quality gates remain open.
