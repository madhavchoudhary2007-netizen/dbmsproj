# CURRENT_STATE
updated_at: 2026-10-27
branch: overhaul/neo-brutal
execution: RUNNING; implementing docs/completion-plan.md with Codex Luna workers
verified_product_head: 81d7819 (T-44641 EXPLAIN truth; integration pending)
reviewed_repository_head: b22bec8
metadata_task: T-44636 ADR-010 and evidence checkpoint accepted a80bfd2; unrelated T-411 work remains untouched
architect_sha256: 0f2b5366fee89ec70d8340ab2e148ad676f0c64bf324f00af559c242cd4cc46c
target_harness: Antigravity Gemini3.8Flash HIGH orchestrator / LOW workers; max2
observed_antigravity_binding: prior state claimed active Flash workers; not observable in this Codex planning session
last_eval_score: no current overhaul score; old51.2974 is obsolete

## Current evidence (2026-10-27 audit)
- Typecheck and zero-warning frontend lint pass; backend Ruff check/format pass (128files); strict mypy passes91app sources; all4design lints pass.
- Offline focused backend:84passed (snapshot, replay, migrations, showcase). This does not prove live SQL behavior or domain integration.
- Mechanical audit:401project files opened, Python142/JSON4/shell17 syntax checks pass; frontend174/backend140 files reviewed within audit scope. Generated/secret/history files excluded; no line-by-line completeness claim.
- Reproduced without real DB: unauthenticated isolation HTTP200; forced DB failure still returns audit sample1, gaps samples2 and refresh success. Core completion blockers recorded in .agent/audit/completion-review-2026-10-27.md.
- Accepted implementation history through T-44613 and T-410 remains in Git/results. Do not restart router/DI/font/shell tasks. Historical route1475/1475, palette80/80 and bundle max161.53KiB/DBMS154.74KiB are scoped prior claims, not current release proof.
- Last full disposable backend evidence predates recent changes; required zero-skip/full coverage and live acceptance remain pending. Boot/lock pass.

- T-44618 accepted a100c9c: 25 authorization/CSRF cases pass with offline fixtures; T-44619 accepted dd11de9: audit/views/gaps empty and error cases pass; T-44620 accepted c71203f: refresh error/success checks pass; T-44617 accepted 15a21dd (31 passed); T-44635 accepted dded0ba (60 passed, original assertions retained); OpenAPI snapshot9 passed, strict showcase mypy passed.

- T-44626 accepted a001d83; a read-only query on verified disposable PostgreSQL returned correct tie, gap and rolling-lap values. Combined isolated suite 94 passed and strict mypy passed; T-44625 tests accepted 0acf6b2; T-44637 fixture updates accepted 65f8069; isolated suite 94 passed.

- T-44624 accepted 23f6a9c: offline 9 passed; guarded disposable PostgreSQL integration 8 passed, including independent PIDs and real SQLSTATE 40P01. Demo circuit rows remaining: 0. First integration attempt lacked PYTHONPATH (4 errors); corrected run passed. T-44623 accepted 013c3ef; legacy fixtures accepted 47fd11c, combined suite 94 passed.

- T-44639 accepted ebee956: authenticated actor set with transaction-local parameterized SQL for both steward handlers; real trigger proof pending. T-44628 accepted 2f3294c: security metadata returns actual rows or errors; T-44627 regression accepted 78d4c9b. A rollback-only disposable trigger probe produced exactly one audit row with the synthetic actor.

- Confirmed P0 RLS gap: on disposable apexgrid-test with restricted apexgrid_app and steward context, own probe rows for both championships and penalties were visible; plan requires penalties only. Probe rolled back. ADR-017 drafted; candidate 009 replayed twice in one rollback-only disposable transaction, with steward/admin/unknown read and steward write checks passing; migration not accepted or deployed.

- T-44641 accepted 81d7819: offline EXPLAIN error/empty/success tests9 passed; no fabricated plan on error. T-44640 regression accepted 2bfcbb1; real EXPLAIN proof pending.

## Phase truth after audit
| Phase | Status | Needed proof/work |
|---|---|---|
|0 Architecture|ACCEPTED|ADR-010 recorded; reconcile missing proposed009 before points changes|
|1 Baseline|PRIOR_ACCEPTED|Final candidate gates still required|
|2 Security|REOPENED_FINDINGS|New showcase access and nonlocal seeding defects|
|3 Backend|IMPLEMENTED/PARTIAL|Current full integration; lock-install and required CI mypy outcomes|
|4 DBMS showcase|REOPENED|Real SQL demos/provenance, auth, truthful failure, actor/RLS and integration|
|5 Foundation|PRIOR_ACCEPTED|Preserve approved tokens/fonts/primitives|
|6 Shell|PRIOR_ACCEPTED|Preserve shared feed/navigation|
|7 Routes|IMPLEMENTED/PARTIAL|Production journeys, all required states/viewport proof|
|8 Taste/motion|SCOPED_ONLY|T-400 recorded30screenshots; remaining motion/visual proof|
|9 Tests|IN_PROGRESS|T-411..415, primitive production conflict and fixtures|
|10 DevOps/docs|OPEN|CI/audits/Lighthouse/parity and accurate demo docs|
|11 Release|OPEN|Cleanup before current full score>=95/all gates; PR wait|

## In-flight ownership and risks
- Preserve frontend/playwright.config.ts, frontend/e2e/real-stack.spec.ts and .agent/packets/T-411.md; hashes in audit record. Preserve pending files until T-411 ownership is reconciled.
- T-44616 accepted c3d03aa: scoped acceptance reran 10 regression tests; T-44615 regression suite accepted c9adf20; T-44621 seed policy tests accepted 4567fa5; T-44622 nonlocal seed default fixed and accepted d61e1f3 (mocked production bootstrap confirms seed_demo=False and no archive call; disposable integration pending). Preserve unrelated T-411 work.
- T-021 fixture depends on existing championship round3; show owned-fixture/cleanup plan before dispatch. Official penalty immutability complicates cleanup; solve with safe disposable isolation, never production data changes.
- RLS default-owner bypass is not itself proof of an unauthorized schema change; test actual restricted-role behavior. Missing analytics relation must not be hidden by fake rows.
- Standings prior-rank source remains absent; do not fabricate deltas. Host Python3.14/Node26 differs from Docker3.12/22; record parity explicitly.
- T-44616 worker line-count envelope differed from git numstat (actual +140/-14); code and independent tests reviewed. No orchestrator product edits or real DB data changes.

## Execution authority
Remaining-work order: docs/completion-plan.md; scope/design: docs/overhaul-plan.md; cadence: delivery-workflow.md; score: evaluation.md. Short ready queue: NEXT_STATE. Keep preserved features/API shapes/assertions and data protections. Only focused packet checks, relevant root integration, domain close and full final candidate checks; no arbitrary three-second limit or duplicate full pytest for coverage.
