# NEXT_STATE
updated_at: 2026-10-27
branch: overhaul/neo-brutal
execution: RUNNING; implementing completion plan
phase: reopen audited security/DBMS gaps, then complete9–11
plan: docs/completion-plan.md (all tasks, exact acceptance outcomes and verification families)

## First actions
Accepted: T-44614..22, T-44623..28 T-44635..39; see Git.; see Git and CURRENT_STATE.
Reconcile live T-411 owner and preserve its dirty config/spec/packet; hashes in audit. Scoped acceptance is fixed; preserve the unrelated browser draft. Every implementation packet needs literal offline Verify, exact paths/types and root-owned integration. Family names below are planning references, not executable packet commands.

### T-44636 — Showcase decision and evidence checkpoint
- worker: O | priority: P1
- target_files: .agent/adr/ADR-010-dbms-showcase-routes.md, .agent/CURRENT_STATE.md, .agent/NEXT_STATE.md, docs/completion-plan.md, .agent/packets/T-44636.md, .agent/results/T-44636.json, .agent/packets/T-44617.md, .agent/results/T-44617.json, .agent/packets/T-44618.md, .agent/results/T-44618.json, .agent/packets/T-44619.md, .agent/results/T-44619.json, .agent/packets/T-44620.md, .agent/results/T-44620.json, .agent/packets/T-44635.md, .agent/results/T-44635.json
- verify: bash scripts/agent/verify-lock.sh && bash scripts/agent/budget.sh && git diff --check -- .agent/CURRENT_STATE.md .agent/NEXT_STATE.md docs/completion-plan.md
### T-44627 — Audit and RLS regressions
- worker: W3 | priority: P1 | after:ADR-010
- target_files: backend/tests/test_showcase_audit.py
- verify: .venv/bin/pytest -q -p no:cacheprovider backend/tests/test_showcase_audit.py
### T-44644 — ADR and evidence checkpoint
- worker: O | priority: P0
- target_files: .agent/adr/ADR-017-audit-rls-scope.md, .agent/CURRENT_STATE.md, .agent/NEXT_STATE.md, docs/completion-plan.md, .agent/packets/T-44644.md, .agent/results/T-44644.json, .agent/packets/T-44623.md, .agent/results/T-44623.json, .agent/packets/T-44624.md, .agent/results/T-44624.json, .agent/packets/T-44625.md, .agent/results/T-44625.json, .agent/packets/T-44626.md, .agent/results/T-44626.json, .agent/packets/T-44627.md, .agent/results/T-44627.json, .agent/packets/T-44628.md, .agent/results/T-44628.json, .agent/packets/T-44637.md, .agent/results/T-44637.json, .agent/packets/T-44638.md, .agent/results/T-44638.json, .agent/packets/T-44639.md, .agent/results/T-44639.json, .agent/packets/T-44640.md, .agent/results/T-44640.json, .agent/packets/T-44641.md, .agent/results/T-44641.json
- verify: bash scripts/agent/verify-lock.sh && bash scripts/agent/budget.sh && git diff --check -- .agent/CURRENT_STATE.md .agent/NEXT_STATE.md docs/completion-plan.md
### T-44640 — EXPLAIN truth regression
- worker: W3 | priority: P0 | state: ACCEPTED 2bfcbb1
- target_files: backend/tests/test_showcase_explain_truth.py
- verify: .venv/bin/pytest -q -p no:cacheprovider backend/tests/test_showcase_explain_truth.py
### T-44641 — Honest EXPLAIN results
- worker: W2 | priority: P0 | state: ACCEPTED 81d7819 | after:44640
- target_files: backend/app/api/dbms_showcase.py
- verify: .venv/bin/pytest -q -p no:cacheprovider backend/tests/test_showcase_explain_truth.py && .venv/bin/ruff check backend/app/api/dbms_showcase.py
### T-44642 — Restricted-role regression
- worker: W3 | priority: P0
- target_files: backend/tests/test_showcase_rls.py
- verify: .venv/bin/pytest -q -p no:cacheprovider backend/tests/test_showcase_rls.py -k fixture_guard
### T-44643 — Restricted-role policy migration
- worker: W2 | priority: P0 | after:44642 and ADR-017
- target_files: backend/migrations/009_audit_rls_scope.sql
- verify: .venv/bin/pytest -q -p no:cacheprovider backend/tests/test_showcase_rls.py -k fixture_guard
### T-44630 — Browser project/environment repair
- worker: W3 | priority: P1 | after:44616 and T-411 ownership handoff
- target_files: frontend/playwright.config.ts, frontend/e2e/runtime/playwright-selection.test.mjs
- verify: BROWSER-SELECTION; root runs guide/browser evidence, no dropped tests.

## Remaining/deferred, retained in the full plan
T-44625..29 real analytics/audit/RLS + backend domain close;44631 redirect/axe; T-021 fixtures; T-411 full real journeys;412visual/413motion/414matrix/415coverage;44632 runner dedup;44633 locked images;420CI/421docs/431cleanup/430score/432PR. No accepted domain restart. Standings delta remains unfabricated; no test, threshold or real-data waiver.
