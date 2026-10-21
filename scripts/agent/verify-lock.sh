#!/usr/bin/env bash
# Fail if ARCHITECT.md is unlocked or was modified after locking.
set -euo pipefail
F=.agent/ARCHITECT.md
grep -q '^> STATUS: LOCKED$' "$F" || { echo "ARCHITECT.md is not locked"; exit 1; }
want=$(grep '^> SHA256:' "$F" | awk '{print $3}')
have=$(awk 'f{print} /^<!-- LOCK:END -->$/{f=1}' "$F" | sha256sum | cut -d' ' -f1)
[ "$want" = "$have" ] || { echo "ARCHITECT.md modified after lock: $want != $have"; exit 1; }
echo "lock ok $have"
