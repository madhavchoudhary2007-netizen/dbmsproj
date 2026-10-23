import re
import sys
from pathlib import Path

from scripts.eval.source_text import mask_comments

_TIME = re.compile(r"(?:\d+(?:\.\d+)?|\.\d+)(ms|s)\Z", re.I)
_RULE = re.compile(r"(?P<header>[^{}]+)\{(?P<body>[^{}]*)\}")
_PROPERTY = re.compile(r"(?:^|;)\s*([-\w]+)\s*:\s*([^;{}]*)")
_ALLOWED = {"transform", "opacity", "background-color"}
_INVALID = "invalid transition: use an allowed property and 100–300ms, or none"
_EASING = {"ease-out", "linear", "cubic-bezier(0.2,0,0,1)"}


def _mask_strings(text: str) -> str:
    chars = list(text)
    quote = ""
    escaped = False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            if quote:
                chars[index] = " "
        elif quote and char == "\\":
            escaped = True
        elif quote and char == quote:
            quote = ""
            chars[index] = " "
        elif not quote and char in "'\"`":
            quote = char
            chars[index] = " "
        elif quote and char != "\n":
            chars[index] = " "
    return "".join(chars)


def _transitions(value: str) -> list[str]:
    items, depth, start = [], 0, 0
    for index, char in enumerate(value):
        depth += (char == "(") - (char == ")")
        if char == "," and depth == 0:
            items.append(value[start:index])
            start = index + 1
    items.append(value[start:])
    return items


def _milliseconds(token: str) -> float | None:
    match = _TIME.fullmatch(token)
    if not match:
        return None
    value = float(token[:-2] if match[1].lower() == "ms" else token[:-1])
    return value * 1000 if match[1].lower() == "s" else value


def _valid_transition(value: str) -> bool:
    value = re.sub(r"\s*!important\s*$", "", value, flags=re.I)
    for item in _transitions(value):
        item = re.sub(
            r"cubic-bezier\s*\(\s*([^)]*)\)",
            lambda m: "cubic-bezier(" + re.sub(r"\s+", "", m[1]) + ")",
            item,
            flags=re.I,
        )
        tokens = item.lower().split()
        if tokens == ["none"]:
            continue
        if len(tokens) < 2 or tokens[0] not in _ALLOWED:
            return False
        duration = _milliseconds(tokens[1])
        if duration is None or not 100 <= duration <= 300:
            return False
        tail = tokens[2:]
        if tail and tail[0] in _EASING:
            tail = tail[1:]
        if tail:
            delay = _milliseconds(tail[0]) if len(tail) == 1 else None
            if delay is None or delay != 0 and not 100 <= delay <= 300:
                return False
    return True


def check_motion(text: str, css: bool = False) -> list[tuple[int, str]]:
    if not css:
        return []
    masked = _mask_strings(mask_comments(text, css=True))
    has_guard = bool(
        re.search(r"@media[^{}]*prefers-reduced-motion\s*:\s*reduce(?=\s*[),])", masked, re.I)
    )
    errors: list[tuple[int, str]] = []
    moving: list[int] = []
    for rule in _RULE.finditer(masked):
        header = rule["header"].strip().replace(" ", "").lower()
        for declaration in _PROPERTY.finditer(rule["body"]):
            key, value = declaration[1].lower(), declaration[2].strip()
            if key not in {"transition", "transition-property"}:
                continue
            offset = rule.start("body") + declaration.start(1)
            none = re.sub(r"\s*!important\s*$", "", value, flags=re.I).lower() == "none"
            if not none:
                moving.append(offset)
            if key == "transition" and not _valid_transition(value):
                errors.append((offset, _INVALID))
            elif key == "transition-property":
                errors.append(
                    (offset, "transition-property requires a validated transition shorthand")
                )
            if ".nb-plinth::before" in header and not none:
                errors.append((offset, "plinth shadow transition is forbidden"))
    if moving and not has_guard:
        errors.append((moving[0], "motion requires a same-file prefers-reduced-motion guard"))
    return sorted(set(errors))


def self_test() -> None:
    root = Path(__file__).with_name("rules")
    good = (root / "motion.good.css").read_text()
    bad = (root / "motion.bad.css").read_text()
    if check_motion(good, css=True) != []:
        raise AssertionError("good motion fixture should have no findings")
    actual = check_motion(bad, css=True)
    expected = [
        (bad.index("transition: all"), _INVALID),
        (bad.index("transition: all"), "motion requires a same-file prefers-reduced-motion guard"),
        (bad.index("transition: box-shadow"), _INVALID),
        (bad.index("transition: transform"), "plinth shadow transition is forbidden"),
        (bad.index("transition: opacity 120ms banana"), _INVALID),
        (bad.index("transition: opacity 120ms 10s"), _INVALID),
    ]
    if actual != sorted(expected):
        raise AssertionError(f"bad motion fixture findings differ: {actual!r}")
    multiline = ".x {\n transition: opacity 99ms;\n}\n@media (prefers-reduced-motion: reduce) {}"
    if check_motion(multiline, css=True) != [(6, _INVALID)]:
        raise AssertionError("multiline transition offset changed")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] != "--self-test":
        raise SystemExit("usage: neo_motion.py --self-test")
    self_test()
