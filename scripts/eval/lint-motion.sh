#!/usr/bin/env bash
# Motion lint (check A-7, static part). Exit 1 on any hit.
set -u
bad=0
if rg -nP "transition:\s*all\b|transition-all" src; then echo "BANNED: transition: all"; bad=1; fi
if rg -nP "transition(-property)?:[^;]*\b(width|height|top|left|margin|box-shadow)\b" src; then
  echo "BANNED: animating layout or shadow properties"; bad=1
fi
if rg -qP "transition|animation|@keyframes" src && ! rg -q "prefers-reduced-motion" src; then
  echo "MISSING: no prefers-reduced-motion guard found"; bad=1
fi
exit $bad
