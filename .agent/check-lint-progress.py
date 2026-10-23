"""Atomic AST-preserving lint progress; full parent zero-error gate stays required."""
import ast
import json
import pathlib
import re
import subprocess
import sys

path, rules = sys.argv[1:3]
current = pathlib.Path(path).read_text()
baseline = subprocess.check_output(["git", "show", "HEAD:" + path], text=True)
assert ast.dump(ast.parse(current)) == ast.dump(ast.parse(baseline)), "AST changed"
pattern = r"#.*(?:noqa|type:\s*ignore).*"
assert re.findall(pattern, current) == re.findall(pattern, baseline), "Directives changed"

def count(source):
    result = subprocess.run(
        [".venv/bin/ruff", "check", "--select", rules, "--output-format", "json",
         "--stdin-filename", path, "-"],
        input=source, text=True, capture_output=True,
    )
    assert result.returncode in (0, 1), result.stderr
    return len(json.loads(result.stdout))

before, after = count(baseline), count(current)
assert after < before, (before, after)
stats = subprocess.check_output(["git", "diff", "--numstat", "--", path], text=True)
assert sum(int(n) for row in stats.splitlines() for n in row.split()[:2]) <= 150
subprocess.run([".venv/bin/ruff", "format", "--check", path], check=True)
print(f"{path}: {rules} findings {before} -> {after}; AST/directives unchanged")
