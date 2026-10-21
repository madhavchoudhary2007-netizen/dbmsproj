# Roles, models and dispatch

Read when: configuring models or effort, dispatching a worker, running the Taste Agent.

## Role contracts

| Role | Owns | MUST NOT |
|---|---|---|
| Orchestrator | ARCHITECT.md, CURRENT/NEXT_STATE.md, ADRs, git history, reviews, scoring | Write repetitive boilerplate (scaffolds, token files, fixtures, CRUD, type re-exports). Edit more than 40 product lines per turn; the only exception is integration glue spanning two workers' boundaries, logged in CURRENT_STATE under "Orchestrator direct edits". Accept a result without re-running its verify command. Present a score below 95. |
| W1 UI/Layout | `*.tsx *.jsx *.css`, design tokens, Tailwind config, assets. Delivers presentational components that render all 5 UI states, use tokens only, meet 44×44 targets and mobile ergonomics | Create stores, call `fetch`, define API types, write tests other than state fixtures the packet names |
| W2 State/Runtime | Stores, hooks, mutations, data-fetching layer, API handlers, schemas, workers, simulation loops. Delivers typed contracts, optimistic update with rollback, cancellation, idempotency, error normalization | Change markup, class names or tokens; touch `tests/` |
| W3 Eval/QA | `tests/ e2e/ scripts/eval/`, Playwright, AST checks, invariant asserts, unit tests, score JSON | Edit product source to make a test pass. A failing test is reported FAILED with the defect; the assertion is never weakened |

## Taste Agent (orchestrator mode)

Runs after architecture Phase B, after every UI packet merges, and when scoring A-5/A-6 in `evaluation.md`. Checks in order:

1. Focal points: exactly one primary action per viewport (count accent-styled elements in the initial viewport).
2. Palette tension: 60-30-10, one accent hue, no gradient spanning more than 60° of hue.
3. Clutter: at most 3 font sizes and 2 weights per card; never border plus shadow plus background change on one element.
4. Bloat: no abstraction with a single call site; no dependency replacing under 30 lines; no file over 300 lines.

Output one line per defect, enqueued in NEXT_STATE: `TASTE-<n>: <file>:<line> — <rule> — <required change>`.

## Model map and configuration

| Role | Claude Code | Codex CLI | Antigravity / Gemini CLI |
|---|---|---|---|
| Orchestrator | Sonnet 5.5, medium | GPT-6 Sol, medium | Gemini 3.8 Flash, high thinking |
| W1, W2, W3 | Haiku 5.5, high | GPT-6 Luna, high | Gemini 3.8 Flash, low thinking |
| Max concurrent workers | 2 | 2 | 2 |

IDs, effort/thinking levels, `MAX_WORKERS` and the context window are set once in `.agent/models.env` (one profile per `HARNESS`). The exact ID strings must be the ones your account lists; fix them there if they differ. Nothing else hard-codes a model. If `bash scripts/agent/boot.sh --probe` fails for a model, stop and report the exact error; never substitute silently.

## Dispatch

Workers always start fresh with the packet file as the entire prompt (packet format: `packets.md`).

```bash
claude -p "$(cat .agent/packets/T-014.md)" --model "$WORKER_MODEL" --effort "$WORKER_EFFORT" --output-format json > .agent/results/T-014.raw.json
codex exec --model "$WORKER_MODEL" "$(cat .agent/packets/T-014.md)" > .agent/results/T-014.raw.txt
gemini -m "$WORKER_MODEL" -p "$(cat .agent/packets/T-014.md)" > .agent/results/T-014.raw.txt
# Antigravity: new agent conversation, packet as the only message, save the JSON envelope to .agent/results/T-014.json
```

Inside Claude Code, prefer the Agent tool with `subagent_type` set to `w1-ui`, `w2-state` or `w3-eval` and the packet text as the prompt. Do not pass `model` or `effort` in that call: a per-call value overrides the frontmatter.

Parallelism: at most `MAX_WORKERS` (2) workers at once; queue the rest. W1 and W2 packets with disjoint `target_files` may run together. W3 runs after the packets it verifies have merged. Two packets touching the same file are serialized. For stronger isolation add `isolation: worktree` to a worker's frontmatter.

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

## Antigravity and Gemini CLI (instructions only)

Antigravity documents no file setting for subagent count, subagent model or thinking level, and no custom subagents. So this is a rule, not a binding: the orchestrator runs on Gemini 3.8 Flash with high thinking; run at most 2 subagents at once, each Gemini 3.8 Flash with low thinking, picking those in the UI where offered. Verify in the UI at session start and report any mismatch. Gemini CLI: pass `-m "$WORKER_MODEL"`; its thinking level has no flag in this kit, set it in its config if your version supports it.
