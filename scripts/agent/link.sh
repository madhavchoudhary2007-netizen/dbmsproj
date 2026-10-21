#!/usr/bin/env bash
# One-time repo setup: CLAUDE.md symlink, working directories, executable scripts.
set -euo pipefail
ln -sf AGENTS.md CLAUDE.md
mkdir -p .agent/packets .agent/results .agent/eval .agent/adr
chmod +x scripts/agent/*.sh scripts/eval/*.sh
echo "linked. Gemini CLI: set its context file name to AGENTS.md. Do not create GEMINI.md if you also use Antigravity."
