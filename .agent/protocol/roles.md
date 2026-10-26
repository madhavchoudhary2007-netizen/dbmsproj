# Roles, models and dispatch

Read when: configuring models or effort, dispatching a worker, running the Taste Agent.

## Role contracts

| Role | Owns | MUST NOT |
|---|---|---|
| Orchestrator | ARCHITECT.md, CURRENT/NEXT_STATE.md, ADRs, git history, reviews, scoring | Write repetitive boilerplate (scaffolds, token files, fixtures, CRUD, type re-exports). Edit more than 40 product lines per turn; the only exception is integration glue spanning two workers' boundaries, logged in CURRENT_STATE under "Orchestrator direct edits". Accept a result without re-running its verify command. Claim completion below score 95. |
| W1 UI/Layout | `*.tsx *.jsx *.css`, design tokens, Tailwind config, assets. Delivers presentational components that render all 5 UI states, use tokens only, meet 44×44 targets and mobile ergonomics | Create stores, call `fetch`, define API types, write tests (W3 owns tests; W1 may provide presentational fixtures only when named) |
| W2 State/Runtime | Stores, hooks, mutations, data-fetching layer, API handlers, schemas, workers, simulation loops. Delivers typed contracts, optimistic update with rollback, cancellation, idempotency, error normalization | Change markup, class names or tokens; touch `tests/` |
| W3 Eval/QA | `tests/ e2e/ scripts/eval/`, Playwright, AST checks, invariant asserts, unit tests, score JSON | Edit product source to make a test pass. A failing test is reported FAILED with the defect; the assertion is never weakened |

## Taste Agent (orchestrator mode)

Runs after architecture Phase B, as a focused diff review after UI acceptance, and with screenshots at route milestones/final A-5/A-6 scoring. The schedule is delivery-workflow.md; do not rerun full screenshots after every cosmetic packet. Checks in order:

1. Focal points: exactly one data-primary per viewport/route, with its accessible primary action; semantic status accents are not extra primary actions.
2. Palette tension: approved overhaul-plan.md section 2 roles/bands, contrast and accent limits; generic palette examples do not override ADR-007. No unapproved gradient.
3. Clutter: at most 3 font sizes and 2 weights per card; approved border + static hard shadow + solid surface is allowed by ADR-007; flag redundant layers, not the approved plinth.
4. Bloat: flag an unjustified single-call-site abstraction, a dependency replacing under 30 lines without a correctness/accessibility reason, and files over 300 lines. A documented domain boundary may justify an abstraction; never add fake callers. Record file-size defects without deleting features or pretending the eight-file/800-line change allowance waives them.

Output one line per defect, enqueued in NEXT_STATE: `TASTE-<n>: <file>:<line> — <rule> — <required change>`.

## Model map and configuration

| Role | Claude Code | Codex CLI | Antigravity / Gemini CLI |
|---|---|---|---|
| Orchestrator | Sonnet 5.5, medium | GPT-6 Sol, medium | Gemini 3.8 Flash, high thinking |
| W1, W2, W3 | Haiku 5.5, high | GPT-6 Luna, high | Gemini 3.8 Flash, low thinking |
| Max concurrent workers | 2 | 2 | 2 |

IDs, effort/thinking levels, `MAX_WORKERS` and the context window are set once in `.agent/models.env` (one profile per `HARNESS`). The exact ID strings must be the ones your account lists; fix them there if they differ. Other docs state requested role labels; actual Antigravity UI settings must be recorded separately under antigravity.md. If `bash scripts/agent/boot.sh --probe` fails for a model, stop and report the exact error; never substitute silently.

## Dispatch

Codex/Claude use the configured native w1-ui, w2-state and w3-eval agents with packet-only context and no per-call model/effort override. Antigravity assigns W1/W2/W3 roles to its available isolated workers and selects the requested model/thinking in the UI under antigravity.md; do not assume Codex TOML files bind Antigravity. Packets own exact scope/interfaces/Verify; delivery-workflow.md owns task sizing and scheduling. Use existing harness profile definitions, not a shell runner or a new conversation per wrapper-sized change.

