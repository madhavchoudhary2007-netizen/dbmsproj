# CURRENT_STATE
updated_at: 2026-10-23
git_head: 1f55cb6
branch: overhaul/neo-brutal
architect_sha256: 9010959b1dacd9fc6b7d9af9afb9ee57fcd7a4753ea9557e397c90ca6982e1a0
harness: codex; orchestrator gpt-6.1-sol/medium; custom workers gpt-6-luna/high
archetype: Neo-Brutal Motorsport (light), ADR-007 approved
last_eval_score: no verified overhaul score; historical100 omits new gates

## Phase and verified facts
- Phase0 complete T-300e465e89/T-30113e6100/T-30259a180e; owner "ok approved continue"/"dont stop you have all permissions". ADR007 activation locked9010959b; boot/lock0. Caller-default harness and actual Codex ORCH_MODEL set; worker bindings/cap unchanged; owner Claude433000 settings preserved.
- Phase1 T-310/T-311 remain OPEN until full Ruff/format gates0; atomic child successes never count as parent pass. T-312 typing/T-313CI thenT-314 scorer follow per dependency graph.
- Latest complete Ruff baseline330(main213,test_api98,demo15,config4), before T-4482/4483. Initial542/format25files/frontend2any. Fresh mypy222 in14files/31checked. Audit7high2moderate remains prior documented until rerun.
- Database tests entire file Ruff+format0, AST unchanged, acceptedT-46012e8ea1 after bounded formatting packets.
- Routers/bootstrap/schemas/CRUD/telemetry/pit/archive scoped Ruff+format0. T-458fe83d11 safely quotes SQL identifiers with psycopg composables and bound values; precise count_documents Protocol. Telemetry/archive formatting AST identical.
- T-453301a40c main dependency bindings; T-45772973d1 UTC/annotations/local/zip modernisation; T-4595601bbd bootstrap format; T-4482a20f2a0 reusable payload+record guards C901<=10. Entire OpenAPI remains identical SHA60d831ab5cc96051d2fa2caa9b4a2f25d89a6444c05c2a5ceed0aaf8c660346b, last checked afterT-4482.
- T-44812cf7b01 demo deletion guard formatting/literals: entire AST+SQL content unchanged. T-4483bfad8d0 narrow seeded RNG/JWT validation fixture lint exceptions, unchanged AST; pyproject comments document reasons, no rule/threshold relaxation.
- Frontend lint/typecheck0 after T-4436cca3aa (two explicit-any replacements); spacing/banned/motion0. Neo lint NOT_RUN untilT-360. Existing FPS17.0ms must tighten to16.7 atT-413; no performance pass claimed.
- Full disposable backend/live gates repeatedly pass136tests,0 failed/skipped/xfailed; login/session/simulation/Mongo/WS/pits/trigger/results/standings/DBMS/generated races PASS. Latest afterT-458/T-4480: .agent/results/T-4480-T-458.retry.full.raw.log exit0.
- T-44804a3ab7f fixes verifier API launch with exec, so cleanup waits actual API PID. After full gate, listener18000 check exit1 confirms none. Previous T-442/T-458 lease failures104passed/32failed came from orphaned disposable API children (ports15432/27018/18000 only, PPID1), not product assertions. PID79496 gracefully terminated; PID11698 self-exited before TERM attempt.
- T-4482 full disposable gate exit0:136passed,0skips, all live acceptance PASS; no API listener afterward (exit1). Repeated-run cleanup defect resolved. Formatting continues in isolated clones.
- T-449 initial formatter188>150 and T-448 initial152>150 rejected/reverted; each repair narrowed scope and passed, parent gates unchanged. T-460 reported3 static checks as tests; corrected to0 collected tests before saving.

## Execution and contracts
- Only overhaul/neo-brutal, no merges/history rewrites. Only accept.sh commits. Preserve all routes/features/copy/hooks/aria/stateclasses/hash routes. API additions need own ADR and owner approval; no existing shape/path changes.
- No .env/secrets/recursive removal or real DB/schema/volume writes; testing only disposable apexgrid-test(postgres15432/Mongo27018). Preserve owner status.sh paths/exclusions and run-loop.sh edits.
- At most2 workers, fresh packet-only custom roles. <=3 files/150 changed lines. Isolated shared clones same branch under ignored .agent/workspaces, shared dependency symlinks, no commits. Review/apply patches sequentially thenaccept.sh; update state each acceptance.
- .agent/check-format-progress.py verifies partial format AST+canonical-content equivalence, strict decrease of distance to Ruff canonical formatting,<=150 lines. Parent full zero-error/format gates remain required. This handles large files without weakening assertions.
- Root scripts/agent/lock.sh auto-commits; canonical lock banner reproduced without Git tail then verify-lock/accept only. Script preserved.

## Deferred gaps
- T-440 before motion: align plan2.3 display min40 vs leading>=48 and2.7 durations with hard100–300ms.
- T-441 before palette: real heading contrast<=1 currently filtered; regression must retain4.5 threshold and omit only decorative aria-hidden duplicates. Bands50–70/20–40/5–15 unchanged.
- T-325 is test-only W3 despite plan W2 label. Oversized plan rows split into bounded packets.

## Orchestrator direct edits
- Requested two model-profile lines; architecture/ADR/state/packet/envelope/orchestration helper only. No authored frontend/backend product lines. Patch integration is worker output, not bulk source authorship.

- T-4484 accepted2cc09da: Advanced145 lines of canonical main formatting with identical AST and canonical contents. Verify exit0; 145 changed lines.

- T-4485 acceptede2d86a7: Advanced141 lines of canonical API-test formatting with identical AST and canonical contents. Verify exit0; 141 changed lines.

- T-4486 accepteda141bc4: Advanced147 lines of canonical main formatting with identical AST and canonical contents. Verify exit0; 147 changed lines.

- T-4487 acceptedb5afb5a: Advanced148 lines of canonical API-test formatting with identical AST and canonical contents. Verify exit0; 148 changed lines.

- T-4488 accepted918245b: Advanced144 lines of canonical main formatting with identical AST and canonical contents. Verify exit0; 144 changed lines.

- T-4489 acceptedab5592b: Advanced141 lines of canonical main formatting with identical AST and canonical contents. Verify exit0; 141 changed lines.

- T-4490 accepted1f55cb6: Advanced140 lines of canonical API-test formatting with identical AST and canonical contents. Verify exit0; 140 changed lines.
