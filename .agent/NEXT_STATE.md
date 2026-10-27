# NEXT_STATE
updated_at: 2026-10-27
branch: overhaul/neo-brutal
execution: RUNNING; implementing completion plan
phase: reopen audited security/DBMS gaps, then complete9–11
plan: docs/completion-plan.md (all tasks, exact acceptance outcomes and verification families)

## First actions
Accepted: T-44614/15/16/17/18/19/20/21/22/35; see Git and CURRENT_STATE.
Reconcile live T-411 owner and preserve its dirty config/spec/packet; hashes in audit. Scoped acceptance is fixed; preserve the unrelated browser draft. Every implementation packet needs literal offline Verify, exact paths/types and root-owned integration. Family names below are planning references, not executable packet commands.

### T-44636 — Showcase decision and evidence checkpoint
- worker: O | priority: P1
- target_files: .agent/adr/ADR-010-dbms-showcase-routes.md, .agent/CURRENT_STATE.md, .agent/NEXT_STATE.md, docs/completion-plan.md, .agent/packets/T-44636.md, .agent/results/T-44636.json, .agent/packets/T-44617.md, .agent/results/T-44617.json, .agent/packets/T-44618.md, .agent/results/T-44618.json, .agent/packets/T-44619.md, .agent/results/T-44619.json, .agent/packets/T-44620.md, .agent/results/T-44620.json, .agent/packets/T-44635.md, .agent/results/T-44635.json
- verify: bash scripts/agent/verify-lock.sh && bash scripts/agent/budget.sh && git diff --check -- .agent/CURRENT_STATE.md .agent/NEXT_STATE.md docs/completion-plan.md
### T-44623 — Real concurrency regressions
- worker: W3 | priority: P1 | after:ADR-010
- target_files: backend/tests/test_showcase_concurrency_unit.py, backend/tests/test_showcase_db.py
- verify: CONCURRENCY-UNIT; DB-SHOWCASE is root-only.
### T-44624 — Real isolation/deadlock demos
- worker: W2 | priority: P1 | after:44623
- target_files: backend/app/api/dbms_showcase.py, backend/app/core/showcase_transactions.py
- verify: CONCURRENCY-UNIT + root DB-SHOWCASE with cleanup/timeouts.
### T-44630 — Browser project/environment repair
- worker: W3 | priority: P1 | after:44616 and T-411 ownership handoff
- target_files: frontend/playwright.config.ts, frontend/e2e/runtime/playwright-selection.test.mjs
- verify: BROWSER-SELECTION; root runs guide/browser evidence, no dropped tests.

## Remaining/deferred, retained in the full plan
T-44625..29 real analytics/audit/RLS + backend domain close;44631 redirect/axe; T-021 fixtures; T-411 full real journeys;412visual/413motion/414matrix/415coverage;44632 runner dedup;44633 locked images;420CI/421docs/431cleanup/430score/432PR. No accepted domain restart. Standings delta remains unfabricated; no test, threshold or real-data waiver.
