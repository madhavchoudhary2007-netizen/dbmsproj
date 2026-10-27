#!/usr/bin/env bash
# Accept a worker result after checking its approved scope and verification command.
set -euo pipefail

id=${1:?usage: accept.sh T-nnn}
[[ "$id" =~ ^T-[0-9]{3,}$ ]] || { echo "invalid task id: $id" >&2; exit 1; }
env_file=.agent/results/$id.json
packet_file=.agent/packets/$id.md
state_file=.agent/NEXT_STATE.md
[[ -f $env_file && -f $packet_file && -f $state_file ]] || {
  echo "missing acceptance input for $id" >&2
  exit 1
}

# Use the already-installed validator without allowing npx to fetch packages.
npx --no-install ajv-cli validate -s .agent/envelope.schema.json -d "$env_file" --spec=draft2020 >/dev/null

tmpdir=$(mktemp -d)
trap 'rm -f "$tmpdir/metadata" "$tmpdir/index" "$tmpdir/index.lock"; rmdir "$tmpdir"' EXIT
python3 - "$id" "$env_file" "$packet_file" "$state_file" "$tmpdir/metadata" <<'PY'
import json
import re
import sys

task_id, envelope_path, packet_path, state_path, output_path = sys.argv[1:]

def fail(message):
    raise SystemExit(message)

with open(envelope_path, encoding="utf-8") as stream:
    envelope = json.load(stream)
if envelope.get("task_id") != task_id:
    fail("envelope task_id does not match requested task")
if envelope.get("status") != "PASSED":
    fail("task result status must be PASSED")
verification = envelope.get("verification")
if not isinstance(verification, dict) or type(verification.get("exit_code")) is not int or verification["exit_code"] != 0:
    fail("envelope verification exit_code must be 0")
reported_command = verification.get("command")
if not isinstance(reported_command, str) or not reported_command:
    fail("envelope verification command is missing")

with open(packet_path, encoding="utf-8") as stream:
    packet = stream.read()
sections = []
lines = packet.splitlines()
for index, line in enumerate(lines):
    if line in ("## Verify", "## Approved Verify"):
        body = []
        for following in lines[index + 1:]:
            if following.startswith("## "):
                break
            body.append(following)
        sections.append(body)
if len(sections) != 1:
    fail("approved Verify command is missing or ambiguous")
body = [line.strip() for line in sections[0] if line.strip()]
if not body:
    fail("approved Verify command is empty")
if body[0] in ("```bash", "```sh"):
    if len(body) != 3 or body[2] != "```":
        fail("approved Verify code fence must contain exactly one command")
    approved_command = body[1]
elif len(body) == 1 and not body[0].startswith("```"):
    approved_command = body[0]
else:
    fail("approved Verify must contain exactly one literal command")
if reported_command != approved_command:
    fail("envelope Verify command does not exactly match approved command")

with open(state_path, encoding="utf-8") as stream:
    state = stream.read()
task_sections = re.findall(
    rf"(?ms)^### {re.escape(task_id)}(?:\s|$)(.*?)(?=^### |\Z)", state
)
if len(task_sections) != 1:
    fail("task section is missing or ambiguous in NEXT_STATE.md")
target_lines = re.findall(r"(?m)^- target_files:\s*(.*)$", task_sections[0])
if len(target_lines) != 1 or not target_lines[0].strip():
    fail("target_files list is missing or empty")

def valid_path(path):
    if not path or path.startswith("/") or "\\" in path or "," in path:
        return False
    if any(ord(char) < 32 or ord(char) == 127 for char in path):
        return False
    parts = path.split("/")
    return all(part not in ("", ".", "..") and part.lower() != ".git" for part in parts)

targets = [item.strip() for item in target_lines[0].split(",")]
if not targets or any(not valid_path(path) for path in targets) or len(set(targets)) != len(targets):
    fail("target_files contains an unsafe, empty, or duplicate path")
modified = envelope.get("files_modified")
if not isinstance(modified, list):
    fail("files_modified must be an array")
for item in modified:
    if not isinstance(item, dict) or not isinstance(item.get("path"), str):
        fail("files_modified contains an invalid path entry")
    path = item["path"]
    if not valid_path(path) or path not in targets:
        fail(f"files_modified path is unsafe or outside target_files: {path}")

summary = envelope.get("diff_summary", "")
if not isinstance(summary, str):
    fail("diff_summary must be a string")
summary = " ".join(summary.split())[:72]
with open(output_path, "w", encoding="utf-8") as stream:
    stream.write(approved_command + "\n")
    stream.write(summary + "\n")
    for path in targets:
        stream.write(path + "\n")
PY

metadata=()
while IFS= read -r line; do
  metadata+=("$line")
done < "$tmpdir/metadata"
approved_command=${metadata[0]}
summary=${metadata[1]}
targets=("${metadata[@]:2}")
((${#targets[@]} > 0)) || { echo "no allowed target paths" >&2; exit 1; }

# Run only the command recorded in the packet, after all envelope checks.
bash -c "$approved_command"

# A separate index lets the task commit coexist with unrelated staged work.
for path in "${targets[@]}"; do
  [[ ! -d $path ]] || { echo "target must name a file, not a directory: $path" >&2; exit 1; }
done
head=$(git rev-parse --verify HEAD)
index_file=$tmpdir/index
GIT_INDEX_FILE=$index_file git read-tree "$head"
pathspecs=()
for path in "${targets[@]}"; do
  pathspecs+=(":(literal)$path")
done
GIT_INDEX_FILE=$index_file git add -A -- "${pathspecs[@]}"
if GIT_INDEX_FILE=$index_file git diff --cached --quiet; then
  echo "no task changes to commit" >&2
  exit 1
fi
GIT_INDEX_FILE=$index_file git commit -m "$id: $summary"
commit=$(git rev-parse --verify HEAD)
# Bring only the accepted entries in the real index up to the new HEAD.
git reset -q "$commit" -- "${pathspecs[@]}"
