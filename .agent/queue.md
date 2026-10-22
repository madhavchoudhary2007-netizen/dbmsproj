# Overflow task queue

## Queue
### T-020 — G18 docs truth gate
- worker: W3 | priority: P2
- target_files: scripts/eval/docs-truth.sh
- contract: flag automated-E2E claims without configured tests
- verify: bash scripts/eval/docs-truth.sh
### T-021 — Acceptance self-owned fixtures
- worker: W3 | priority: P2
- target_files: scripts/acceptance.py
- contract: own named test championship/events, clean up; preserve assertions
- verify: .venv/bin/python scripts/acceptance.py
### T-022 — Spacing lint precision
- worker: W3 | priority: P2
- target_files: scripts/eval/lint-spacing.sh
- contract: ignore border widths, keep spacing checks
- verify: bash scripts/eval/lint-spacing.sh --self-test

### T-023 — TASTE-1 reduce UI module bloat
- worker: W1 | priority: P2 | after: T-005
- target_files: frontend/components/ui.tsx, frontend/components/data-table.tsx
- contract: extract cohesive table presentation so ui.tsx is <=300 lines; preserve exports and behavior
- verify: npm --prefix frontend run typecheck

### T-034 — TASTE-2 reduce special-pages module bloat
- worker: W1 | priority: P2 | after: T-032
- target_files: frontend/components/special-pages.tsx, frontend/components/pit-wall.tsx
- contract: extract cohesive PitWall presentation within 150 changed lines and preserve behavior; continue staged extraction until <=300 lines
- verify: npm --prefix frontend run typecheck

### Phase 3 — ADR-003 full time/grid enforcement proposal
- owner: orchestrator | priority: P2
- contract: write a finding-backed CP defining race elapsed time, starting grid, inherited records, reranking and role journeys before new sanctions are enabled; no historical data rewrite.

### Deferred Phase 4 / cross-gate tasks from NEXT_STATE
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
