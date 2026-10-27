# CURRENT_STATE
updated_at: 2026-10-27
branch: overhaul/neo-brutal
execution: RUNNING; implementing docs/completion-plan.md with Codex Luna workers
verified_product_head: aa1dc05 (T-44662 live/steward browser tests)
reviewed_repository_head: b22bec8
metadata_task: T-44644 ADR-017 and evidence checkpoint accepted bd8fd2; unrelated T-411 work remains untouched
architect_sha256: 0f2b5366fee89ec70d8340ab2e148ad676f0c64bf324f00af559c242cd4cc46c
target_harness: Antigravity Gemini3.8Flash HIGH orchestrator / LOW workers; max2
observed_antigravity_binding: prior state claimed active Flash workers; not observable in this Codex planning session
last_eval_score: no current overhaul score; old51.2974 is obsolete

## Current evidence (2026-10-27 audit)
- Typecheck and zero-warning frontend lint pass; backend Ruff check/format pass (128files); strict mypy passes91app sources; all4design lints pass.
- Offline focused backend:84passed (snapshot, replay, migrations, showcase). This does not prove live SQL behavior or domain integration.
- Audit and prior scoped evidence: .agent/audit/completion-review-2026-10-27.md; accepted work through T-410 in git. Historical results are not current release proof.
- Boot/lock pass; earlier import isolation failures fixed by T-44652/54/55/57/59.

- T-44618 accepted a100c9c: 25 authorization/CSRF cases pass with offline fixtures; T-44619 accepted dd11de9: audit/views/gaps empty and error cases pass; T-44620 accepted c71203f: refresh error/success checks pass; T-44617 accepted 15a21dd (31 passed); T-44635 accepted dded0ba (60 passed, original assertions retained); OpenAPI snapshot9 passed, strict showcase mypy passed.

- T-44626 accepted a001d83; a read-only query on verified disposable PostgreSQL returned correct tie, gap and rolling-lap values. Combined isolated suite 94 passed and strict mypy passed; T-44625 tests accepted 0acf6b2; T-44637 fixture updates accepted 65f8069; isolated suite 94 passed.

- T-44624 accepted 23f6a9c: offline 9 passed; guarded disposable PostgreSQL integration 8 passed, including independent PIDs and real SQLSTATE 40P01. Demo circuit rows remaining: 0. First integration attempt lacked PYTHONPATH (4 errors); corrected run passed. T-44623 accepted 013c3ef; legacy fixtures accepted 47fd11c, combined suite 94 passed.

- T-44639 accepted ebee956: authenticated actor set with transaction-local parameterized SQL for both steward handlers; rollback-only trigger proof passed; T-44646 accepted d64cdc2 and T-44645 tests accepted 0594502: both steward handlers bind validated role and actor; real endpoint/trigger proof pending. T-44628 accepted 2f3294c: security metadata returns actual rows or errors; T-44627 regression accepted 78d4c9b. A rollback-only disposable trigger probe produced exactly one audit row with the synthetic actor.

- Confirmed P0 RLS gap: on disposable apexgrid-test with restricted apexgrid_app and steward context, own probe rows for both championships and penalties were visible; plan requires penalties only. Probe rolled back. ADR-017 accepted bd8fd2; migration 009 accepted 89a10ac. T-44642 regression accepted 93b7791; disposable integration 7 passed with rollback and two replays; direct restricted-role steward/admin/unknown read and steward write checks passed. Not deployed to any database.

- T-44641 accepted 81d7819: offline EXPLAIN error/empty/success tests9 passed; no fabricated plan on error. T-44640 regression accepted 2bfcbb1; real EXPLAIN proof pending.

- T-44630: three explicit browser modes collect 1415 app, 60 guide and 8 real-stack tests; guide mobile 12 passed; T-44631 accepted 2f4e25c and mobile accessibility 17 passed on production build. Unmocked mode requires isolated loopback URL and rebuilds with it; real-stack journeys remain pending.

- T-44650 owned lifecycle accepted 0ace81a; root ran acceptance in newly created marked disposable PostgreSQL/Mongo databases, exited 0, and verified zero owned databases remained. T-44649 lifecycle tests accepted a263597, T-44648 script a45939b and T-44647 tests d6078a2; existing assertions retained and immutable trigger untouched.
- T-44652 accepted 9cf5440: mixed-import auth verification 42 passed; wider auth checks 56 passed. Real-stack browser run's result was lost during session recovery and must be rerun; its port listeners are gone.
- T-44654 accepted a8a4221; 116 focused checks passed.
- T-44654 introduced a startup regression in backend cwd; T-44655 accepted 4d234b1, proving startup import and 95 focused cases. Owned browser run stopped during bootstrap and needs rerun.
- Backend after T-44664: 478 passed, zero skips; coverage 76.88% vs required 80%. T-44651: 20 browser journeys passed plus 2 corrected standings tests. T-44662: timing updates and steward approval/recalculation passed on desktop/mobile (4 tests); owned databases cleaned. One concurrent standings call returned 409; likely race unproven.
- Backend diagnosis: duplicate app.main modules caused stale globals and pool sharing. T-44656 tests accepted a636737; T-44657 fix accepted b0ad626, with 118 focused checks and startup/Ruff passing. Browser failures include stale selectors, unresolved WebSocket connection and standings 409.
- Showcase route identity regression: T-44658 tests accepted b65d527; T-44659 fix accepted 0eb4a10. 118 focused tests and startup/Ruff pass; full gate pending.
- T-44660/61/63/64 accepted: 9 Mongo, 6 SQL, 14 pit and 11 steward checks pass; coverage gate not rerun yet.

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
- T-44630 config accepted be9002a; real-stack spec accepted T-44651. Preserve untracked owner packet .agent/packets/T-411.md.
- Acceptance isolation and seed-default fixes accepted T-44615/16/21/22; preserve unrelated T-411 work.
- T-021 fixture depends on existing championship round3; show owned-fixture/cleanup plan before dispatch. Official penalty immutability complicates cleanup; solve with safe disposable isolation, never production data changes.
- RLS default-owner bypass is not itself proof of an unauthorized schema change; test actual restricted-role behavior. Missing analytics relation must not be hidden by fake rows.
- Standings prior-rank source remains absent; do not fabricate deltas. Host Python3.14/Node26 differs from Docker3.12/22; record parity explicitly.
- T-44616 worker line-count envelope differed from git numstat (actual +140/-14); code and independent tests reviewed. No orchestrator product edits or real DB data changes.

## Execution authority
Remaining-work order: docs/completion-plan.md; scope/design: docs/overhaul-plan.md; cadence: delivery-workflow.md; score: evaluation.md. Short ready queue: NEXT_STATE. Keep preserved features/API shapes/assertions and data protections. Only focused packet checks, relevant root integration, domain close and full final candidate checks; no arbitrary three-second limit or duplicate full pytest for coverage.
