# NEXT_STATE
updated_at: 2026-10-22T12:00:00Z
loop_iteration: 1 of 5

## Queue (top-down; <=3 target files and <=150 changed lines per task)
### T-015 — G13 simulation boundary extraction
- worker: W2 | priority: P1 | after: T-012
- target_files: backend/app/main.py, backend/app/simulation_core.py
- contract: behavior-preserving <=150-line extraction; no route/schema change
- verify: .venv/bin/pytest -q backend/tests/test_api.py -k simulation
### T-017 — G08 spacing tokens
- worker: W1 | priority: P2 | after: T-010
- target_files: frontend/app/globals.css, frontend/tailwind.config.ts
- contract: add spacing scale in <=150 lines
- verify: npm --prefix frontend run build
### T-018 — G10 typography
- worker: W1 | priority: P2 | after: T-017
- target_files: frontend/app/globals.css, frontend/tailwind.config.ts
- contract: accessible sans/mono hierarchy
- verify: npm --prefix frontend run build
### T-019 — G16 runtime parity
- worker: W3 | priority: P2 | runtime versions verified; container source gates require builder stage
- target_files: scripts/eval/runtime-parity.sh
- contract: compare host/container Node and Python; run container gates
- verify: bash scripts/eval/runtime-parity.sh
## Blocked
- Historical browser matrix passed 715/715 before cookie migration; current full run stopped at 10 stale responsive login fixtures after 269 passes. Backend runtime audit clean. Frontend dev dependency audit and quality debt remain.
- T-006: twice FAILED. Initial packet omitted `special-pages.tsx`; retry asserted empty/partial states without a screen-specific filter/list contract. No test accepted; requires a route-specific applicability matrix before new work.
- T-026/T-027/T-028: depend on blocked T-006 state matrix.
- T-019: frontend runner lacks source; test in builder stage.
- T-014: split into ADR-002 backend/frontend/browser/acceptance packets T-050..055; implementation follows reproducing tests.

## Done this iteration (pruned on compaction)
- T-088 ✓ 73de4fd; archive provisional label, full browser 775/775, typecheck pass.
- T-001..T-086: accepted history and evidence in git/LOOP.md; latest T-086 648ddad archive API fix.
- T-087 ✓ 710e0cf; strict desktop/mobile archive UI xfails reproduced; ordinary views pass.
