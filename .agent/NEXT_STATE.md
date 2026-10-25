# NEXT_STATE
updated_at: 2026-10-25
phase: 3 T331 + 7 route redesign; Phases0–2,5–6 COMPLETE; no current score

## Queue
### T-44518 W1 — OPEN
- target_files: frontend/app/styles/live.css, frontend/components/nb/table.tsx
- contract: T385 fix the two populated-live accessibility failures without altering data or thresholds.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-neobrutal.sh

### T-44517 W3 — OPEN
- target_files: backend/tests/test_demo_route_dependencies.py
- contract: T332 verify generated-race DELETE uses a request DatabaseSession override and preserves delete error ordering.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_demo_route_dependencies.py backend/tests/test_contract_snapshot.py backend/tests/test_request_dependencies.py backend/tests/test_runtime_dependencies.py && .venv/bin/ruff check backend/tests/test_demo_route_dependencies.py && .venv/bin/ruff format --check backend/tests/test_demo_route_dependencies.py

### T-44516 W1 — OPEN
- target_files: frontend/components/pages/session-overview.tsx, frontend/components/pages/sessions.tsx
- contract: T386 restyle the Sessions header, session list and selected-session layout using the existing primitives.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-neobrutal.sh

## Blocked
- T379 parent final gate: exact split complete, build/static0 and1020/1100mockedPASS; remaining15desktopA3layouts requirePhase7. Body/reducedmotion repaired; never mark fullsuitepassed. Proceed Phase7layouttasks as parentgate repairs, retain fullgate for finalrerun.

## Deferred
- TASTE-382-BLOAT: resource-page.tsx >300lines; split genuine reusable presentation/runtime responsibilities after T382 flow coverage, no single-call fake wrappers.

- TASTE-381-1: four KPIface accents followT381 but exceedT400 max3; consolidate supportingcolourbeforeA5, preserve data/features and thresholds.
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
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
