#!/usr/bin/env bash
# Aggregate validated dimension evidence. NOT_RUN remains a failed denominator entry.
set -euo pipefail
cd .agent/eval
validate() {
  jq -e --arg dim "$1" '
    {functional:{"F-1":3,"F-2":2,"F-3":4,"F-4":6,"F-5":3,"F-6":2,"F-7":2,"F-8":2,"F-9":1},
     aesthetic:{"A-1":2,"A-2":2,"A-3":2,"A-4":2,"A-5":3,"A-6":2,"A-7":2},
     performance:{"P-1":3,"P-2":3,"P-3":2,"P-4":3,"P-5":2,"P-6":2},
     edge:{"E-1":3,"E-2":4,"E-3":2,"E-4":2,"E-5":2}}[$dim] as $expected
    | (.checks | type == "array") and
      ([.checks[].id] as $ids | ($ids|length) == ($expected|length) and (($ids|unique|length) == ($ids|length))) and
      ([.checks[] | select(($expected[.id] != null) and ($expected[.id] == .weight) and
        (.passed == true or .passed == false or .passed == null) and (.detail|type=="string"))] | length == ($expected|length))
  ' "$1.json" >/dev/null || { echo "invalid $1.json: expected each check ID once with exact weight and valid evidence" >&2; return 1; }
}
for dim in functional aesthetic performance edge; do validate "$dim"; done
pct() { jq '([.checks[]|select(.passed==true)|.weight]|add//0) as $p | ([.checks[].weight]|add//0) as $a | 100*$p/$a' "$1.json"; }
F=$(pct functional); A=$(pct aesthetic); P=$(pct performance); E=$(pct edge)
FILES="functional.json aesthetic.json performance.json edge.json"
G=$(jq -s '[.[].checks[]|select(.id|IN("F-1","F-2","F-3","F-4","F-5","P-6"))|select(.passed!=true)|.id]' $FILES)
N=$(jq -s '[.[].checks[]|select(.passed==null)|.id]' $FILES)
jq -n --argjson f "$F" --argjson a "$A" --argjson p "$P" --argjson e "$E" --argjson g "$G" --argjson n "$N" \
  '{functional:$f,aesthetic:$a,performance:$p,edge:$e,aggregate:(0.30*$f+0.25*$a+0.25*$p+0.20*$e),failed_gates:$g,not_run:$n}
   | .presentable=(.aggregate>=95 and (.failed_gates|length)==0 and (.not_run|length)==0)' | tee score.json
jq -e .presentable score.json >/dev/null
