# Antigravity execution contract — Gemini 3.8 Flash

Read once at Antigravity session start and after a harness/model change. This is the active harness contract under ADR-015/016; DOC_AUTHORITY.md lists active versus historical sources. AGENTS.md remains the router; delivery-workflow.md owns cadence; packets.md owns isolation; evaluation.md owns scores. This file does not add a second product plan.

## Model binding and evidence
| Role | Owner-requested model | Thinking | How to verify |
|---|---|---|---|
| Orchestrator | Gemini 3.8 Flash | high | Antigravity model/thinking UI or actual session metadata |
| W1 UI, W2 runtime, W3 QA | Gemini 3.8 Flash | low | Worker UI/session metadata, once per configuration and after any change |
| Concurrent workers | At most 2 | Not a model setting | Orchestrator counts running worker IDs before dispatch |

Markdown and .agent/models.env declare the requested profile; they cannot prove the actual Antigravity UI selection. boot.sh does not attest the running model/thinking. Record requested and observed settings separately. If actual metadata is unavailable, record UNVERIFIED; do not invent an ID or claim a binding passed. If a visible setting differs, correct that role before dispatch; never substitute a model silently. Do not alter Codex/Claude profiles to configure Antigravity. Keep existing supported context settings; do not invent a 12-task or early-compaction trigger.

## Session receipt (record once, no secrets)
Record in CURRENT_STATE or the active packet: harness; requested/observed orchestrator model+thinking and evidence source; requested/observed worker model+thinking; current branch; execution permission; active worker IDs. Expected branch is overhaul/neo-brutal. A current documentation-only user request authorizes documentation only even if another session's product state says RUNNING. Inspect live status before taking over in-flight work; do not run two competing orchestrators on the same tree.

Read START_HERE.md and run the existing boot once as directed there. In the Antigravity shell explicitly export HARNESS=antigravity before sourcing models.env, so a different harness default does not choose the wrong profile. This selects declarations only, not the UI model. Do not bypass boot, read old LOOP history, change branches or reinstall tools merely because the harness changed. Never infer permission from a stale PAUSED/RUNNING sentence in a plan; resolve the latest owner instruction and the current state.

## Dispatch gate — do all before launching a worker
1. Choose one complete domain/user defect and its final boundary. Normal <=3 files/~150 changed lines; justified structural <=8 files/800 lines. These are ceilings, not goals. CRUD and simulator lifecycle are separate domains unless a concrete dependency makes a combined change indivisible; record that dependency. main.py<=120 is a final entrypoint gate, not permission for a giant mixed task.
2. Select the role and disjoint target files. Count running IDs. Prefer W2 backend plus W1 measured A3 route repair, or W2 plus independent W3; launch the second only when ready and independent. Queue conflicting files. Do not invent work to keep two workers busy.
3. Write one packet with exact task ID, target/read paths, inline interfaces, preserved copy/hooks for UI, acceptance criteria, allowed test node IDs/commands, allowed formatter commands and explicit root-owned integration checks. Copy the canonical envelope schema; do not improvise it.
4. Check that the Verify command collects the intended tests offline. It must not silently filter out required snapshot cases, collect zero tests or run DB/browser/network/server checks inside a worker. No arbitrary three-second deadline: test relevance determines scope. A required lease test stays required; the orchestrator runs its DB-backed variant on apexgrid-test.
5. Copy the exact packet into an isolated worker. Do not pass full conversation/state/history. Use low thinking and the requested worker model where the UI supports them. Workers return only the schema JSON and never commit. If isolated workers are unavailable, record the harness limitation; use the owner-authorized serial WORKER MODE/ORCHESTRATOR MODE fallback in roles.md and never describe it as a real parallel worker.

## Worker instruction block (inline in every packet)
- Do only this task; read/edit only the listed paths. Print at most100 lines per file output. Never read .env or secrets.
- Run only Approved Verify and explicitly listed support/format commands. Do not add a broader test file, DB probe, install, server, build or search outside scope. If another command/test/context is needed, return FAILED with the exact need; the orchestrator decides.
- Preserve all interfaces/features/assertions. No test skipping, threshold changes, invented results or unrelated refactors.
- Inspect your target diff. If scope, command or hypothesis changes, stop and report it; do not silently expand.
- Return only the JSON envelope with the exact task ID, actual command/exit/counts and all changed target files. Zero collected tests is not a passing test run. An unavailable check is not PASSED.

## Acceptance gate — orchestration checks the model cannot self-certify
1. Compare the envelope's task ID and exact Verify command with the packet. Do not execute an unapproved envelope command. Check the actual target diff and pre-existing dirty files; .agent/ files are ignored by the current accept.sh boundary loop, so review them manually too.
2. Validate reported counts/output and relevant integration requirements. Worker-reported success alone is insufficient. For a valid candidate run accept.sh once; it independently reruns Verify, checks its implemented boundaries and commits. Do not rerun the same suite a third time.
3. accept.sh currently uses git add -A. If unrelated work is present, do not run it blindly or silently include that work. A doc reconciliation may explicitly capture an existing pending packet unchanged when the owner requests all working docs; identify it and do not claim its product task passed. Otherwise wait for a safe acceptance boundary or record the commit blocker.
4. Full disposable integration is a domain milestone, not a whole-phase-only gate. Auth/permissions/SQL/schema/persistence/shared-provider changes require their relevant integration proof at task scope too. A static-only accepted commit is TASK_VERIFIED/PARTIALLY_VERIFIED, not DOMAIN_VERIFIED. Run no real database mutation.
5. Update short state once with evidence IDs, scope, integration debt and next action. Record any scope/command deviation and its repair; no transcript polling loop. Existing work remains evidence, not an instruction to redo it.

## What is enforced versus what is a rule
| Mechanism | Actually checks | Does not establish |
|---|---|---|
| boot.sh | Existing lock/budgets and configured harness checks | Actual Antigravity UI model/thinking, task quality or final score |
| accept.sh | Envelope schema, executed Verify exit, implemented file-boundary loop, commit | Exact packet-command equality, worker role, .agent/ scope, relevance/coverage, real UI settings or unrun integration |
| Tests/lints/score.sh | Their actual assertions, exits and recorded scoring evidence | Untested behavior or a model's verbal compliance |
| Packet + orchestrator review | Explicit scope, command authorization, evidence and repair decisions | Guaranteed future obedience by any model |

Docs reduce ambiguity; they cannot guarantee model compliance. Never call a manual rule mechanically enforced unless a real check exists. No new enforcement script/config/product code is introduced by this documentation task. On deviation: stop that worker's expansion, preserve its in-scope work, issue one focused repair with evidence; obey the five-repair ceiling and escalate identical failures without a changed hypothesis.
