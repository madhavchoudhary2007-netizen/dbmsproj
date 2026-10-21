#!/usr/bin/env bash
# Unattended runner for the perfection loop on Codex.
# Starts a fresh `codex exec` session each time; continuity comes from the state files, not chat history.
# Stops when .agent/FINAL_REPORT.md has a verdict, after MAX sessions, or when 3 sessions in a row make no commit.
# Usage: bash scripts/agent/run-loop.sh [max_sessions]
set -u
max=${1:-40}
log=.agent/loop-runs.log
mkdir -p .agent
kick='Start the perfection loop: read .agent/protocol/perfection-loop.md completely and follow it exactly, beginning with Phase 0.'
resume='Resume the perfection loop: read .agent/protocol/perfection-loop.md completely, run its Resume section, then continue exactly as it says.'
stalls=0
for i in $(seq 1 "$max"); do
  if [ -f .agent/FINAL_REPORT.md ] && head -1 .agent/FINAL_REPORT.md | grep -Eq '^Verdict: (DONE|ESCALATED)$'; then
    echo "finished: $(head -1 .agent/FINAL_REPORT.md)"; exit 0
  fi
  prompt=$resume; [ -f .agent/LOOP.md ] || prompt=$kick
  before=$(git rev-parse HEAD 2>/dev/null || echo none)
  echo "$(date -u +%FT%TZ) session $i start (head $before)" >> "$log"
  codex exec --sandbox workspace-write --approve-for-me "$prompt" >> "$log" 2>&1
  echo "$(date -u +%FT%TZ) session $i exit $?" >> "$log"
  after=$(git rev-parse HEAD 2>/dev/null || echo none)
  if [ "$before" = "$after" ]; then stalls=$((stalls + 1)); else stalls=0; fi
  if [ "$stalls" -ge 3 ]; then echo "stopped: 3 sessions in a row made no commit; see $log"; exit 1; fi
  sleep 30
done
echo "stopped: $max sessions without a final verdict; see $log"; exit 1
