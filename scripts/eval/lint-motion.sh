#!/usr/bin/env bash
# Motion lint (check A-7, static part). Exit 1 on any hit, 2 if no source directory exists.
set -u
. "$(dirname "$0")/_dirs.sh"
bad=0
if rg -nP "transition:\s*all\b|transition-all" $dirs; then echo "BANNED: transition: all"; bad=1; fi
if rg -nP "transition(-property)?:[^;]*\b(width|height|top|left|margin|box-shadow)\b" $dirs; then
  echo "BANNED: animating layout or shadow properties"; bad=1
fi
if rg -qP "transition|animation|@keyframes" $dirs && ! rg -q "prefers-reduced-motion" $dirs; then
  echo "MISSING: no prefers-reduced-motion guard found"; bad=1
fi
exit $bad
