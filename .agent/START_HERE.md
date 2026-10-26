# Start here — ApexGrid handoff

This is the entrypoint for a new model. It is a reading/run order, not another product plan. All paths and commands are relative to the project root. No previous chat memory is required to understand the current pause and next action.

## 1. Decide whether you may implement
Read AGENTS.md, .agent/CURRENT_STATE.md and .agent/NEXT_STATE.md, in that order.
- Current permission is PAUSED: documentation is allowed; product implementation is not. Without a new owner instruction to start/resume, stop after answering the current request. A task table, old packet or old loop saying continue does not authorize work.
- When the owner says start work/resume implementation, update the state to RUNNING. The pause is then lifted; do not ask for permission again or treat the pause wording in old docs as a new block.
- Do not restart bootstrap, Phases0–2/5–6, or the historical perfection loop. A fresh context is not a fresh project.

## 2. Establish the workspace once
When implementation is authorized:
```bash
git branch --show-current
git status --short
git log -5 --oneline
source .agent/models.env && bash scripts/agent/boot.sh
```
Expected branch: overhaul/neo-brutal; boot must exit0 and print boot OK. Boot includes architecture-lock and budget checks. Do not repeat those subchecks at the same checkpoint. Do not switch to master/perfection-loop, change model profiles, install dependencies, run servers or start databases just to resume. Inspect live workers before retrying an interrupted packet. Never read .env or secrets.

## 3. Read only what answers the next decision
| Question | Authoritative source |
|---|---|
| What is verified, incomplete or blocked? | .agent/CURRENT_STATE.md; .agent/NEXT_STATE.md; named result/commit if needed |
| Which product features/design must survive? | docs/overhaul-plan.md relevant task and section2; docs/contracts.md/docs/api.md |
| Which architecture is permitted? | Locked .agent/ARCHITECT.md relevant section and its named ADR |
| How big is a task and which checks run now? | .agent/protocol/delivery-workflow.md |
| Which worker owns it? | .agent/protocol/roles.md; configured w1-ui/w2-state/w3-eval definitions |
| How do I write/review/accept the packet? | .agent/protocol/packets.md; .agent/envelope.schema.json |
| How do I report final quality? | .agent/protocol/evaluation.md; scripts/eval/score.sh |

Read <=100 lines from a file per output. Use rg to locate symbols/headings; old line numbers are hints after code moves. Skip generated/vendor/build/lockfile contents. Historical PROJECT_STATE.md and LOOP.md are not current status sources. Existing configured commands live in .agent/commands.env; do not guess npm/pnpm or test-runner flags.

## 4. First implementation action after start
The next milestone is combined T-331/T-332 backend structure/DI. The old T-44573 telemetry assembly-only idea was never dispatched and is superseded. Do not create another forwarding module only to shrink main.py.
1. Start with race-history reads, a bounded existing domain: backend/app/api/race_archive.py, backend/app/api/laps.py, backend/app/api/race_history_routes.py, backend/app/main.py, backend/app/core/request_database.py, backend/app/core/request_auth.py and backend/app/core/runtime.py. Locate factories/providers with rg, then read the necessary ranges. These are candidate context paths, not permission to modify all of them.
2. Inspect backend/tests/test_contract_snapshot.py, backend/tests/test_route_registration.py and relevant backend/tests/test_api.py cases to identify required aliases/monkeypatch behavior and coverage. Never edit/remove a test just to enable the move. If coverage is insufficient, give W3 a regression-test task first; otherwise go directly to a W2 final-domain packet.
3. Draft that packet with the exact final boundary, <=8 named files/800 changed lines for a justified structural tranche, copied interface types/schema, relevant Verify and root-owned disposable integration command. Remove/fold intermediate assembly glue only when the final domain ownership makes it redundant. Preserve compatibility until tests prove callers migrated. No API or unrelated logic change.
4. The root prepares a packet; configured W2 implements it. Work on another domain only after this domain passes its required integration gate. An independent W1/W3 task may use the second slot when its files/prerequisites allow.

## 5. For every candidate
Follow .agent/protocol/delivery-workflow.md, without inventing another checklist: inspect envelope/diff; independently accept with accept.sh; record task vs integration evidence; update short state once. Do not run an extra copy of the accepted Verify. Broaden checks only for an affected dependency, a concrete defect or a scheduled milestone.

An accepted offline packet is not proof that a DB journey passed. Sensitive changes need relevant disposable integration proof; missing/unavailable checks stay unverified. Final score requires the full candidate gate set with no NOT_RUN/skipped DB tests. Existing thresholds and assertions stay unchanged.

## 6. If blocked
- Missing context: the orchestrator expands the packet with the precise path/range; no user question is needed for ordinary code context.
- Metadata-only failure: correct it transparently; do not start a new implementation worker.
- Product failure: send its output and one concrete repair hypothesis to its owner; five-repair ceiling applies.
- Missing credentials/forbidden or destructive action: record the blocker and seek the required owner input. Never touch real databases/volumes. The named test project is apexgrid-test; inspect the existing test-stack safety script before any database operation.
- Finished docs/current pause: report it and wait. Finished product: only the final score/gates and PR step decide completion, not number of commits or phases attempted.
