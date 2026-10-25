# NEXT_STATE
updated_at: 2026-10-25
phase: 3 T331 + 7 route redesign; Phases0–2,5–6 COMPLETE; no current score

## Queue
### T-44370 W1 — OPEN
- target_files: frontend/components/special-pages.tsx
- contract: T379 remove unused legacy imports from compatibility page before final LiveTiming relocation.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

## Blocked
- None currently. Owner switch gpt-6-luna/high implemented and freshworkers succeeded.

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44369 accepted1d7f717; verify0.
- T-44368 accepted1af6714; verify0.
- T-44367 accepted5ac053e; verify0.
- T-44366 accepted627d48a; verify0. (full accepted history: git log and .agent/results)
- Worker switch: T44319 ba3fa7c, T44320 4645e52; custom roles gpt-6-luna/high.
- T44360 065361e stream wire; T44361 5bba15e CRUD router stage; T44362 cc361aa live polling.
- T44363 70bf3a3 nested-router test traversal; T44365 68e26c9 list refresh; T44364 a52fd5b CRUD wire.
- Phases0–2,5–6 complete. Login T380 complete0a3e206; remaining Phase7 pages dependT379.
- T379 Dashboard/Sessions/Stewards/Pit/Analytics/DBMS moves complete; only final Live local state/page move remains.
- Backend T331 remains main<=120; latest main1047lines. CRUD wire isolated full suite running T44364.full.raw.log.
