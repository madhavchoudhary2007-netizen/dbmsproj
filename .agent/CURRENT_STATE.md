# CURRENT_STATE
updated_at: 2026-10-23
git_head: 4a3ab7f
branch: overhaul/neo-brutal
architect_sha256: 9010959b1dacd9fc6b7d9af9afb9ee57fcd7a4753ea9557e397c90ca6982e1a0
harness: codex; orchestrator gpt-6.1-sol/medium; custom workers gpt-6-luna/high
archetype: Neo-Brutal Motorsport (light), ADR-007 approved
last_eval_score: no verified overhaul score; historical100 excludes new gates

## Active work and verified facts
- Phase0 complete T-300e465e89/T-30113e6100/T-30259a180e. Owner approved in chat "ok approved continue"/"dont stop you have all permissions". Architecture activation locked9010959b; boot/verify-lock0.
- H=codex; caller-default HARNESS and correct Codex ORCH_MODEL set. Worker profiles/efforts/cap/context preserved. Owner Claude433000 configuration preserved.
- T-4427bdbf4c bootstrap/schemas Ruff+format0; T-4436cca3aa perf-fps real optional-memory type and bundle formatter, frontend lint/typecheck0; spacing/banned/motion0.
- T-44487025ef analytics/auth/pit routers; T-446c9ab8a1 user/membership/telemetry routers: Ruff+format0 and identical OpenAPI SHA60d831ab5cc96051d2fa2caa9b4a2f25d89a6444c05c2a5ceed0aaf8c660346b. Offline import requires APP_ENV=local; missing deployed JWT_SECRET correctly refuses.
- T-4452c4ffd3:SQL exception checks narrowed to driver DatabaseError, strict zips and UTC; no weakened assertions.
- T-4479731af5 database range1-180 formatting30lines; T-449c728e2a range200-300 formatting98lines: exact whole-file AST unchanged.
- T-451dc1a36f test_api import sorting/unused tick rename34lines; selected lint0.
- Full disposable gate after T-442, after T-444/445 and after T-446/447: exit0,136 tests passed,0 failed/skipped/xfailed; live login/session/simulator/Mongo/WebSocket/pit/trigger/results/standings/DBMS/generated-race acceptance PASS. Logs .agent/results/*full.raw.log.
- Initial T-442 gate104passed/32failures had orphaned PID79496 holding runtime lease. lsof confirmed test ports15432/27018/18000 only, PPID1; graceful termination fixed rerun. No real database touched.
- T-449 initial range200-400 exceeded150lines(188); clone reverted, repair200-300 accepted, full parent gate unchanged.
- T-448 initial152lines exceeded150 despite scoped lint0. Clone reverted; repair now pit_repository+race_archive only, telemetry deferred. Last stale envelope repeated initial failure; fresh repair requested.
- T-459 W2 and T-460 W3 are current independent packets; at most2 workers. Full parent T-310/T-311 gates remain OPEN, scoped children never presented as parent passes.

## Contracts and guardrails
- Branch overhaul/neo-brutal only; preserve every feature/route/copy/hook/aria/state class/DBMS hash. API change needs its ADR/owner approval; no destructive operations/real DB data/schema writes, .env/secrets, recursive removal or gate weakening.
- Database testing only disposable apexgrid-test, postgres15432/Mongo27018. Never real volumes.
- Only accept.sh commits. Workers use isolated local shared clones on same branch under ignored .agent/workspaces; no commits; dependency symlinks. Review/apply bounded patches sequentially to avoid accept.sh git-add-all boundary collisions. State updated after each acceptance.
- Owner scripts/agent/status.sh, root status.sh and run-loop.sh edits preserved/excluded.
- <=3 files/150 changed lines per packet; no bulk product code by orchestrator.

## Open risks and next milestones
- Initial Ruff542(540backend+2tool),format25files,frontend2any; latest count before T-448/451:494(app335/tests159). Mypy222/audit7high2moderate remain prior documented inputs until rerun.
- T-310/T-311 full zero gates required before T-312 strict types/T-313CI, thenT-314 real F7Ruff/F8mypy/F9audit score and hardF2.
- Neo-brutal lint NOT_RUN untilT-360. Existing FPS spec17.0ms must tighten to owner16.7 inT-413. No performance pass claimed.
- T-440 before motion: plan2.3 display minimum40 vs leading>=48;2.7 durations exceed hard100–300. Align specs before implementation.
- T-441 before palette: regression for real headings contrast<=1 currently excluded; preserve4.5 gate, exclude only decorative aria-hidden duplicates. Bands50–70/20–40/5–15 unchanged.
- Parent tasks over150lines split into boundedT44x packets. T-325 test-only work is W3 despite plan label.
- lock.sh directly commits, incompatible with accept-only Git: reproduced canonical banner without Git tail, verify-lock0, then accepted; script unchanged.

## Orchestrator direct edits
- T-300 requested two model profile lines; otherwise architecture/ADR/state/packets/envelopes and patch integration only. Zero authored frontend/backend product lines.
- T-448 repair accepted4d16cea:130 changed lines in pit/archive; exact AST unchanged, full scoped Ruff/format0. Deterministic RNG has one justified S311 inline suppression.
- T-452 accepted8504aea:40 test-format lines, exact AST unchanged, range400-480 green. No additional DB rerun needed for AST-identical formatting; next behavior-affecting batch reruns full suite.
- T-454 accepted0df18c1:82 test-format lines, exact AST preserved. T-453 OpenAPI comparison unchanged60d831ab; full gate follows integration.
- T-453 accepted301a40c:95 dependency-default lines, B0080/OpenAPI unchanged. Full disposable gate running in T-453.full.raw.log.
- T-457 accepted72973d1:43 main lines, UTC/annotation/local/semicolon modernisation, explicit shortest zip. Selected lint0/OpenAPI unchanged. Fresh strict mypy remains222 errors in14files/31checked beforeT-312.
- T-455 acceptedc457b0d:97 test-format lines, exact whole-file AST, middle format0.
- T-453 full disposable rerun exit0:136 passed,0 failed/skipped/xfailed; all live acceptance flows PASS.
- T-456 accepted6f866cc:132 test-format lines, full database-test format0 and exact AST unchanged; full lint still has long literal debt.
- T-458 acceptedfe83d11:72 lines, CRUD identifiers now psycopg composables with bound values, precise count protocol; telemetry AST unchanged. Scoped lint/format0; full disposable gate running.
- T-460 envelope initially counted3 static checks as tests; corrected metadata to0 tests (no pytest collected), preserving actual verification command/status. No test pass fabricated.
- T-460 accepted12e8ea1:database tests full Ruff/format0 and exact AST preserved,68lines. T-458 full gate failed104passed/32failed: orphan11698 held test runtime lease. PPID1 and lsof confirmed ONLY test15432/27018/18000. Graceful termination authorized; script kills subshell instead of child. New T-4480 addresses cleanup without gate changes.
- T-459 accepted5601bbd:46 main format lines, exact AST unchanged. Orphan11698 had already exited when TERM was attempted (no such process); no process was killed by that command. Cleanup must wait on actual API PID before next run.

- T-4480 accepted4a3ab7f: Exec the API process so verifier cleanup waits for its shutdown. Verify exit0; 2 changed lines.
