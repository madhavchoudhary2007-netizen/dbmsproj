#!/usr/bin/env bash
# Anti-AI-slop lint (check A-2). Exit 1 on any hit, 2 if no source directory exists.
set -u
. "$(dirname "$0")/_dirs.sh"
bad=0
chk() { if rg -nP "$2" $dirs; then echo "BANNED: $1"; bad=1; fi; }
chk "Inter/Roboto as font"  "font-family:\s*['\"]?(Inter|Roboto)"
chk "purple gradient"       "from-(purple|violet|fuchsia)-[0-9]+|linear-gradient\([^)]*#(7c3aed|8b5cf6|a855f7|6d28d9)"
chk "heavy shadow"          "shadow-(xl|2xl)"
chk "glassmorphism"         "backdrop-(filter|blur)"
chk "emoji icon"            "[\x{1F300}-\x{1FAFF}]"
chk "generic copy"          "(?i)unlock the power|seamless(ly)?|revolutioniz|supercharge|elevate your"
exit $bad
