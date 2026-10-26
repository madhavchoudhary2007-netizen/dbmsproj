# Context recovery and handoff

Read after compaction/new session or before ending a session. Context limits/configuration are owned by .agent/models.env and harness settings; do not change them during recovery. State is saved after every accepted result, so recovery does not need another historical audit.

## Resume
1. Read AGENTS.md, CURRENT_STATE.md, NEXT_STATE.md and the relevant locked ARCHITECT.md sections in <=100-line ranges. Read delivery-workflow.md for cadence; read only the next task's plan/contract sections. Resolve permission from the latest owner request and current state; do not freeze a historical PAUSED or RUNNING sentence. For Antigravity read antigravity.md once and record observed model/thinking or UNVERIFIED.
2. Inspect branch, git status and recent commits. Active overhaul branch is overhaul/neo-brutal. Reconcile the last accepted task/verified product revision with Git; a later docs-only commit does not invalidate product evidence. Preserve unrelated owner edits/scripts.
3. Run boot.sh once. It verifies lock and state budgets; do not immediately run those subchecks again. If state is over budget, condense completed history per state-files.md, then retry only the failed checkpoint.
4. Inspect live workers and only the active queue packets/results. A missing result does not prove a worker is gone. Recover completed candidates under packets.md; re-dispatch only after confirming the worker is no longer running and reviewing its diff. Do not accept an old result blindly after dependencies changed.
5. Preserve the active task/owner and do not repeat completed domains named in current state. Resume implementation only when the owner has authorized it and NEXT_STATE records RUNNING. Use normal accept.sh commits; no automatic checkpoint commit or runner process.

## Handoff
Keep current evidence, partial verification, in-flight task ID/targets and next action on disk. Record a pause explicitly. Run budget only if it was not already covered at this checkpoint. Never read every historical result/log or restart an old loop just to recover context.
