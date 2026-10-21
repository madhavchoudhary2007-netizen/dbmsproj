#!/usr/bin/env bash
# Accept a worker result. Usage: bash scripts/agent/accept.sh T-021
# Validates the envelope, re-runs the verify command, checks file boundaries, commits on PASSED.
set -euo pipefail
id=${1:?usage: accept.sh T-nnn}
env=.agent/results/$id.json
npx --yes ajv-cli validate -s .agent/envelope.schema.json -d "$env" --spec=draft2020 >/dev/null
bash -c "$(jq -r .verification.command "$env")"          # never trust the reported result
allowed=$(awk -v id="$id" '$0 ~ "^### "id" "{f=1;next} /^### /{f=0} f' .agent/NEXT_STATE.md \
  | sed -n 's/^- target_files: //p' | tr ',' '\n' | sed 's/^ *//; s/ *$//')
[ -n "$allowed" ] || { echo "no target_files found for $id in NEXT_STATE.md"; exit 1; }
for f in $(git ls-files -m -o --exclude-standard | grep -v '^\.agent/'); do
  echo "$allowed" | grep -qx "$f" || { echo "boundary violation: $f"; exit 1; }
done
if [ "$(jq -r .status "$env")" = PASSED ]; then
  git add -A && git commit -m "$id: $(jq -r .diff_summary "$env" | cut -c1-72)"
else
  echo "$id reported FAILED; nothing committed"; exit 1
fi
