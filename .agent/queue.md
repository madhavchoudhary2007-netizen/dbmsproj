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