At most two workers run at once, with disjoint target files and satisfied prerequisites. W3 test work may precede the W1/W2 fix it protects; verification of merged behavior follows its dependency. Repairs use the same role and focused packet. Before redispatch after interruption, inspect live status. Preserve owner scripts and unrelated changes.

## Claude Code binding (configuration, not prose)

Prose can be ignored; settings files are read by the harness.

| Role | Model | Effort | Set in |
|---|---|---|---|
| Orchestrator | sonnet | medium | `.claude/settings.json` (`model`, `effortLevel`) |
| W1, W2, W3 | haiku | high | frontmatter of `.claude/agents/w1-ui.md`, `w2-state.md`, `w3-eval.md` |

- Worker files set `omitClaudeMd: true` so this repo's instruction files stay out of worker context (needs Claude Code 2.1.271 or later). Frontmatter keys are case-sensitive; a misspelled key is silently ignored.
- These environment variables override the binding and MUST be unset (also check the `env` block of every settings file): `CLAUDE_CODE_EFFORT_LEVEL` flattens every effort level; `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` ignores worker `model`. `boot.sh` fails if either is set.
- Verify: after the first dispatch of a session run `/tasks`; it shows each worker's model and effort. On mismatch stop and report. If Haiku does not accept `high`, `/tasks` shows the level actually applied; record it under Open risks in CURRENT_STATE.

- Auto-compact: `autoCompactWindow` and `env.CLAUDE_CODE_AUTO_COMPACT_WINDOW` are both 400000 (the env var wins if they ever differ; `boot.sh` requires both to equal `CONTEXT_WINDOW`). Claude Code caps the window at the model's own limit.
- Concurrency cap: `.claude/settings.json` sets `env.CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` to `"2"`. Resumed or forked subagents may exceed it, so also obey the rule: never start a third worker while two are running.

## Codex CLI binding

| What | Set in |
|---|---|
| Orchestrator `gpt-6-sol`, `medium` | `~/.codex/config.toml` (`model`, `model_reasoning_effort`); template `.agent/templates/codex-config.toml` |
| Workers `gpt-6-luna`, `high` | `.codex/agents/w1-ui.toml`, `w2-state.toml`, `w3-eval.toml` (`model`, `model_reasoning_effort`) |
| Cap of 2 | `[agents] max_concurrent_threads_per_session = 2` (legacy alias `max_threads`) in the same config |

`boot.sh` checks the worker TOMLs and, if `~/.codex/config.toml` exists, the `[agents]` cap. Packets still begin "Ignore AGENTS.md except this packet".

Run Codex with write access to the workspace (workspace-write). Subagents inherit the parent session's sandbox and approvals, and Codex ignores `sandbox_mode`, `approval_policy` and `mcp_servers` in an agent file. accept.sh checks only its implemented boundary loop and ignores .agent/ paths; the orchestrator manually reviews every changed path, role, and exact packet-command equality under packets.md. The sandbox does not establish task scope.

## Antigravity and Gemini CLI

The requested Antigravity profile is Gemini3.8Flash HIGH orchestration and Gemini3.8Flash LOW workers, cap2. Follow antigravity.md for observed-setting evidence, dispatch/acceptance gates and capability limitations. .agent/models.env is the requested profile, not proof of actual UI selection. No invented setting, silent substitution or boot-based model attestation.

The owner-approved no-subagent fallback is WORKER MODE: one packet/role at a time, exact targets/Verify/envelope, then ORCHESTRATOR MODE for independent acceptance. Record it as serial fallback, never as two real workers. Select LOW for worker work and HIGH for orchestration where the harness supports it; if it cannot supply the requested role settings, report that limitation rather than pretending compliance. Product-line limits apply to orchestrator integration, not an explicitly authorized worker-mode packet.

Gemini CLI uses its actual supported model/config options; Antigravity UI instructions are not claims that CLI flags or custom subagent binding exist. Do not change harness configuration during a documentation-only task.
