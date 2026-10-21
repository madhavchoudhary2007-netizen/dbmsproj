#!/usr/bin/env bash
# Size budgets (1 token ~ 4 characters). Exit 1 if any budget is exceeded.
set -u
bad=0
tok() { [ -f "$1" ] || return 0; t=$(( $(wc -c < "$1") / 4 ))
  if [ "$t" -lt "$2" ]; then echo "ok   $1 ~$t tokens (max $2)"; else echo "OVER $1 ~$t tokens (max $2)"; bad=1; fi; }
chars() { [ -f "$1" ] || return 0; c=$(LC_ALL=C.UTF-8 wc -m < "$1")
  if [ "$c" -le "$2" ]; then echo "ok   $1 $c chars (max $2)"; else echo "OVER $1 $c chars (max $2)"; bad=1; fi; }
tok .agent/CURRENT_STATE.md 2000
tok .agent/NEXT_STATE.md 1500
chars AGENTS.md 12000   # Antigravity rule-file cap (reported); also keeps Codex's 32 KiB combined cap safe
exit $bad
