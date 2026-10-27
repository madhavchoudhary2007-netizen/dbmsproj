# NEXT_STATE
updated_at: 2026-10-27
branch: overhaul/neo-brutal
execution: RUNNING
phase: 9 tests & visual regression; Phase 8 complete

## Queue (root must prepare exact packets before dispatch)
### T-410 — Playwright webServer production/CI mode
- worker: W3 | priority: P1 | origin: Phase 9 T-410 Playwright CI webServer
- target_files: frontend/playwright.config.ts
- contract: Update webServer in frontend/playwright.config.ts to use next build && next start -p 3100 (or npm run start) when CI or PLAYWRIGHT_USE_PROD is set, while preserving next dev locally.
- verify: npm --prefix frontend exec -- playwright test --config frontend/playwright.config.ts e2e/routes.spec.ts

### T-411 — Real-stack project and end-to-end happy paths (Hard Gate F-4)
- worker: W3 | priority: P1 | origin: Phase 9 T-411 Real-stack Playwright Project
- target_files: frontend/playwright.config.ts, frontend/e2e/real-stack.spec.ts
- contract: Add real-stack project in playwright.config.ts (desktop-1440, mobile-375) without page.route mocks against backend on 18000 (SEED_DEMO=1); cover login, dashboard, live timing updates, steward actions, standings recalculation.
- verify: npm --prefix frontend exec -- playwright test --config frontend/playwright.config.ts --project=real-stack

### T-413 — Motion specifications and P-5 perf-fps threshold
- worker: W3 | priority: P1 | origin: Phase 9 T-413 Motion specs & P-5
- target_files: frontend/e2e/motion-hooks.spec.ts, frontend/e2e/perf-fps.spec.ts
- contract: Assert reduced motion gives 0 running animations across routes; marquee animates only transform; FLIP <= 350ms; perf-fps asserts p95 <= 16.7ms and heap growth < 1MB.
- verify: npm --prefix frontend exec -- playwright test --config frontend/playwright.config.ts e2e/motion-hooks.spec.ts e2e/perf-fps.spec.ts

### T-415 — Backend coverage hardening and tie-break specs
- worker: W3 | priority: P1 | origin: Phase 9 T-415 Backend coverage & tie-breaks
- target_files: backend/tests/test_points_system.py, backend/tests/test_standings_tiebreak.py
- contract: Add standings tie-break unit tests and verify backend coverage meets >= 80% threshold across backend/app.
- verify: APEXGRID_TEST_STACK=1 DATABASE_URL='postgresql://apexgrid:apexgrid@localhost:15432/apexgrid' MONGODB_URL='mongodb://localhost:27018' MONGODB_DATABASE=apexgrid APP_ENV=local PYTHONPATH=backend:. .venv/bin/pytest -q backend/tests/test_points_system.py backend/tests/test_standings_tiebreak.py

## Integration debt / deferred
- Real-stack test runs against apexgrid-test on 18000 / 15432 / 27018.
- CI workflows (T-420) and docs (T-421) queued for Phase 10.
- Final scoring (T-430) and cleanup (T-431) queued for Phase 11.
