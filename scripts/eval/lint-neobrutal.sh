#!/usr/bin/env bash
# Radius-only foundation for ADR-007. Exit 1 for violations, 2 for bad inputs.
set -u
root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root"
if [ "${1:-}" = "--self-test" ]; then
  set -- --self-test "$(dirname "$0")/rules/radius.good.css" "$(dirname "$0")/rules/radius.bad.css"
elif [ "$#" -eq 0 ]; then
  . scripts/eval/_dirs.sh || exit 2
  read -r -a files <<< "$dirs"
  set -- --scan "${files[@]}"
else
  set -- --scan "$@"
fi
python3 - "$@" <<'PY'
import os, re, sys
from pathlib import Path

allowed = re.compile(r"^(?:0(?:px)?|9999px|var\(--radius-(?:none|full)\))$", re.I)
css_radius = re.compile(r"\b(?:border-radius|border-(?:top|right|bottom|left|start|end)(?:-[a-z]+)?-radius)\s*:\s*([^;{}]+)", re.I)
js_radius = re.compile(r"(?<![\w$])(?:\"(?:borderRadius|border(?:TopLeft|TopRight|BottomLeft|BottomRight|StartStart|StartEnd|EndStart|EndEnd)Radius)\"|'(?:borderRadius|border(?:TopLeft|TopRight|BottomLeft|BottomRight|StartStart|StartEnd|EndStart|EndEnd)Radius)'|(?:borderRadius|border(?:TopLeft|TopRight|BottomLeft|BottomRight|StartStart|StartEnd|EndStart|EndEnd)Radius))\s*:\s*([^,;}\n]+)")
tw_radius = re.compile(r"(?<![\w-])(?:[\w-]+:)*rounded(?:-[\w./%]+|\[[^\]\s]+\])?")
extensions = {".css", ".scss", ".sass", ".js", ".jsx", ".ts", ".tsx", ".html", ".vue", ".svelte"}
skip = {"node_modules", ".next", "dist", "build", "vendor", "coverage", "generated"}

def check(text, css=False):
    chars = list(text); i = 0; quote = ""
    while i < len(chars):
        c = chars[i]
        if quote:
            if c == "\\": i += 2; continue
            if c == quote: quote = ""
        elif c in "'\"`": quote = c
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2); end = len(text) if end < 0 else end + 2
            for j in range(i, end):
                if chars[j] != "\n": chars[j] = " "
            i = end; continue
        elif not css and text.startswith("//", i):
            end = text.find("\n", i + 2); end = len(text) if end < 0 else end
            for j in range(i, end): chars[j] = " "
            i = end; continue
        i += 1
    clean = "".join(chars); hits = []
    for m in css_radius.finditer(clean):
        vals = re.split(r"\s+", m.group(1).strip())
        if not vals or any(not allowed.fullmatch(v.strip("'\"")) for v in vals): hits.append((m.start(), "CSS radius"))
    for m in js_radius.finditer(clean):
        v = m.group(1).strip().strip("'\" ")
        if v.isdigit(): v += "px"
        if not allowed.fullmatch(v): hits.append((m.start(), "JS radius"))
    for m in tw_radius.finditer(clean):
        if m.group(0).split(":")[-1] not in ("rounded-none", "rounded-full"):
            hits.append((m.start(), "Tailwind radius"))
    return sorted(hits)

def self_test(good, bad):
    g, b = check(good.read_text()), check(bad.read_text())
    css = ".x { background:url(https://example.invalid/image.png); border-radius:8px; }"
    controls = check("const x = { borderTopWidth: 4 }; const r = 'https://host';\n/*a\n b*/\n.el { border-radius: 8px; }")
    js = check("const a = { borderRadius: 0, borderTopLeftRadius: 9999, \"borderBottomLeftRadius\": 8 }; const b = { borderBottomRightRadius: 8 };")
    if g or not any(x[1] == "CSS radius" for x in b) or not any(x[1] == "Tailwind radius" for x in b): return False
    return bool(check(css, css=True)) and not any(x[1] == "JS radius" for x in controls) and any(x[1] == "CSS radius" and 1 + controls_text.count("\n", 0, x[0]) == 4 for x in controls) and len(js) == 2 and all(x[1] == "JS radius" for x in js)

if sys.argv[1] == "--self-test":
    if len(sys.argv) != 4: raise SystemExit(2)
    controls_text = "const x = { borderTopWidth: 4 }; const r = 'https://host';\n/*a\n b*/\n.el { border-radius: 8px; }"
    if not self_test(Path(sys.argv[2]), Path(sys.argv[3])):
        print("SELF-TEST FAILED: radius controls or comment line positions are wrong", file=sys.stderr); raise SystemExit(1)
    print("SELF-TEST PASSED: fixtures, CSS, Tailwind, JS values, comments and URLs")
    raise SystemExit(0)

if sys.argv[1] != "--scan": raise SystemExit(2)
paths = []
for raw in sys.argv[2:]:
    p = Path(raw)
    if p.is_file(): paths.append(p)
    elif p.is_dir():
        for base, dirs, names in os.walk(p):
            dirs[:] = [d for d in dirs if d not in skip]
            paths.extend(Path(base) / n for n in names)
    else: print(f"LINT ERROR: file not found: {p}", file=sys.stderr); raise SystemExit(2)
bad = 0
for p in paths:
    if p.suffix.lower() not in extensions or any(x in p.parts for x in skip): continue
    try: text = p.read_text(errors="replace")
    except OSError as e: print(f"LINT ERROR: cannot read {p}: {e}", file=sys.stderr); raise SystemExit(2)
    for pos, rule in check(text, css=p.suffix.lower() in {".css", ".scss", ".sass"}):
        print(f"{p}:{1 + text.count(chr(10), 0, pos)}: {rule} must use 0, 9999px, var(--radius-none), or var(--radius-full)")
        bad = 1
raise SystemExit(bad)
PY
