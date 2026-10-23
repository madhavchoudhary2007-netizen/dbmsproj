# CURRENT_STATE
updated_at: 2026-10-23
git_head: 8969b47
branch: overhaul/neo-brutal
architect_sha256: 9010959b1dacd9fc6b7d9af9afb9ee57fcd7a4753ea9557e397c90ca6982e1a0
harness: codex; orchestrator gpt-6.1-sol/medium; custom workers gpt-6-luna/high
archetype: Neo-Brutal Motorsport (light), ADR-007 approved
last_eval_score: no verified overhaul score; historical100 omits new gates

## Phase and verified facts
- Phase0 complete T-300e465e89/T-30113e6100/T-30259a180e; owner approved in chat, ADR007 activated and lock9010959b/boot0. Codex harness/profile and cap verified; owner Claude433000 settings preserved.
- Phase1 T-311 accepted8570e58: backend-tests Ruff and strict frontend lint0; scripts/eval Ruff separately0. T-310 OPEN: only main.py remaining, 3 C901 findings remaining (simulation_loop16, control_simulation24, dbms_lock_demo16). All other backend files Ruff+format0.
- T-44110 acceptedfd42784: explicit existing exception suppression preserves classes/order; health degraded contract retained, pit409 cause explicit, UP034 cleaned, non-security lock-demo RNG narrowly justified. After T-44111/T-44113 only3 C901 findings remain; full gate PASS136,0 skips and live flows PASS; no leaked listener.
- Main and demo entire formatting completeT-4410119620dd; test_api full formatting/E501 completeT-44106c6e5749. All formatting/literal children verified exact AST/SQL/unchanged directives (or canonical content), <=150 changed lines each.
- T-44108a893c67 uses UTC alias: normalized AST proves no other change,2 focused simulation tests passed. T-44109d9258cb extracts2Cursor fixture factories: exact class/assertion AST/counts preserved,3 focused tests pass; test_api full Ruff/format0.
- T-441072429939 demo/config Ruff+format0; non-import AST and parsed TOML identical. Public local-only fallback and JWT guard values unchanged, no secret values printed. Narrow seeded-RNG/S105 reasons only, no global rule change.
- CRUD safe identifiers T-458fe83d11 and reusable guards T-4482a20f2a0 accepted. Main dependencies T-453301a40c and UTC/local modernisation accepted. OpenAPI SHA remains60d831ab5cc96051d2fa2caa9b4a2f25d89a6444c05c2a5ceed0aaf8c660346b, last checked afterT-44110.
- Full isolated backend/live gates repeatedly pass136 tests,0failed/skipped/xfailed. All login/session/simulation/Mongo/WS/pit/trigger/results/standings/DBMS/generated-race flows PASS. Latest completed afterT-4482 includes CRUD guards, T-44110 rerun136PASS plus live flows PASS.
- Verifier cleanup defect fixedT-44804a3ab7f: exec makes API_PID actual API, cleanup waits it. Two subsequent full runs leave no18000listener(exit1). Prior orphan lease failures104pass/32failed were disposable API children, not product assertions; no real DB touched.
- Frontend lint/typecheck and existing spacing/banned/motion0. Neo lint NOT_RUN untilT-360; FPS17.0ms must tighten to16.7 atT-413; no performance/overhaul score claimed.
- Fresh strict mypy baseline222 in14/31files (main171); T-312 follows T-310. Prior audit7high2moderate unrefreshed. T-313CI thenT-314F7/F8/F9 scorer follow graph.
- Rejected cap overruns T-449188,T-448152,T-44110212 were reverted in clones and scope split repairs passed. T-44110 SIM117 merges deferredT-44112. T-460 static3checks misreported as tests corrected to0; T-4490 expanded initial28lines to140 for efficiency.

## Execution and contracts
- Only overhaul/neo-brutal, no merges/history rewrites. Only accept.sh commits. Preserve all routes/features/copy/hooks/aria/stateclasses/hash routes. API additions need own ADR and owner approval; no existing shape/path changes.
- No .env/secrets/recursive removal or real DB/schema/volume writes; testing only disposable apexgrid-test(postgres15432/Mongo27018). Preserve owner status.sh paths/exclusions and run-loop.sh edits.
- At most2 workers, fresh packet-only custom roles. <=3 files/150 changed lines. Isolated shared clones same branch under ignored .agent/workspaces, shared dependency symlinks, no commits. Review/apply patches sequentially thenaccept.sh; update state each acceptance.
- .agent/check-format-progress.py verifies partial format AST+canonical-content equivalence, strict decrease of distance to Ruff canonical formatting,<=150 lines. Parent full zero-error/format gates remain required. This handles large files without weakening assertions.
- Root scripts/agent/lock.sh auto-commits; canonical lock banner reproduced without Git tail then verify-lock/accept only. Script preserved.

## Deferred gaps
- T-325 is test-only W3 despite plan W2 label. Oversized plan rows split into bounded packets.

## Orchestrator direct edits
- Requested two model-profile lines; architecture/ADR/state/packet/envelope/orchestration helper only. No authored frontend/backend product lines. Patch integration is worker output, not bulk source authorship.


























- T-311 accepted8570e58: Full backend-test and strict frontend lint milestone passes without source changes. Verify exit0; 0 changed lines.



- T-44112 accepted518b4b4: Merged two lock-demo context pairs; normalized With AST and ordering identical. Verify exit0; 138 changed lines.

- T-44111 acceptedb069dab: Composed CRUD and session action SQL with psycopg.sql; used static action SET fragments and reused CRUD 404 checks while preserving action flow. Verify exit0; 62 changed lines.

- T-44111 worker envelope counts27/23 corrected from git numstat35/27 before acceptance; actual62lines in scope, verify0. Full isolated rerun PASS136,0 skips, all live flows PASS; no18000listener.

- T-44113 accepted11595ad: Extracted the principal team authorization guard into one helper called by both reservation handlers. Verify exit0; 17 changed lines.

- T-44113 principal guard inlining proves whole AST equivalent; API SHA unchanged. Latest full gate T-44111.full.raw.log136PASS +all live flowsPASS.

- T-440 accepted5248d21: catalogue now respects48px display/100–300ms; long repeating motion replaced by static ongoing content and event-triggered200ms. Doc-only15lines, no gate changes; existing architecture already requires these limits.

- T-44114 accepted8969b47: Inlined driver selection and validation into _start_session_simulation, leaving only the start operation extraction. Verify exit0; 108 changed lines.
