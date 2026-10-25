# NEXT_STATE
updated_at: 2026-10-25
phase: 3 T331 + 7 route redesign; Phases0–2,5–6 COMPLETE; no current score

## Queue
### T-44417 W1 — OPEN
- target_files: frontend/components/pages/dashboard.tsx, frontend/app/styles/dashboard.css
- contract: T381 wire genuine WebSocket and runtime-lease observations into the existing service health card.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-neobrutal.sh

### T-44416 W3 — OPEN
- target_files: frontend/e2e/runtime/dashboard-connectivity.test.mjs
- contract: T381 execute the actual connectivity transport helpers in VM tests before UI adoption.
- verify: npm --prefix frontend run test:runtime && npm --prefix frontend run lint -- --max-warnings 0

### T-44415 W3 — OPEN
- target_files: frontend/e2e/race-control-feed.spec.ts
- contract: T381 adopt explicit platform mocks in the remaining mocked dashboard race-control feed suite.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && cd frontend && ./node_modules/.bin/playwright test e2e/race-control-feed.spec.ts --list

## Blocked
- T379 parent final gate: exact split complete, build/static0 and1020/1100mockedPASS; remaining15desktopA3layouts requirePhase7. Body/reducedmotion repaired; never mark fullsuitepassed. Proceed Phase7layouttasks as parentgate repairs, retain fullgate for finalrerun.

## Deferred

- TASTE-381-1: four KPIface accents followT381 but exceedT400 max3; consolidate supportingcolourbeforeA5, preserve data/features and thresholds.
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44414 accepted95bf890; verify0.
- T-44413 accepted1a4871f; verify0.
- T-44412 acceptedfd9629d; verify0.
- T-44411 accepted6b9fd8c; verify0.
- T-44410 accepted6b6cf24; verify0.
- T-44409 accepted5b1d8f4; verify0.
- T-44408 accepted1ffce81; verify0.
- T-44407 acceptedb87fee6; verify0.
- T-44406 acceptedd018de6; verify0.
- T-44405 acceptedd756a9f; verify0.
- T-44404 accepted5a0ad53; verify0.
- T-44403 accepted4521ac9; verify0.
- T-44402 accepted104bdb8; verify0.
- T-44401 accepted60c4999; verify0.
- T-44400 accepted67d0603; verify0.
- T-44398 acceptedda48958; verify0.
- T-44399 accepted1924d64; verify0. (full history in Git/results)
- Latest T44397 133240e fixture guards, T44396 894f75e incidents UI, T44395 22c7e77 app factory, T44394 3226b70 recovery contracts, T44393 69e17d0 browser spec, T44392 6f7d543 incidents hook, T44391 fb08ca2 states/Next up, T44390 09d5636 runtime regressions, T44388 0f0ec37 sources.
- Phases0–2,5–6 complete; T380 login complete0a3e206. T379 exact route split complete but full parent gate pending. Main846lines; root backend231PASS0skip/livePASS T44395.
