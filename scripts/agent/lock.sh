#!/usr/bin/env bash
# Prepend the lock banner to .agent/ARCHITECT.md with the SHA-256 of the body, then commit.
set -euo pipefail
F=.agent/ARCHITECT.md
body=$(awk 'f{print} /^<!-- LOCK:END -->$/{f=1}' "$F")
[ -z "$body" ] && body=$(cat "$F")          # first lock: no banner yet
hash=$(printf '%s\n' "$body" | sha256sum | cut -d' ' -f1)
{
  echo '<!-- LOCK:BEGIN -->'
  echo '> STATUS: LOCKED'
  echo "> SHA256: $hash"
  echo "> LOCKED_AT: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo '> LOCKED_BY: orchestrator'
  echo '<!-- LOCK:END -->'
  printf '%s\n' "$body"
} > "$F.tmp" && mv "$F.tmp" "$F"
git add "$F" && git commit -m "arch: lock ARCHITECT.md ($hash)"
