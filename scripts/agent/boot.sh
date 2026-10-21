#!/usr/bin/env bash
# Session boot checks.
# Usage: source .agent/models.env && bash scripts/agent/boot.sh [--probe]
set -euo pipefail
: "${HARNESS:?run: source .agent/models.env first}"
fail() { echo "BOOT FAIL: $*" >&2; exit 1; }

if [ "${1:-}" = "--probe" ]; then   # optional one-token reachability check; uses a little quota
  case "$HARNESS" in
    claude) claude -p "reply OK" --model "$ORCH_MODEL" --effort "$ORCH_EFFORT" >/dev/null \
         && claude -p "reply OK" --model "$WORKER_MODEL" --effort "$WORKER_EFFORT" >/dev/null ;;
    codex)  codex exec --model "$ORCH_MODEL" "reply OK" >/dev/null && codex exec --model "$WORKER_MODEL" "reply OK" >/dev/null ;;
    gemini) gemini -m "$ORCH_MODEL" -p "reply OK" >/dev/null ;;
    antigravity) echo "verify the models in the Antigravity model picker" ;;
    *) fail "unknown HARNESS: $HARNESS" ;;
  esac
fi

if [ "$HARNESS" = "claude" ]; then
  [ -z "${CLAUDE_CODE_EFFORT_LEVEL:-}" ] || fail "CLAUDE_CODE_EFFORT_LEVEL is set; it overrides every effort level. Unset it."
  [ -z "${CLAUDE_CODE_SUBAGENT_MODEL_FORCE:-}" ] || fail "CLAUDE_CODE_SUBAGENT_MODEL_FORCE is set; it overrides worker models. Unset it."
  for f in w1-ui w2-state w3-eval; do
    grep -q "^model: $WORKER_MODEL$" ".claude/agents/$f.md" \
      && grep -q "^effort: $WORKER_EFFORT$" ".claude/agents/$f.md" \
      || fail "$f frontmatter does not match models.env"
  done
  jq -e --arg m "$ORCH_MODEL" --arg e "$ORCH_EFFORT" \
    '.model == $m and .effortLevel == $e and (((.env // {}) | has("CLAUDE_CODE_EFFORT_LEVEL")) | not)' \
    .claude/settings.json >/dev/null || fail ".claude/settings.json does not match models.env"
  jq -e --arg n "$MAX_WORKERS" '.env.CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS == $n' .claude/settings.json >/dev/null \
    || fail "settings.json env.CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS must be \"$MAX_WORKERS\""
  jq -e --argjson w "$CONTEXT_WINDOW" --arg s "$CONTEXT_WINDOW" \
    '.autoCompactWindow == $w and .env.CLAUDE_CODE_AUTO_COMPACT_WINDOW == $s' .claude/settings.json >/dev/null \
    || fail "settings.json autoCompactWindow and env.CLAUDE_CODE_AUTO_COMPACT_WINDOW must equal CONTEXT_WINDOW ($CONTEXT_WINDOW)"
fi

if [ "$HARNESS" = "codex" ]; then
  for f in w1-ui w2-state w3-eval; do
    grep -q "^model = \"$WORKER_MODEL\"" ".codex/agents/$f.toml" \
      && grep -q "^model_reasoning_effort = \"$WORKER_EFFORT\"" ".codex/agents/$f.toml" \
      || fail ".codex/agents/$f.toml does not match models.env"
  done
  cfg="${CODEX_HOME:-$HOME/.codex}/config.toml"
  if [ -f "$cfg" ]; then
    grep -Eq "^(max_concurrent_threads_per_session|max_threads) *= *$MAX_WORKERS\b" "$cfg" \
      || fail "$cfg lacks [agents] max_concurrent_threads_per_session = $MAX_WORKERS"
    grep -Eq "^model_auto_compact_token_limit *= *$CONTEXT_WINDOW\b" "$cfg" \
      || fail "$cfg lacks model_auto_compact_token_limit = $CONTEXT_WINDOW"
  else
    echo "WARN: $cfg not found; merge .agent/templates/codex-config.toml into it"
  fi
fi

if [ "$HARNESS" = "antigravity" ] || [ "$HARNESS" = "gemini" ]; then
  echo "NOTE: model, thinking level and the $MAX_WORKERS-subagent cap are instruction-only here; confirm them in the UI."
fi

if [ -f .agent/ARCHITECT.md ]; then
  bash scripts/agent/verify-lock.sh || fail "architecture lock check failed"
else
  echo "No architecture yet: read .agent/protocol/architect.md"
fi
bash scripts/agent/budget.sh || fail "size budget exceeded"
test -z "$(git status --porcelain -- src app lib server 2>/dev/null)" || echo "WARN: uncommitted product changes; reconcile before dispatching"
echo "boot OK"
