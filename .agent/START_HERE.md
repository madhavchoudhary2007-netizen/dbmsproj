# Start here — ApexGrid handoff

This is the entrypoint for a new model. It is a reading/run order, not another product plan. All paths and commands are relative to the project root. No previous chat memory is required to understand the current permission and next action.

## 1. Decide whether you may implement
Read AGENTS.md, .agent/CURRENT_STATE.md and .agent/NEXT_STATE.md, then .agent/DOC_AUTHORITY.md once.
- Resolve permission from the latest owner instruction and current state. An explicit start/resume lifts an older pause; a documentation-only request authorizes documentation only. Preserve another session's in-flight task and do not launch a competing orchestrator.
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
| Antigravity setup and compliance? | .agent/protocol/antigravity.md; requested Gemini 3.8 Flash HIGH orchestrator / LOW workers; actual UI settings or UNVERIFIED |
| Which worker owns it? | .agent/protocol/roles.md; roles.md; for Antigravity use UI-selected isolated roles, not Codex/Claude configuration files |
| How do I write/review/accept the packet? | .agent/protocol/packets.md; .agent/envelope.schema.json |
| How do I report final quality? | .agent/protocol/evaluation.md; scripts/eval/score.sh |

Read <=100 lines from a file per output. Use rg to locate symbols/headings; old line numbers are hints after code moves. Skip generated/vendor/build/lockfile contents; an exact required framework guide may be named by root as packet read-only context per packets.md. Historical PROJECT_STATE.md and LOOP.md are not current status sources. Existing configured commands live in .agent/commands.env; do not guess npm/pnpm or test-runner flags.

## 4. Next implementation action, only when authorized
Read the live queue and docs/completion-plan.md, not an old starting task. The 2026-10-27 audit reopens concrete showcase/security/CI gaps. Reconcile the current T-411 dirty config/spec/packet owner first; preserve their bytes. No accepted router/DI domain is restarted. Prepare safe acceptance-scope regression/fix before parallel commits; then follow ready dependency rows and existing scope/gates.
1. Inspect only the next task's domain and existing characterization/snapshot tests. Preserve all contracts and assertions. If coverage is missing, queue a focused W3 regression task before the product move.
2. Use one coherent responsibility per packet, normally small; a justified structural tranche may use <=8 named files/800 changed lines. This is a ceiling, not a target. CRUD and simulation/lifecycle stay separate unless an indivisible dependency is documented. Do not create forwarding wrappers only to shrink main.py.
3. Record exact offline worker checks, any approved support commands and root-owned disposable integration. No arbitrary three-second cutoff: relevant lifecycle/lease/auth/persistence coverage remains mandatory. Inspect pytest selection so required tests are actually collected.
4. Keep one ready W2 backend lane and one independent W1 measured frontend-repair lane where prerequisites and disjoint files permit. Two workers maximum; no filler work. Domain integration gates run before advancing dependent domains. main.py<=120 alone does not complete Phase 3; T-333..T-340 still require evidence.

## 5. For every candidate
Follow .agent/protocol/delivery-workflow.md, without inventing another checklist: inspect envelope/diff and exact packet/envelope Verify equality before execution; independently accept with accept.sh; record task vs integration evidence; update short state once. Do not run an extra copy of the accepted Verify. Broaden checks only for an affected dependency, a concrete defect or a scheduled milestone.

An accepted offline packet is not proof that a DB journey passed. Sensitive changes need relevant disposable integration proof; missing/unavailable checks stay unverified. Final score requires the full candidate gate set with no NOT_RUN/skipped DB tests. Existing thresholds and assertions stay unchanged.

## 6. If blocked
- Missing context: the orchestrator expands the packet with the precise path/range; no user question is needed for ordinary code context.
- Metadata-only failure: correct it transparently; do not start a new implementation worker.
- Product failure: send its output and one concrete repair hypothesis to its owner; five-repair ceiling applies.
- Missing credentials/forbidden or destructive action: record the blocker and seek the required owner input. Never touch real databases/volumes. The named test project is apexgrid-test; inspect the existing test-stack safety script before any database operation.
- Finished documentation request: report it and wait for implementation authorization applicable to this session. Finished product: only the final score/gates and PR step decide completion, not number of commits or phases attempted.
