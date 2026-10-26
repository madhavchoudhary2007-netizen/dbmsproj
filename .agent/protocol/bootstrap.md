# Bootstrap, layout and conventions

Existing-project routing (ADR-014): setup is already configured. Do not repeat installs, copy templates, relink files or probe models on ordinary resume. Read CURRENT_STATE/NEXT_STATE and delivery-workflow.md; use bootstrap steps only for an actually missing setup component.

Read when: first session in a repo, or when a file from this kit is missing.

## Setup (once per repo)

1. Copy this kit into the repo root (keep dotfiles).
2. `bash scripts/agent/link.sh` creates `CLAUDE.md` as a symlink to `AGENTS.md`, creates `.agent/{packets,results,eval,adr}` and marks the scripts executable.
3. Edit `.agent/models.env` (default `HARNESS`, exact model IDs, effort, `MAX_WORKERS`) and `.agent/commands.env` (this project's real install, typecheck, lint, test, e2e and build commands; defaults assume pnpm).
4. Only if browser setup is actually missing and an authorized task requires it, adapt the template into this project's frontend/ setup. Never create a competing root runner or reinstall existing setup.
5. Add to `.gitignore`: `.agent/results/*.raw.*` and `.agent/eval/*.json` (keep `score.json` if you want history).
6. Harness setup:
   - **Gemini CLI:** set its context file name to `AGENTS.md` in its settings (the key is `contextFileName` or `context.fileName` depending on version; check your version's docs). Do not create `GEMINI.md` if Antigravity is also used.
   - **Antigravity:** nothing to link; it reads root `AGENTS.md`. Keep protocol files out of `.agent/rules/` and `.agents/rules/`.
   - **Codex CLI:** merge `.agent/templates/codex-config.toml` into `~/.codex/config.toml` (orchestrator model, `[agents]` cap of 2); worker definitions are already in `.codex/agents/`. Check combined instruction size with `bash scripts/agent/budget.sh`.
7. Run `source .agent/models.env && bash scripts/agent/boot.sh`. Bootstrap is complete when it prints `boot OK`. CLI model probing is root-owned only when supported and explicitly needed; it does not verify Antigravity UI binding. For Antigravity record observed model/thinking under antigravity.md.

## Layout

```
AGENTS.md                      router (always loaded, under 12,000 characters)
CLAUDE.md -> AGENTS.md
.claude/settings.json          orchestrator model + effort + 2-worker cap
.claude/agents/                w1-ui.md  w2-state.md  w3-eval.md (worker model + effort)
.claude/rules/frontend.md      points UI work at the design files
.codex/agents/                 w1-ui.toml  w2-state.toml  w3-eval.toml (Codex workers)
.claude/skills/                architect  evaluate  compact-state
.agent/models.env  .agent/commands.env  .agent/envelope.schema.json
.agent/ARCHITECT.md            written in Phase A–D, then locked
.agent/CURRENT_STATE.md  .agent/NEXT_STATE.md
.agent/{adr,packets,results,eval}/
.agent/protocol/               roles architect lenses archetypes design-visual design-ux
                               state-files packets evaluation compaction bootstrap
.agent/templates/playwright.config.ts
scripts/agent/                 boot link lock verify-lock budget accept
scripts/eval/                  lint-banned lint-spacing lint-motion palette.ts score.sh rules/
```

## Commit prefixes

For this configured overhaul all commits go through accept.sh with T-nnn prefix, including documentation/architecture metadata. Old kit arch/eval/checkpoint/fix(orch) examples do not authorize a direct git commit. State preparation for its own acceptance is allowed under state-files.md.
