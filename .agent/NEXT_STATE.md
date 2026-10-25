# NEXT_STATE
updated_at: 2026-10-25
phase: 3 T331 + 7 route redesign; Phases0–2,5–6 COMPLETE; no current score

## Queue
### T-44479 W3 — OPEN
- target_files: frontend/e2e/resource-memberships.spec.ts
- contract: Repair membership partial-state test locators while retaining strict cause and mutation assertions.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && cd frontend && ./node_modules/.bin/playwright test e2e/resource-memberships.spec.ts --list

### T-44478 W1 — OPEN
- target_files: frontend/app/styles/resources.css
- contract: Repair serious membership roster contrast and tiny legacy type at all widths.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-neobrutal.sh

### T-44477 W2 — OPEN
- target_files: backend/app/core/simulation_tick.py, backend/app/core/validation.py, backend/app/crud_repository.py
- contract: T339 complete strict types for simulation ticks and CRUD validation boundaries.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_simulation_replay.py backend/tests/test_telemetry_ordering.py backend/tests/test_telemetry_ingest_contract.py backend/tests/test_contract_snapshot.py && .venv/bin/mypy --strict --follow-imports=silent backend/app/core/simulation_tick.py backend/app/core/validation.py backend/app/crud_repository.py && .venv/bin/ruff check backend/app backend/tests && .venv/bin/ruff format --check backend/app/core/simulation_tick.py backend/app/core/validation.py backend/app/crud_repository.py

### T-44476 W1 — OPEN
- target_files: frontend/components/pages/live/demo-controls.tsx, frontend/components/pages/live/delete-demo-modal.tsx, frontend/components/pages/live/index.tsx
- contract: T383 restyle live-demo hero and native delete confirmation with one active primary.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-neobrutal.sh

## Blocked
- T379 parent final gate: exact split complete, build/static0 and1020/1100mockedPASS; remaining15desktopA3layouts requirePhase7. Body/reducedmotion repaired; never mark fullsuitepassed. Proceed Phase7layouttasks as parentgate repairs, retain fullgate for finalrerun.

## Deferred
- TASTE-382-BLOAT: resource-page.tsx >300lines; split genuine reusable presentation/runtime responsibilities after T382 flow coverage, no single-call fake wrappers.

- TASTE-381-1: four KPIface accents followT381 but exceedT400 max3; consolidate supportingcolourbeforeA5, preserve data/features and thresholds.
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44475 acceptedbc67c9a; verify0.
- T-44474 acceptedda4d3ee; verify0.
- T-44473 accepteddcbb14e; verify0.
- T-44472 acceptedb5df2f8; verify0.
- T-44471 accepted2c7283c; verify0.
- T-44469 accepteddc0ff28; verify0.
- T-44470 accepted17b9763; verify0.
- T-44468 acceptedddbf765; verify0.
- T-44467 accepted0308663; verify0.
- T-44466 accepted978192d; verify0.
- T-44465 acceptede1470ec; verify0.
- T-44463 acceptede6311f5; verify0.
- T-44464 accepteded47d9f; verify0.
- T-44462 accepted4019403; verify0.
- T-44461 accepteda939d11; verify0.
- Earlier accepted tasks/hashes/evidence: Git/.agent/results. Parent milestones remain open until full gates.
