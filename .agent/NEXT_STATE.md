# NEXT_STATE
updated_at: 2026-10-25
phase: 3 T331 + 7 route redesign; Phases0–2,5–6 COMPLETE; no current score

## Queue
### T-44508 W1 — OPEN
- target_files: frontend/components/nb/chart-frame.tsx, frontend/components/pages/live/telemetry-charts.tsx, frontend/app/styles/live.css
- contract: T385 finish chart partial-state retry wording and scoped live chart/metadata layout.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-neobrutal.sh

### T-44510 W2 — OPEN
- target_files: frontend/lib/live-timing-data.ts
- contract: T384 derive completed pit-stop count per driver from supplied recorded pit history, leaving unavailable counts unknown.
- verify: npm --prefix frontend run test:runtime && npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

### T-44505 W1 — OPEN
- target_files: frontend/components/pages/live/race-records.tsx, frontend/components/pages/live/index.tsx
- contract: T385 render recorded laps and race-control history with actual five-state loading/retry and approved table/timeline presentation.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-neobrutal.sh

## Blocked
- T379 parent final gate: exact split complete, build/static0 and1020/1100mockedPASS; remaining15desktopA3layouts requirePhase7. Body/reducedmotion repaired; never mark fullsuitepassed. Proceed Phase7layouttasks as parentgate repairs, retain fullgate for finalrerun.

## Deferred
- TASTE-382-BLOAT: resource-page.tsx >300lines; split genuine reusable presentation/runtime responsibilities after T382 flow coverage, no single-call fake wrappers.

- TASTE-381-1: four KPIface accents followT381 but exceedT400 max3; consolidate supportingcolourbeforeA5, preserve data/features and thresholds.
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44507 acceptedab9660e; verify0.
- T-44506 acceptedc96573a; verify0.
- T-44504 acceptedd13765d; verify0.
- T-44503 accepteda8a1741; verify0.
- T-44502 accepted1d24522; verify0.
- T-44501 accepted63a8d91; verify0.
- T-44500 accepted5f8c134; verify0.
- T-44499 acceptedb1247fd; verify0.
- T-44498 acceptedf8b1888; verify0.
- T-44497 accepted3518121; verify0.
- T-44496 accepted401fdf1; verify0.
- T-44495 accepted9641a88; verify0.
- T-44493 accepted9f604dd; verify0.
- T-44494 accepted37a230e; verify0.
- T-44492 accepted0ba1b81; verify0.
- T-44491 acceptedafe1acd; verify0.
- T-44490 accepted1f267c0; verify0.
- T-44489 accepted2281e36; verify0.
- T-44488 accepted262f582; verify0.
- T-44487 accepted7e554e7; verify0.
- T-44486 acceptede52386c; verify0.
- T-44485 accepted60148e6; verify0.
- T-44484 accepted7ae0ac6; verify0.
- T-44482 accepteda13ec92; verify0.
- T-44483 accepted702e3cc; verify0.
- T-44481 accepted1d68f7b; verify0.
- Earlieracceptedtasks/hashes/evidence: Git/.agent/results.
