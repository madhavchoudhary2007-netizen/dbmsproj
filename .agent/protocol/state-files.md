# State files and task atomicity

Read when updating state or splitting work. Task sizing and verification cadence are defined once in delivery-workflow.md (ADR-014).

## Current facts, not a duplicate history
- CURRENT_STATE.md: <2000 tokens. Record branch, requested/observed harness settings or UNVERIFIED, verified product revision, last accepted task, architecture hash, phase/milestone outcomes, current evidence and unresolved risks. Name the evidence source; distinguish task, integration and release verification.
- NEXT_STATE.md: <1500 tokens. Record execution state from the latest owner instruction (PAUSED/RUNNING), next <=12 tasks with true dependencies, blockers and the next action. Completed work belongs in Git/results; keep at most five recent completion IDs.
- queue.md/backlog.md: remaining findings with ID, severity, evidence and reason/dependency. Do not lose deferred work when shortening state.
- Update both state files once after each accepted result. Orchestrator-owned docs reconciliation may prepare the state for its own acceptance commit; identify it by task ID and reconcile its hash from Git on resume. Documentation commits do not erase the last verified product revision.
- Budget is checked every five accepted tasks, after substantial state growth and before a pause/handoff unless boot checked it at that checkpoint. Never call budget immediately after a successful boot merely to repeat the same check.
- On overflow, remove completed detail already present in commits/results and duplicated standing rules. Do not discard open findings or invent completion. Large historical logs are read only when a concrete ambiguity needs them.

## Task format

```markdown
### T-123 — One complete concern
- worker: W2 | priority: P1 | origin: T-331/T-332 domain milestone
- target_files: backend/app/example.py, backend/app/api/example.py
- read_only_context: docs/contracts.md (relevant section), backend/tests/test_example.py (specific range)
- contract: exact preserved behavior or measured defect and expected outcome
- boundaries: no unrelated behavior/dependency/API/schema changes
- verify: exact offline command; name root-owned integration evidence separately
```

accept.sh reads the `### T-nnn` heading and comma-separated `target_files:` line; keep them exact. The packet includes any structural-size exception justification and the complete named target list. Normal, structural and docs-only limits are in delivery-workflow.md; do not reintroduce a conflicting 150-line hard cap here.

## Resume and pause

CURRENT_STATE is the current verified snapshot. NEXT_STATE is the queue, not a second status narrative. Respect PAUSED even if old packets, logs or task rows say continue. On an owner start instruction, reconcile Git and in-flight work, update state to RUNNING, then dispatch. A packet without a result is not proof that its worker disappeared: inspect live agent status before redispatching.

No clean-checkpoint or state-only commit outside accept.sh. The orchestrator owns documentation/state/ADRs; product changes remain delegated with their configured role boundaries.

## Evidence and coordination receipt
Record each active task ID, role/worker ID, domain, exact packet Verify, root integration requirement and state (IN_FLIGHT/TASK_VERIFIED/PARTIALLY_VERIFIED/DOMAIN_VERIFIED). A static-only accepted refactor is not a completed integration milestone. Keep one short session model/settings receipt rather than repeating it per task while configuration is unchanged. When another session owns an in-flight packet, preserve it and current progress; do not overwrite state with a stale first-task plan. A documentation reconciliation may capture that pending packet unchanged as explicit context; it does not accept the product task.
