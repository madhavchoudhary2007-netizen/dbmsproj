#!/usr/bin/env bash
# Spacing scale lint (check A-1). Legal px values: 4 8 12 16 24 32 48 64 (and 0). Exit 1 on any hit.
set -u
bad=0
if rg -nP "(margin|padding|gap|inset|top|left|right|bottom)[a-z-]*:[^;{}]*?(?<![\w.])(?!(?:4|8|12|16|24|32|48|64)px\b)[1-9]\d*(?:\.\d+)?px" src --glob '*.css'; then
  echo "BANNED: pixel spacing outside the scale (css)"; bad=1
fi
if rg -nP "\b(p|m|gap|space-[xy]|inset|top|left|right|bottom)[trblxy]?-\[\d+px\]" src; then
  echo "BANNED: tailwind arbitrary pixel spacing"; bad=1
fi
exit $bad
