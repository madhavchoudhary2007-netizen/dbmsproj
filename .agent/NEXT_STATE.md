# NEXT_STATE
updated_at: 2026-10-25
phase: 3 T331 + 7 route redesign; Phases0–2,5–6 COMPLETE; no current score

## Queue
### T-44402 W1 — OPEN
- target_files: frontend/components/pages/dashboard.tsx, frontend/app/styles/dashboard.css
- contract: T381 compact the dashboard supporting-paper cards with consistent legal spacing, resolving the last desktop palette-layout failure.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-neobrutal.sh

### T-44401 W2 — OPEN
- target_files: backend/app/core/runtime.py
- contract: T331/T332 prerequisite: typed application runtime container and FastAPI request/WS dependency getters; stage before removing legacy compatibility bindings.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/python -c "from backend.app.core.runtime import RuntimeState; print('PASS runtime module imports without connecting resources')" && .venv/bin/mypy --strict --follow-imports=silent backend/app/core/runtime.py && .venv/bin/ruff check backend/app backend/tests && .venv/bin/ruff format --check backend/app/core/runtime.py

## Blocked
- T379 parent final gate: exact split complete, build/static0 and1020/1100mockedPASS; remaining15desktopA3layouts requirePhase7. Body/reducedmotion repaired; never mark fullsuitepassed. Proceed Phase7layouttasks as parentgate repairs, retain fullgate for finalrerun.

## Deferred
- TASTE-381-1: four KPIface accents followT381 but exceedT400 max3; consolidate supportingcolourbeforeA5, preserve data/features and thresholds.
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44400 accepted67d0603; verify0.
- T-44398 acceptedda48958; verify0.
- T-44399 accepted1924d64; verify0. (full history in Git/results)
- Latest T44397 133240e fixture guards, T44396 894f75e incidents UI, T44395 22c7e77 app factory, T44394 3226b70 recovery contracts, T44393 69e17d0 browser spec, T44392 6f7d543 incidents hook, T44391 fb08ca2 states/Next up, T44390 09d5636 runtime regressions, T44388 0f0ec37 sources.
- Phases0–2,5–6 complete; T380 login complete0a3e206. T379 exact route split complete but full parent gate pending. Main846lines; root backend231PASS0skip/livePASS T44395.
