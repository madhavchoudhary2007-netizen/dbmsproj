# Context compaction and re-seeding

Read when: right after a compaction, and when a session is ending.

**Compaction happens once, automatically, at `CONTEXT_WINDOW` (400k tokens). There are no earlier thresholds at 260k or 340k, and the orchestrator does not compact on its own before 400k.** Settings: Claude Code `autoCompactWindow` and `env.CLAUDE_CODE_AUTO_COMPACT_WINDOW` in `.claude/settings.json`; Codex `model_auto_compact_token_limit` in `~/.codex/config.toml`; Antigravity has no documented setting, so start a new conversation yourself when it slows or loses track.

Because the automatic compact gives no warning, state must already be on disk: update `CURRENT_STATE.md` and `NEXT_STATE.md` after every accepted envelope and commit (`state-files.md`), so nothing depends on a final sync. Keep in-flight work recoverable: a packet file for every dispatched task.

## After a compaction

1. **Re-seed.** First actions:
   ```bash
   source .agent/models.env && bash scripts/agent/boot.sh
   cat .agent/ARCHITECT.md        # if over 100 lines read in ranges of at most 100, contracts and lenses first
   cat .agent/CURRENT_STATE.md .agent/NEXT_STATE.md
   git log --oneline -10 && git status --short
   ```
   Anything the compaction summary retains is non-authoritative; the state files override it. Confirm `git_head` in CURRENT_STATE equals `git rev-parse --short HEAD`; on a mismatch reconcile from `git log` before dispatching anything.
2. **Recover in-flight work.** For each packet in `.agent/packets/` with no matching `.agent/results/<id>.json`, re-dispatch it (a worker that was running is gone). Run `accept.sh` on any envelope that did return.
3. **Sync the state files** if the git log shows merged work they do not record, then run `bash scripts/agent/budget.sh` and `verify-lock.sh`; condense per `state-files.md` if over budget.
4. **Checkpoint commit:** `git add .agent && git commit -m "checkpoint: after compaction head=$(git rev-parse --short HEAD)"`
5. Resume the queue from the top of `NEXT_STATE.md`.

Manual compaction (only if the user asks): Claude Code `/compact Re-seed only from .agent/ARCHITECT.md, .agent/CURRENT_STATE.md, .agent/NEXT_STATE.md`; Codex `/compact`; Gemini CLI `/compress`; Antigravity new conversation.

Between unrelated milestones prefer `/clear` (Claude Code) or a new conversation and re-seed the same way; it is cheaper than a summary.
