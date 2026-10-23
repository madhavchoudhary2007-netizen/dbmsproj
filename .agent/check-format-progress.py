"""Atomic formatting verification; parent Ruff zero-error gates remain required."""
import ast
import difflib
import pathlib
import subprocess
import sys

path = sys.argv[1]
current = pathlib.Path(path).read_text()
baseline = subprocess.check_output(["git", "show", "HEAD:" + path], text=True)

def canonical(source):
    result = subprocess.run(
        [".venv/bin/ruff", "format", "--stdin-filename", path, "-"],
        input=source, text=True, capture_output=True, check=True,
    )
    return result.stdout.splitlines()

def distance(source, formatted):
    return sum(
        (i2 - i1) + (j2 - j1)
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            a=source.splitlines(), b=formatted, autojunk=False
        ).get_opcodes() if tag != "equal"
    )

assert ast.dump(ast.parse(current)) == ast.dump(ast.parse(baseline)), "AST changed"
formatted = canonical(baseline)
assert canonical(current) == formatted, "Changed canonical contents"
before, after = distance(baseline, formatted), distance(current, formatted)
assert after < before, (before, after)
stats = subprocess.check_output(["git", "diff", "--numstat", "--", path], text=True)
assert sum(int(n) for row in stats.splitlines() for n in row.split()[:2]) <= 150
print(f"{path}: format distance {before} -> {after}; AST/canonical contents unchanged")
