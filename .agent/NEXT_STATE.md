# NEXT_STATE
updated_at: 2026-10-25
phase: 3 T331 + 7 route redesign; Phases0–2,5–6 COMPLETE; no current score

## Queue
### T-44495 W2 — OPEN
- target_files: frontend/lib/live-stream.ts, frontend/lib/live-stream-types.ts, frontend/lib/use-live-timing-state.ts
- contract: T384 expose truthful snapshot loading/error settlement and a retry handle from the existing stream refresh, without extra timers or requests.
- verify: npm --prefix frontend run test:runtime && npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

### T-44494 W3 — OPEN
- target_files: frontend/e2e/runtime/live-timing-data.test.mjs
- contract: T384 regression-test actual derived interval, three-sector benchmark classification and tied fastest laps.
- verify: npm --prefix frontend run test:runtime && npm --prefix frontend run typecheck

### T-44493 W1 — OPEN
- target_files: frontend/components/pages/live/timing-tower.tsx
- contract: T384 render tyre, sector and fastest-lap domain cues and a truthful interval while preserving every timing field.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-neobrutal.sh

## Blocked
- T379 parent final gate: exact split complete, build/static0 and1020/1100mockedPASS; remaining15desktopA3layouts requirePhase7. Body/reducedmotion repaired; never mark fullsuitepassed. Proceed Phase7layouttasks as parentgate repairs, retain fullgate for finalrerun.

## Deferred
- TASTE-382-BLOAT: resource-page.tsx >300lines; split genuine reusable presentation/runtime responsibilities after T382 flow coverage, no single-call fake wrappers.

- TASTE-381-1: four KPIface accents followT381 but exceedT400 max3; consolidate supportingcolourbeforeA5, preserve data/features and thresholds.
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
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
