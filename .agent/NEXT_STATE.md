# NEXT_STATE
updated_at: 2026-10-27
branch: overhaul/neo-brutal
execution: RUNNING; implementing completion plan
phase: reopen audited security/DBMS gaps, then complete9–11
plan: docs/completion-plan.md (all tasks, exact acceptance outcomes and verification families)

## First actions
Reconcile live T-411 owner and preserve its dirty config/spec/packet; hashes in audit. Scoped acceptance is fixed; preserve the unrelated browser draft. Every implementation packet needs literal offline Verify, exact paths/types and root-owned integration. Family names below are planning references, not executable packet commands.

### T-44614 — Completion plan / audit truth
- worker: O | priority: P1 | state: CHECKPOINT_IN_PROGRESS
- target_files: docs/completion-plan.md, docs/overhaul-plan.md, .agent/CURRENT_STATE.md, .agent/NEXT_STATE.md, .agent/DOC_AUTHORITY.md, .agent/START_HERE.md, .agent/audit/completion-review-2026-10-27.md, .agent/packets/T-44614.md, .agent/results/T-44614.json, .agent/packets/T-44615.md, .agent/results/T-44615.json, .agent/packets/T-44616.md, .agent/results/T-44616.json, .agent/packets/T-44621.md, .agent/results/T-44621.json, .agent/packets/T-44622.md, .agent/results/T-44622.json
- contract: Planning only; preserve pending product bytes/lock/rubric/scope. Safe commit blocked by unrelated T-411 work until scoped acceptance or owner handoff.
- verify: bash scripts/agent/verify-lock.sh && bash scripts/agent/budget.sh && git diff --check -- .agent/CURRENT_STATE.md .agent/NEXT_STATE.md .agent/DOC_AUTHORITY.md .agent/START_HERE.md docs/overhaul-plan.md
### T-44615 — Acceptance-scope regressions
- worker: W3 | priority: P0 | state: ACCEPTED c9adf20
- target_files: scripts/eval/test_accept_scope.py
- verify: .venv/bin/pytest -q -p no:cacheprovider scripts/eval/test_accept_scope.py
### T-44616 — Safe task-only acceptance
- worker: W2 | priority: P0 | state: ACCEPTED c3d03aa | after:44615
- target_files: scripts/agent/accept.sh
- verify: .venv/bin/pytest -q -p no:cacheprovider scripts/eval/test_accept_scope.py
### T-44617 — Showcase auth/truth regression
- worker: W3 | priority: P0 | after:44616
- target_files: backend/tests/test_showcase_security_truth.py
- verify: .venv/bin/pytest -q -p no:cacheprovider backend/tests/test_showcase_security_truth.py
### T-44618 — Showcase admin access
- worker: W2 | priority: P0 | after:44617
- target_files: backend/app/api/dbms_showcase.py
- verify: SHOWCASE-AUTH + root relevant disposable auth integration.
### T-44619 — Honest database reads
- worker: W2 | priority: P0 | after:44618
- target_files: backend/app/api/dbms_showcase.py
- verify: SHOWCASE-TRUTH + root empty/error/real-row integration.
### T-44620 — Honest refresh outcome
- worker: W2 | priority: P0 | after:44619
- target_files: backend/app/api/dbms_showcase.py
- verify: SHOWCASE-REFRESH + root real refresh/failure proof.
### T-44621 — Seed-policy regression
- worker: W3 | priority: P1 | state: ACCEPTED 4567fa5 | after:44616
- target_files: backend/tests/test_seed_policy.py
- verify: .venv/bin/pytest -q -p no:cacheprovider backend/tests/test_seed_policy.py
### T-44622 — Safe nonlocal seeding
- worker: W2 | priority: P1 | state: ACCEPTED d61e1f3 | after:44621
- target_files: backend/app/config.py, backend/app/bootstrap.py
- verify: .venv/bin/pytest -q -p no:cacheprovider backend/tests/test_seed_policy.py && .venv/bin/ruff check backend/app/config.py
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
