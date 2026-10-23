"""Reusable checks for forbidden visual effects in CSS and source text."""

import re
import sys
from pathlib import Path

from scripts.eval.source_text import mask_comments

PROPERTY = re.compile(
    r"(?P<key>['\"](?P<quoted>-webkit-backdrop-filter|-webkit-filter|"
    r"backdrop-filter|backdropFilter|filter)['\"]|"
    r"(?P<plain>-webkit-backdrop-filter|-webkit-filter|backdrop-filter|"
    r"backdropFilter|filter))\s*:",
    re.I,
)
BLUR_FUNCTION = re.compile(r"(?<![\w-])blur\s*\(", re.I)
TAILWIND_BLUR = re.compile(
    r"(?<![\w-])(?:[\w-]+:)*(?:backdrop-)?blur"
    r"(?:-(?:\[[^\]\s]+\]|[\w-]+))?(?![\w(-])"
)


def _inside_string(text: str, offset: int) -> bool:
    quote = ""
    escaped = False
    for char in text[:offset]:
        if escaped:
            escaped = False
        elif quote and char == "\\":
            escaped = True
        elif quote and char == quote:
            quote = ""
        elif not quote and char in "'\"`":
            quote = char
    return bool(quote)


def _style_function(value: str) -> bool:
    value = value.strip()
    if len(value) >= 2 and value[0] in "'\"" and value[-1] == value[0]:
        return bool(BLUR_FUNCTION.search(value[1:-1]))
    return any(not _inside_string(value, match.start()) for match in BLUR_FUNCTION.finditer(value))


def _property_follows(text: str, comma: int) -> bool:
    return bool(re.match(r"\s*(?:['\"][\w-]+['\"]|[\w-]+)\s*:", text[comma + 1 :]))


def _value_end(text: str, start: int) -> int:
    quote = ""
    depth = 0
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
        elif quote and char == "\\":
            escaped = True
        elif quote and char == quote:
            quote = ""
        elif not quote and char in "'\"`":
            quote = char
        elif not quote and char == "(":
            depth += 1
        elif not quote and char == ")":
            depth = max(0, depth - 1)
        elif (
            not quote
            and depth == 0
            and (char in ";}" or char == "," and _property_follows(text, index))
        ):
            return index
    return len(text)


def _expect(condition: bool) -> None:
    if not condition:
        raise AssertionError("blur rule self-test failed")


def check_blur(text: str, css: bool = False) -> list[tuple[int, str]]:
    """Return source offsets and reasons for disallowed blur effects."""
    clean = mask_comments(text, css=css)
    hits: list[tuple[int, str]] = []
    for match in PROPERTY.finditer(clean):
        key = match.group("key")
        start = match.start()
        prefix = clean[:start].rstrip()
        if key[0] in "'\"":
            if not prefix.endswith(("{", ",")):
                continue
        elif _inside_string(clean, start):
            continue
        value_start = match.end()
        value_end = _value_end(clean, value_start)
        value = clean[value_start:value_end]
        if _style_function(value):
            hits.append((match.start(), "blur() in filter style"))
    for match in TAILWIND_BLUR.finditer(clean):
        if match.group().rsplit(":", 1)[-1] not in (
            "blur-none",
            "backdrop-blur-none",
        ):
            hits.append((match.start(), "blur utility"))
    return sorted(set(hits))


def _self_test() -> None:
    root = Path(__file__).with_name("rules")
    good = (root / "blur.good.css").read_text()
    bad = (root / "blur.bad.css").read_text()
    _expect(check_blur(good, css=True) == [])
    _expect(len(check_blur(bad, css=True)) >= 4)
    cases = [
        ("a { filter: blur(0); }", True),
        ("a { backdrop-filter: blur(2px); }", True),
        ("a { -webkit-filter: blur(1px); }", True),
        ("a { -webkit-backdrop-filter: blur(1px); }", True),
        ('({ "filter": "blur(2px)" })', False),
        ("({ backdropFilter: 'blur(2px)' })", False),
        ("<div className='md:hover:blur-[2px]' />", False),
        ("<div class='backdrop-blur-md' />", False),
        ("<div className='blur' />", False),
        ("a { filter: drop-shadow(0, 0, 2px, #000), blur(2px); }", True),
        ("<div class='blur-none backdrop-blur-none' />", False),
        ("/* filter: blur(2px); */ a { color: red; }", True),
        ('a { content: "filter: blur(2px)"; }', True),
        ('const prose = "filter: blur(2px) https://x/blur(4px)";', False),
    ]
    rejected = {case[0] for case in cases[:10]}
    for source, is_css in cases:
        result = check_blur(source, css=is_css)
        _expect(bool(result) == (source in rejected))
        if "/*" in source:
            _expect(result == [])
        if result:
            _expect(0 <= result[0][0] < len(source))
    offset_source = "a { filter: blur(2px); }"
    _expect(check_blur(offset_source, css=True)[0][0] == offset_source.index("filter"))


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        _self_test()
    else:
        raise SystemExit("usage: neo_effects.py --self-test")
