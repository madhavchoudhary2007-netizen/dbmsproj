#!/usr/bin/env bash
# Unattended runner for the perfection loop on Codex.
# Starts a fresh `codex exec` session each time; continuity comes from the state files, not chat history.
# Stops when: .agent/FINAL_REPORT.md has a verdict; MAX sessions ran; 2 sessions in a row exited non-zero
# (a bad flag, login or model will not fix itself); or 3 sessions in a row made no commit.
# Usage: bash scripts/agent/run-loop.sh [max_sessions]
set -u
max=${1:-40}
log=.agent/loop-runs.log
mkdir -p .agent
kick='Start the perfection loop: read .agent/protocol/perfection-loop.md completely and follow it exactly, beginning with Phase 0.'
resume='Resume the perfection loop: read .agent/protocol/perfection-loop.md completely, run its Resume section, then continue exactly as it says.'
command -v codex >/dev/null || { echo "codex not found in PATH"; exit 1; }
# Pick exec flags from the installed Codex. --approve-for-me already implies the workspace-write sandbox
# (passing --sandbox with it is rejected by codex 0.160.1); older builds get an explicit sandbox instead.
if codex exec --help 2>&1 | grep -q -- '--approve-for-me'; then flags="--approve-for-me"
else flags="--sandbox workspace-write"; fi
echo "codex flags: $flags"
if ! out=$(codex exec $flags "reply OK" 2>&1); then
  echo "preflight failed: codex exec $flags"; echo "$out" | tail -n 20; exit 1
fi
show_tail() { echo "--- last 25 lines of $log ---"; tail -n 25 "$log"; }
stalls=0; fails=0
for i in $(seq 1 "$max"); do
  if [ -f .agent/FINAL_REPORT.md ] && head -1 .agent/FINAL_REPORT.md | grep -Eq '^Verdict: (DONE|ESCALATED)$'; then
    echo "finished: $(head -1 .agent/FINAL_REPORT.md)"; exit 0
  fi
  prompt=$resume; [ -f .agent/LOOP.md ] || prompt=$kick
  before=$(git rev-parse HEAD 2>/dev/null || echo none)
  echo "$(date -u +%FT%TZ) session $i start (head $before)" >> "$log"
  codex exec $flags "$prompt" >> "$log" 2>&1
  rc=$?
  echo "$(date -u +%FT%TZ) session $i exit $rc" >> "$log"
  after=$(git rev-parse HEAD 2>/dev/null || echo none)
  if [ "$rc" -ne 0 ]; then fails=$((fails + 1)); else fails=0; fi
  if [ "$before" = "$after" ]; then stalls=$((stalls + 1)); else stalls=0; fi
  if [ "$fails" -ge 2 ]; then echo "stopped: 2 sessions in a row exited non-zero (last exit $rc)"; show_tail; exit 1; fi
  if [ "$stalls" -ge 3 ]; then echo "stopped: 3 sessions in a row made no commit"; show_tail; exit 1; fi
  sleep 30
done
echo "stopped: $max sessions without a final verdict"; show_tail; exit 1
