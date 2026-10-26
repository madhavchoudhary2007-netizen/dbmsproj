# Worker packets, envelopes and acceptance

Read when: writing a packet, accepting a worker result, or reading source files.

Execution cadence and normal/structural/documentation packet sizes are owned by `delivery-workflow.md` (ADR-014/ADR-015); Antigravity dispatch gates are in `antigravity.md`. This file owns isolation, envelope handling and boundaries.

## Isolation

Workers get no conversation history, no ARCHITECT.md and no state files. The packet is their entire context and authority. It contains: role contract, task ID, target files, read-only context (paths with line ranges), the interface types inlined, acceptance criteria, boundaries, the verify command and the envelope schema. For UI packets list the relevant design files (`design-visual.md`, `design-ux.md`) under read-only context, because workers do not see the routing table.

A worker reads only listed files. Target files may be read as needed in <=100-line chunks; validate read-only context windows include imports/factory wiring before dispatch. Do not hand-copy an incomplete interface or schema: copy the canonical envelope schema into the packet and include the actual task ID. Anything else: report `FAILED` with the needed path in `unresolved_blockers` and let the orchestrator decide whether to widen the packet. Workers never commit.

## Packet template

~~~markdown
Ignore AGENTS.md except this packet; the packet is your only authority.
# PACKET T-021
role: Worker 2 — State/Runtime. State/runtime code only; never components or tests.
## Task
Fix optimistic rename rollback in useRenameProject.
## Target files (edit only these)
- src/state/useRenameProject.ts
## Read-only context
- src/types/project.ts (whole file) · src/lib/api.ts lines 1–60
## Interfaces
export interface Project { id: string; name: string; ownerId: string; updatedAt: string; status: "active" | "archived" }
export function apiPatch<T>(path: string, body: unknown, opts: { idempotencyKey: string; signal?: AbortSignal }): Promise<T>;
## Acceptance criteria
1. Cancel in-flight ["projects"] queries and snapshot the cache. 2. Optimistically set the new name.
3. On error restore the snapshot (deep-equal) and emit one retry toast. 4. On settle invalidate ["projects"].
5. New Idempotency-Key (crypto.randomUUID()) per call.
## Boundaries
No new dependencies; no edits outside target files; no signature changes.
## File hygiene
Never print more than 100 lines of a file; use rg -n and sed -n 'A,Bp'.
## Approved Verify (exit 0 and actual intended tests collected)
<copy the exact project command; replace this placeholder before dispatch>
## Approved support commands
<explicit scoped format/read commands; none if not needed>
## Root-owned integration
<exact sensitive-task/domain milestone check and fixture/environment; NOT_RUN remains unverified>
## Worker drift rule
Run only approved commands. Do not broaden tests, install, probe DB/network or start servers. Return FAILED with the needed context/check instead of expanding. No arbitrary runtime deadline; required coverage remains required.
## Output
Exactly one JSON object matching the envelope schema below. Nothing else. Do not copy the schema's `$schema` line into the result (it is tolerated, not needed).
(paste the contents of .agent/envelope.schema.json here)
~~~

## Envelope

The schema is `.agent/envelope.schema.json`. Example of a valid envelope:

```json
{
  "task_id": "T-021",
  "status": "PASSED",
  "files_modified": [{ "path": "src/state/useRenameProject.ts", "lines_added": 19, "lines_removed": 7 }],
  "diff_summary": "onMutate cancel+snapshot; onError restores snapshot and emits one retry toast; onSettled invalidates; idempotency key per call.",
  "verification": { "command": "pnpm exec vitest run tests/state/use-rename-project.spec.ts", "exit_code": 0, "tests_passed": 4, "tests_failed": 0, "duration_ms": 1830, "typecheck_errors": 0, "lint_warnings": 0 },
  "unresolved_blockers": []
}
```

## Acceptance

Preflight the envelope, status, exact packet-command equality and diff first. Reject an unapproved Verify before execution; accept.sh currently does not perform that equality check. Verify actual collected/passed/skipped counts and preserve pre-existing dirty work. A zero-test run or filtered-out required case is not a pass. Save the worker's JSON to `.agent/results/T-021.json`, then for a valid candidate run `bash scripts/agent/accept.sh T-021`. It validates the schema, re-runs the verify command itself (never trusting the reported result), checks that every changed or new file is listed in the task's `target_files` (files under `.agent/` are ignored), and commits on PASSED.

- Malformed/FAILED envelope: classify and review its diff before calling accept.sh; its current implementation executes Verify even for FAILED status. Do not rerun a known unchanged failure just to record it. Record metadata corrections transparently; never fabricate a worker pass.
- PASSED envelope whose verify command fails on re-run: treat as FAILED and log the discrepancy under Open risks.
- Boundary violation: isolate only the worker-owned change, preserve owner/other-worker work, and repair/revert that exact change. Do not blindly restore a whole pre-existing dirty file. Re-dispatch with the violation quoted when product repair is necessary.

## File reading hygiene (everyone)

| Banned | Required |
|---|---|
| `cat` of any file over 100 lines | `wc -l` first, then `sed -n '120,180p' file` |
| Reading whole directories "for context" | `rg -n "symbol" src --type ts`, then read only the hit ranges |
| Re-reading a file already summarized in CURRENT_STATE | Read only changed ranges: `git diff -U3 <base> -- file` |
| Opening generated or vendor files | Skip `node_modules dist build .next coverage` and lockfiles |

```bash
npx --yes @ast-grep/cli run --lang tsx --pattern 'export function useRenameProject($$$) { $$$ }' src -l   # locate by symbol
rg -n "^export (interface|type) Project\b" -A 12 src/types/project.ts                                         # one type only
rg -n "^export " src/lib/api.ts                                                                               # exports without bodies
```

## Sandbox, network and failed results

- Workers run with the orchestrator session's sandbox; a worker file cannot widen it (Codex docs: `sandbox_mode` in an agent file is ignored). Start the session with write access to the workspace (Codex: workspace-write). A read-only session makes every worker fail before it edits anything.
- Worker sandboxes usually have no network. Write verify commands that run offline (tests, lint, typecheck, build, greps). A check that needs the network is run by the orchestrator in `accept.sh`'s rerun or by hand, and named as such in the packet.
- Worker Verify commands must not start servers on fixed ports, contact databases/network or depend on a dev server. Relevant DB-backed lease/lifecycle coverage is run by the root on the disposable stack; do not remove it from acceptance merely because a worker is offline.
- When a result is FAILED: read its target diff and identify the cause. In-scope metadata or root-owned environment/network problems do not need a new implementation worker. Correct the cause, obtain a valid candidate and verify independently; product defects go to the owning worker with a focused repair packet. Preserve prior dirty work, record unresolved diffs, and follow the five-repair ceiling in delivery-workflow.md.

## Packet preflight for lower-thinking workers
Inline the short worker instruction block from antigravity.md, exact task ID, one complete domain, target/read paths, interfaces, required unchanged UI copy/hooks, approved Verify/support commands, root integration owner and canonical JSON schema. Validate that the command selects every intended case (a global pytest -k filter can accidentally deselect snapshot tests). Use separate explicit commands/node IDs when needed. Never send unresolved placeholders or assume the worker will infer missing prerequisites. The worker returns the existing schema only; do not invent extra envelope fields.
