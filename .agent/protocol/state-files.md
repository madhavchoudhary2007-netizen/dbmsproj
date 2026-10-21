# State files and task atomicity

Read when: creating or updating `.agent/CURRENT_STATE.md` or `.agent/NEXT_STATE.md`, or splitting work into tasks.

Agent memory lives on disk, not in the conversation. A cold session must be able to resume from `ARCHITECT.md`, `CURRENT_STATE.md` and `NEXT_STATE.md` alone.

| File | Purpose | Budget | Update when |
|---|---|---|---|
| `.agent/CURRENT_STATE.md` | Verified ground truth | < 2,000 tokens | After every accepted envelope and every commit |
| `.agent/NEXT_STATE.md` | Ordered atomic task queue | < 1,500 tokens | A task is added, dispatched, finished or re-enqueued |

`bash scripts/agent/budget.sh` measures both (1 token ≈ 4 characters). Over budget: move finished detail to git history (it is in the commit messages), collapse VERIFIED component rows into one line, and delete invariants already enforced by a test (cite the test file instead).

The repo ships both files as empty scaffolds. The examples below show the exact format with realistic values.

## CURRENT_STATE.md

```markdown
# CURRENT_STATE
updated_at: 2026-10-19T11:05:00Z
git_head: 9c41e2a
branch: feat/projects-list
architect_sha256: 3f1c9e0b7d2a4c6e8f0a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e4f5a6
archetype: enterprise-saas
last_eval_score: 91.5 (2026-10-19T10:52Z, .agent/eval/score.json)

## Active contracts
- src/types/project.ts → Project { id: string; name: string; ownerId: string; updatedAt: string; status: "active"|"archived" }
- GET /api/projects?status=&q= → { items: Project[]; total: number }
- PATCH /api/projects/:id (header Idempotency-Key required) → Project

## Component status
| Component | Owner | Status | States | Verified by |
|---|---|---|---|---|
| tokens.css | W1 | VERIFIED | n/a | scripts/eval/palette.ts, lint-spacing.sh |
| ProjectList | W1 | IN_REVIEW | 5/5 | e2e/states/project-list.spec.ts |
| useRenameProject | W2 | FAILED | n/a | rollback test (T-021) |
Status values: PLANNED, IN_PROGRESS, IN_REVIEW, VERIFIED, FAILED

## Known invariants
- INV-1: items.length <= total (tests/state/use-projects.spec.ts)
- INV-3: a failed optimistic rename restores the previous name within one render (FAILING)

## Orchestrator direct edits
- 2026-10-19 src/app/routes.tsx (18 lines): wired ProjectList to useProjects

## Open risks
- R-2: 10k-row fixture renders in 410ms (budget 300ms); T-023 queued
```

## NEXT_STATE.md

```markdown
# NEXT_STATE
updated_at: 2026-10-19T11:05:00Z
loop_iteration: 2 of 5

## Queue (dispatch top-down; parallelize only disjoint target_files)
### T-021 — Fix optimistic rename rollback
- worker: W2 | priority: P0 | origin: EVAL 10:52Z F-3
- target_files: src/state/useRenameProject.ts
- read_only_context: src/types/project.ts, src/lib/api.ts (1–60)
- contract: on error the cache ["projects"] equals the pre-mutation snapshot; one error toast with retry
- boundaries: no component, test or api.ts edits
- verify: pnpm exec vitest run tests/state/use-rename-project.spec.ts

### T-024 — TASTE-2: one primary button in the ProjectList header
- worker: W1 | priority: P2
- target_files: src/components/projects/ProjectListHeader.tsx
- contract: exactly one data-primary="true" in the header; "Import" becomes secondary
- boundaries: no token changes
- verify: pnpm exec playwright test e2e/taste/focal-points.spec.ts

## Blocked
- none

## Done this iteration (pruned on compaction)
- T-019 ✓ 9c41e2a
```

`accept.sh` reads the `target_files:` line of the task's `### T-nnn` block, so keep that exact key and a comma-separated list.

## Atomic task

A task is atomic only if all hold: one worker; at most 3 target files; at most 150 changed lines expected; one verify command that exits 0 on success; no dependency on another task in the same batch. Otherwise split it before dispatch.
