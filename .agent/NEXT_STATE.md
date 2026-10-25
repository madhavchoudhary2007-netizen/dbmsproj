# NEXT_STATE
updated_at: 2026-10-25
phase: 3 T331 + 7 route redesign; Phases0–2,5–6 COMPLETE; no current score

## Queue
### T-44532 W1 — OPEN
- target_files: frontend/components/pages/steward-sanctions.tsx
- contract: T387 make steward sanction fields readable and accessible with approved primitives while retaining unsupported-sanction guards.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-neobrutal.sh

### T-44531 W3 — OPEN
- target_files: frontend/e2e/session-resilience.spec.ts
- contract: T386 test same-frame session mutation spam and real result loading/error/retention/retry in the browser.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && cd frontend && npx playwright test e2e/session-resilience.spec.ts --list

## Blocked
- T379 parent final gate: exact split complete, build/static0 and1020/1100mockedPASS; remaining15desktopA3layouts requirePhase7. Body/reducedmotion repaired; never mark fullsuitepassed. Proceed Phase7layouttasks as parentgate repairs, retain fullgate for finalrerun.

## Deferred
- TASTE-382-BLOAT: resource-page.tsx >300lines; split genuine reusable presentation/runtime responsibilities after T382 flow coverage, no single-call fake wrappers.

- TASTE-381-1: four KPIface accents followT381 but exceedT400 max3; consolidate supportingcolourbeforeA5, preserve data/features and thresholds.
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44529 accepted82138ba; verify0.
- T-44527 accepted378faa0; verify0.
- T-44530 accepted8e83f3c; verify0.
- T-44528 accepted885b8ac; verify0.
- T-44526 accepted7897a78; verify0.
- T-44525 acceptedb301b9c; verify0.
- T-44524 accepted4666958; verify0.
- T-44522 accepted0935ce7; verify0.
- T-44523 accepted9a68302; verify0.
- T-44520 accepted2e68037; verify0.
- T-44521 accepted3f2d1fc; verify0.
- T-44519 acceptedd868cac; verify0.
- T-44517 accepteddede5cd; verify0.
- T-44516 accepted7023bc4; verify0.
- T-44518 acceptedeffb424; verify0.
- T-44515 accepted51b8121; verify0.
- T-44514 acceptedc48443f; verify0.
- T-44512 acceptedbe6cc11; verify0.
- T-44511 acceptedad39af5; verify0.
- T-44509 accepted1b65d17; verify0.
- T-44510 accepted1d3180f; verify0.
- T-44508 accepted040cb67; verify0.
- T-44505 accepted38165fc; verify0.
- T-44507 acceptedab9660e; verify0.
- T-44506 acceptedc96573a; verify0.
- T-44504 acceptedd13765d; verify0.
- T-44503 accepteda8a1741; verify0.
- T-44502 accepted1d24522; verify0.
- Earlier tasks: Git/.agent/results; parent milestones require full gates.

## Plan dependencies still required
- T387 penalty history and licence meter: existing incident/driver APIs expose no penalty history or season totals. Add documented read-only contracts under a dedicated ADR before wiring; do not infer zero.
- T385/M13 first chart draw animation remains for T400; actual stream updates remain animation-free.
