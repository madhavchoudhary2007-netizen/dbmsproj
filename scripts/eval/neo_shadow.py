"""Validate the hard-shadow rules used by the neo-brutal design system."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.eval.neo_contrast import CLASS, LITERAL
from scripts.eval.neo_effects import _inside_string, _value_end
from scripts.eval.source_text import mask_comments

_TOKEN = re.compile(r"var\(--(?:shadow-nb|nb-shadow)-(4|8|12|16)\)")
_TOKEN_KEYS = {
    f"--{style}-{size}" for style in ("shadow-nb", "nb-shadow") for size in (4, 8, 12, 16)
}
_LENGTH = re.compile(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))px\Z")
_COLOR_PATTERN = (
    r"(?:#(?:000|000000)|black|var\(--(?:nb-ink|color-ink)\)|"
    r"rgb\(\s*0\s*,\s*0\s*,\s*0\s*\)|"
    r"rgba\(\s*0\s*,\s*0\s*,\s*0\s*,\s*(?:1|1\.0+)\s*\))"
)
_COLOR_SUFFIX = re.compile(rf"(?P<color>{_COLOR_PATTERN})\s*$", re.IGNORECASE)
_KEY = re.compile(
    r"(?P<key>box-shadow|boxShadow|['\"]boxShadow['\"]|"
    r"--(?:shadow-nb|nb-shadow)-(?:4|8|12|16))\s*:",
    re.IGNORECASE,
)
_IMPORTANT = re.compile(r"\s*!important\s*$", re.IGNORECASE)
_NAMED_CLASS = re.compile(r"shadow-nb-(4|8|12|16)\Z")
_MIN_PIXEL_VARIANT = re.compile(r"min-\[(\d+(?:\.\d+)?)px\]\Z")


def _length(part: str) -> float | None:
    match = _LENGTH.fullmatch(part)
    return float(match.group(1)) if match else 0.0 if part == "0" else None


def _literal_layer(layer: str, max_offset: int, tokens: bool) -> bool:
    token = _TOKEN.fullmatch(layer)
    if token:
        return tokens and int(token.group(1)) <= max_offset
    if layer.lower() == "none":
        return True
    color_match = _COLOR_SUFFIX.search(layer)
    if color_match is None:
        return False
    lengths = layer[: color_match.start()].split()
    if not 2 <= len(lengths) <= 4:
        return False
    parsed = [_length(part) for part in lengths]
    if any(number is None for number in parsed):
        return False
    numbers = [number for number in parsed if number is not None]
    return (
        len(numbers) in (2, 3, 4)
        and numbers[2:] == [0] * (len(numbers) - 2)
        and all(abs(number) <= max_offset for number in numbers[:2])
    )


def valid_shadow(value: str, max_offset: int = 16) -> bool:
    """Return whether every comma-separated shadow layer obeys the hard-shadow rule."""
    if max_offset < 0:
        return False
    value = value.strip()
    if len(value) >= 2 and value[0] in "'\"" and value[-1] == value[0]:
        value = value[1:-1]
    layers = [layer.strip() for layer in re.split(r",(?![^()]*\))", value)]
    return bool(layers) and all(_literal_layer(layer, max_offset, True) for layer in layers)


def _class_limit(variants: list[str], max_offset: int) -> int:
    has_desktop_min = any(
        item in {"sm", "md", "lg", "xl", "2xl"}
        or (match := _MIN_PIXEL_VARIANT.fullmatch(item)) is not None
        and float(match.group(1)) >= 620
        for item in variants
    )
    has_mobile_max = any(item.startswith("max-") for item in variants)
    return min(max_offset, 8) if has_mobile_max and not has_desktop_min else max_offset


def _strip_important(utility: str) -> str | None:
    leading = utility.startswith("!")
    if leading:
        utility = utility[1:]
    trailing = utility.endswith("!")
    if leading and trailing:
        return None
    return utility[:-1] if trailing else utility


def _class_utility(token: str, max_offset: int) -> bool:
    depth = 0
    split = -1
    for index, char in enumerate(token):
        if char == "[":
            depth += 1
        elif char == "]":
            depth = max(0, depth - 1)
        elif char == ":" and depth == 0:
            split = index
    variants = token[:split].split(":") if split >= 0 else []
    utility = _strip_important(token[split + 1 :] if split >= 0 else token)
    if utility is None:
        return False
    limit = _class_limit(variants, max_offset)
    if utility == "shadow-none" or utility in {"shadow-black", "shadow-ink"}:
        return True
    named = _NAMED_CLASS.fullmatch(utility)
    if named:
        return int(named.group(1)) <= limit
    if utility.startswith("shadow-[") and utility.endswith("]"):
        return valid_shadow(utility[8:-1].replace("_", " "), limit)
    return not (utility == "shadow" or utility.startswith("shadow-"))


def _class_hits(clean: str, max_offset: int, enabled: bool) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    if not enabled:
        return hits
    for match in CLASS.finditer(clean):
        outside_tag = clean.rfind("<", 0, match.start()) <= clean.rfind(">", 0, match.start())
        if _inside_string(clean, match.start()) or outside_tag:
            continue
        if match.group(2) is not None:
            literals = [(match.start(2), match.group(2))]
        else:
            expression = match.group(3)
            literals = [
                (match.start(3) + item.start(2), item.group(2))
                for item in LITERAL.finditer(expression)
            ]
        for offset, classes in literals:
            for utility in re.finditer(r"\S+", classes):
                if not _class_utility(utility.group(), max_offset):
                    hits.append((offset + utility.start(), "disallowed hard shadow class"))
    return hits


def check_shadows(text: str, css: bool = False, max_offset: int = 16) -> list[tuple[int, str]]:
    clean = mask_comments(text, css)
    hits: list[tuple[int, str]] = []
    for match in _KEY.finditer(clean):
        key = match.group("key").strip("'\"")
        if css:
            if key.lower() == "box-shadow":
                key = "box-shadow"
            elif key not in _TOKEN_KEYS:
                continue
        elif key != "boxShadow":
            continue
        is_token = key.startswith("--")
        start = match.start()
        prefix = clean[:start].rstrip()
        if _inside_string(clean, start) or not prefix.endswith(("{", ",", ";")):
            continue
        value_start = match.end()
        value_end = _value_end(clean, value_start)
        value = clean[value_start:value_end].strip()
        if css:
            value = _IMPORTANT.sub("", value).strip()
        if value.startswith(("'", '"')) and value[-1:] == value[0]:
            value = value[1:-1]
        valid = (
            _literal_layer(value, max_offset, True) if is_token else valid_shadow(value, max_offset)
        )
        if not valid:
            hits.append((start, "disallowed hard shadow"))
    hits.extend(_class_hits(clean, max_offset, not css))
    return sorted(set(hits))


def _expect(condition: bool) -> None:
    if not condition:
        raise AssertionError("shadow rule self-test failed")


def self_test() -> None:
    rules = Path(__file__).parent / "rules"
    good = (rules / "shadow.good.css").read_text()
    bad = (rules / "shadow.bad.css").read_text()
    _expect(check_shadows(good, css=True) == [])
    _expect(bool(check_shadows(bad, css=True)))
    _expect(check_shadows(good) == [])
    _expect(bool(check_shadows(bad)))
    _expect(valid_shadow("none"))
    _expect(valid_shadow("-8px 8px 0 0 #000", max_offset=8))
    _expect(not valid_shadow("9px 0px #000", max_offset=8))
    _expect(not valid_shadow("2px 2px 1px #000"))
    _expect(not valid_shadow("2px 2px 0 1px #000"))
    _expect(not valid_shadow("2px 2px 0 #222"))
    _expect(not valid_shadow("2px 2px 0 rgba(0,0,0,.5)"))
    _expect(valid_shadow("2px 2px 0 rgb(0,0,0)"))
    _expect(valid_shadow("4px 4px 0 rgb(0, 0, 0)"))
    _expect(valid_shadow("2px 2px 0 rgba(0,0,0,1)"))
    _expect(valid_shadow("2px 2px #000, var(--nb-shadow-8)"))
    _expect(not valid_shadow("2px 2px #000, 20px 0px #000"))
    _expect(not valid_shadow("var(--shadow-other)"))
    _expect(not valid_shadow("var(--shadow-nb-16)", max_offset=8))
    _expect(check_shadows(".x { /* box-shadow: 4px 4px 1px #000 */ }", css=True) == [])
    _expect(check_shadows("box-shadow: 4px 4px 1px #000", css=True) == [])
    _expect(check_shadows(".x { box-shadow: none !important; }", css=True) == [])
    _expect(bool(check_shadows(".x { BOX-SHADOW: 0 0 8px #000; }", css=True)))
    _expect(bool(check_shadows("({ 'boxShadow': '4px 4px 1px #000' })")))
    _expect(check_shadows("const s = 'boxShadow: 4px 4px 1px #000';") == [])
    _expect(check_shadows(".x { --shadow-nb-8: 8px 8px 0 #000; }", css=True) == [])
    _expect(bool(check_shadows(".x { --shadow-nb-8: 8px 8px 1px #000; }", css=True)))
    _expect(check_shadows(".x { --nb-shadow-4: var(--shadow-nb-4); }", css=True) == [])
    _expect(bool(check_shadows(".x { --nb-shadow-4: var(--other); }", css=True)))
    _expect(bool(check_shadows(".x { --shadow-nb-4: 4px 4px 0 #222; }", css=True)))
    _expect(bool(check_shadows(".x { --shadow-nb-4: 4px 4px 0 rgba(0,0,0,.5); }", css=True)))
    _expect(
        check_shadows('<div className="shadow-none shadow-nb-8 shadow-black shadow-ink" />') == []
    )
    _expect(check_shadows('<div className={active ? "shadow-nb-8" : "shadow-none"} />') == [])
    _expect(check_shadows('<div className="max-sm:shadow-nb-8" />') == [])
    _expect(check_shadows('<div className="shadow-nb-8! md:max-lg:shadow-nb-12" />') == [])
    _expect(check_shadows('<div className="shadow-[4px_4px_0_#000]" />') == [])
    _expect(
        bool(
            check_shadows(
                '<div className="shadow shadow-sm shadow-md shadow-lg shadow-xl shadow-2xl" />'
            )
        )
    )
    _expect(
        check_shadows('<div className="shadow-xl" />') == [(16, "disallowed hard shadow class")]
    )
    important_bad = '<div className="!shadow-xl" />'
    _expect(check_shadows(important_bad) == [(16, "disallowed hard shadow class")])
    _expect(bool(check_shadows('<div className="shadow-red-500" />')))
    _expect(bool(check_shadows('<div className="shadow-[4px_4px_8px_#000]" />')))
    _expect(bool(check_shadows('<div className="max-[620px]:shadow-nb-12" />')))
    _expect(bool(check_shadows('<div className="max-sm:shadow-nb-12" />')))
    _expect(
        check_shadows('const copy = { message: "shadow-xl" }; // <div className="shadow-xl" />')
        == []
    )


if __name__ == "__main__":
    import sys

    if sys.argv[1:] == ["--self-test"]:
        self_test()
    elif sys.argv[1:]:
        raise SystemExit(f"unknown arguments: {' '.join(sys.argv[1:])}")
