# ApexGrid delivery workflow

Authority: owner instruction of 2026-10-26 and ADR-014. This is the single execution policy for the active overhaul. AGENTS.md supplies routing and safety; docs/overhaul-plan.md supplies scope/design/task requirements; evaluation.md owns scores and thresholds. Other protocol files link here rather than adding duplicate run schedules.

## Operating state
- New model entrypoint: `.agent/START_HERE.md`. Its numbered steps link to authoritative rules instead of requiring chat history.
- Active branch: `overhaul/neo-brutal`. The earlier perfection-loop queue/log is historical.
- Implementation is currently PAUSED by the owner. Complete only documentation; dispatch no implementation worker until the owner says start work or explicitly resumes implementation. That new instruction lifts this pause: update state to RUNNING and continue without asking again.
- On resume, read AGENTS.md, CURRENT_STATE.md, NEXT_STATE.md and only relevant architecture/contracts/plan sections. Accepted work is evidence, not a request to restart phases.
- Preserve all existing features, API contracts, data, tests, assertions, score weights and gates. No secrets or .env access, recursive deletion, production DB mutation, force-push or merge. Database checks use only guarded disposable `apexgrid-test` resources.

## Size work around a complete concern
- Normal task: one owner, up to 3 target files and about 150 changed lines expected.
- Mechanical move or tightly coupled structural/DI tranche: one domain, up to 8 named target files and 800 changed lines expected. Explain why a smaller split would introduce throwaway glue. No unrelated behavior change, dependency or migration in the same task. Split a larger tranche by domain.
- Documentation-only reconciliation: orchestrator-owned, explicit named Markdown files, no product/executable/config changes; it may span more files. Use a documentation verifier and accept.sh; do not run product suites for prose changes.
- Limits are review bounds, not goals. A task must improve a real module boundary, user journey or measured defect. Do not add forwarding/assembly wrappers just to reduce a line count.
- T-331 and T-332 form one structural milestone delivered by domain: move each domain toward its final dependency-injected shape once. Keep main.py <=120 lines as the final entrypoint criterion. Reuse existing request providers and characterization tests; preserve handlers required by callers/tests. Review recent assembly-only modules for folding into final domain ownership, without speculative rewrites.
- W1/W2/W3 ownership and the two-worker cap remain. W3 owns tests; use existing tests when adequate. A missing regression test is a preceding W3 task; a known defect gets a demonstrated failing test before its W1/W2 fix. Pure moves use existing characterization coverage.
- Parallelize only disjoint target files and satisfied dependencies. Independent UI/QA work can accompany backend work; do not serialize unrelated work merely because phase numbers differ. Never exceed two workers.

## Verification levels
| Level | When | Required evidence |
|---|---|---|
| Task | Every product result | Relevant regression/characterization tests; snapshot for backend routing/contract work; applicable scoped lint/types. Worker runs Verify; orchestrator independently reruns the same command through accept.sh. |
| Domain/milestone | A coherent domain tranche closes | Backend: full disposable pytest with zero DB skips, snapshot, Ruff/format and strict mypy. Frontend: typecheck, zero-warning lint, `lint-spacing.sh`, `lint-banned.sh`, `lint-motion.sh`, `lint-neobrutal.sh`, build and affected route/state/keyboard/axe/viewport checks. Record counts and environment. |
| Release | Completed implementation and final repairs | Full current backend, production build, real-stack E2E, all route/viewports, visual, accessibility, security audits, coverage and performance evidence; evaluation.md score >=95 and every hard gate passes. No NOT_RUN accepted as completion. |

- The task row's Verify describes the acceptance requirement; expanded commands are recorded in the packet. A large parent task's full-suite requirement is the milestone gate, not an extra full run for every mechanical child task.
- Auth, permissions, schema, SQL, simulator persistence/order or shared providers require relevant integration tests before their task is considered verified; these are not deferred merely for speed. The orchestrator runs DB/browser/network checks on the approved environment. Record a task as PARTIALLY_VERIFIED in state until required integration proof exists; never turn NOT_RUN/skips into passes.
- UI changes get an immediate focused Taste diff review; screenshots/full Taste audits run at route milestones and final evaluation. Reuse route runs that already include axe/overflow/states instead of starting duplicate runs.
- Do not run a third copy of a command already executed by accept.sh at the same tree, scope and environment. Do not broaden a passing check without a changed dependency, new failure/risk or scheduled milestone gate.
- Evidence identity: tested revision or exact product-content digest, command/options, scope, runtime/environment, fixture version and counts. Reuse only when all relevant inputs are unchanged. Shared CSS/components invalidate dependent routes; backend/provider changes invalidate dependent integration evidence. Documentation-only commits do not invalidate product evidence; final release still runs the complete gate set on the final candidate.
- Record stale or unavailable evidence explicitly. No timer-based reruns, speculative full suites or claiming old scores are current.

## Session and task loop
1. Session/resume: inspect branch/status/in-flight work and run boot.sh once. It already checks the architecture lock and state budgets. Run boot again only after harness/protocol/lock configuration changes or a failed boot is repaired. No separate budget invocation immediately after a successful boot.
2. Before dispatch: verify the architecture lock, preflight task boundaries/context and select a meaningful tranche. Validate context ranges include imports and factory wiring; target files may be read in <=100-line chunks. Packet-only workers keep their role/model profile; no model overrides.
3. Review the returned envelope and exact diff before acceptance. Save the envelope without rewriting its claims. For FAILED/malformed results, classify the cause first: do not rerun an unchanged known-failing check or launch a new worker for metadata/network-only corrections. Correct supported metadata with an audit note; product repairs go to the owning worker.
4. Run accept.sh once for a valid candidate. It reruns Verify, enforces boundaries and commits. Do not invoke a separate commit. Inspect staged/untracked content first because the current script stages all changes. Preserve owner scripts and unrelated work.
5. Update CURRENT_STATE and NEXT_STATE once per accepted result, including integration status, latest evidence, blocker and next action. Keep current facts there; use Git/results for completed history. Queue <=12 tasks; keep the rest in queue.md/backlog.md with reasons.
6. Run budget.sh every five accepted tasks, after substantial state growth or before a pause/handoff. Omit it when the same checkpoint's boot already checked budgets. Keep state <2000/<1500 tokens and AGENTS.md <12000 characters.
7. Repair only with a concrete failing output or review finding. An identical failure without a changed hypothesis is escalation evidence, not another blind retry. At most five targeted repair iterations per task/milestone; keep unrelated work progressing when permitted. Log blockers honestly.

## Canonical references and completion
- Product scope and all twelve phase requirements: docs/overhaul-plan.md; phase numbering reports progress and does not multiply verification.
- Roles/models: roles.md and .agent/models.env; packet schema/boundaries: packets.md and envelope.schema.json.
- Commands: .agent/commands.env and existing test-stack/browser configuration. Do not copy setup templates over a configured project.
- Runtime contracts: docs/contracts.md, docs/api.md and locked ARCHITECT.md; architecture changes follow architect.md/ADRs.
- Scores: evaluation.md and scripts/eval/score.sh. Reuse matching evidence across dimensions; no four duplicate suite runs for four scoring workers.
- Stop after satisfying the final definition of done or an honest escalation. Do not invent extra polish cycles. During the current pause, documentation completion does not authorize implementation.
