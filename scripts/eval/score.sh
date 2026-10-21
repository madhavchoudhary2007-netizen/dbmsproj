#!/usr/bin/env bash
# Aggregate the four dimension files into .agent/eval/score.json. Exit 0 only if presentable.
# passed: true | false | null (NOT_RUN: excluded from the denominator, listed under not_run).
set -euo pipefail
cd .agent/eval
pct() { jq '([.checks[]|select(.passed==true)|.weight]|add//0) as $p
            | ([.checks[]|select(.passed!=null)|.weight]|add//0) as $a
            | if $a==0 then 0 else 100*$p/$a end' "$1.json"; }
F=$(pct functional); A=$(pct aesthetic); P=$(pct performance); E=$(pct edge)
FILES="functional.json aesthetic.json performance.json edge.json"
G=$(jq -s '[.[].checks[] | select(.id|IN("F-1","F-3","F-4","F-5","P-6")) | select(.passed!=true) | .id]' $FILES)
N=$(jq -s '[.[].checks[] | select(.passed==null) | .id]' $FILES)
jq -n --argjson f "$F" --argjson a "$A" --argjson p "$P" --argjson e "$E" --argjson g "$G" --argjson n "$N" \
  '{functional:$f, aesthetic:$a, performance:$p, edge:$e,
    aggregate:(0.30*$f + 0.25*$a + 0.25*$p + 0.20*$e), failed_gates:$g, not_run:$n}
   | .presentable = (.aggregate >= 95 and (.failed_gates|length) == 0)' | tee score.json
jq -e .presentable score.json >/dev/null
