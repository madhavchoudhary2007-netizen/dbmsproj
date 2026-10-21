# Worker packets, envelopes and acceptance

Read when: writing a packet, accepting a worker result, or reading source files.

## Isolation

Workers get no conversation history, no ARCHITECT.md and no state files. The packet is their entire context and authority. It contains: role contract, task ID, target files, read-only context (paths with line ranges), the interface types inlined, acceptance criteria, boundaries, the verify command and the envelope schema. For UI packets list the relevant design files (`design-visual.md`, `design-ux.md`) under read-only context, because workers do not see the routing table.

A worker reads only the files listed. Anything else: report `FAILED` with the needed path in `unresolved_blockers` and let the orchestrator decide whether to widen the packet. Workers never commit.

## Packet template

~~~markdown
# PACKET T-021
Ignore AGENTS.md except this packet; the packet is your only authority.
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
## Verify (exit 0 required for PASSED)
pnpm exec vitest run tests/state/use-rename-project.spec.ts
## Output
Exactly one JSON object matching the envelope schema below. Nothing else.
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

Save the worker's JSON to `.agent/results/T-021.json`, then run `bash scripts/agent/accept.sh T-021`. It validates the schema, re-runs the verify command itself (never trusting the reported result), checks that every changed or new file is listed in the task's `target_files` (files under `.agent/` are ignored), and commits on PASSED.

- Malformed envelope: treat as FAILED.
- PASSED envelope whose verify command fails on re-run: treat as FAILED and log the discrepancy under Open risks.
- Boundary violation: `git checkout -- <file>` (delete new files), then re-dispatch once with the violation quoted in the packet.

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
