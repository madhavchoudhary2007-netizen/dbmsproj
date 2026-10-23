"""Static co-occurrence check for white text on the neo-brutal red."""

import re
import sys
from pathlib import Path

from scripts.eval.neo_effects import _inside_string
from scripts.eval.source_text import mask_comments

WHITE = re.compile(r"^(?:white|#fff(?:fff)?|var\(--(?:nb|color)-paper\)|var\(--paper\))$", re.I)
RED = re.compile(r"^(?:#ff6b6b|var\(--(?:nb|color)-red\))$", re.I)
BLOCK = re.compile(
    r"\{((?:[^{}'\"`]|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`)*)\}", re.S
)
DECL = re.compile(r"(?:^|[;,])\s*(['\"]?)([\w-]+)\1\s*:\s*([^;,]*)")
CLASS = re.compile(r"\bclass(?:Name)?\s*=\s*(?:(['\"`])([^'\"`]*)\1|\{([^}]*)\})", re.S)
LITERAL = re.compile(r"(['\"`])([^'\"`]*)\1")
RED_CLASS = re.compile(r"(?:^|\s)(bg-red|bg-\[#ff6b6b\])(?:\s|$)", re.I)
WHITE_CLASS = re.compile(r"(?:^|\s)(text-(?:white|paper|\[#(?:fff|ffffff)\]))(?:\s|$)", re.I)


def _fields(body: str) -> dict[str, tuple[str, int, bool]]:
    fields: dict[str, tuple[str, int, bool]] = {}
    for match in DECL.finditer(body):
        if _inside_string(body, match.start(1)):
            continue
        key = match.group(2).lower().replace("backgroundcolor", "background-color")
        value = match.group(3)
        prior = fields.get(key)
        important = bool(re.search(r"!\s*important\s*$", value, re.I))
        if prior is None or important or not prior[2]:
            fields[key] = (value, match.start(2), important)
    return fields


def _value(value: str) -> str:
    value = re.sub(r"\s*!important\s*$", "", value.strip(), flags=re.I).strip()
    if len(value) >= 2 and value[0] in "'\"" and value[-1] == value[0]:
        value = value[1:-1]
    return value.strip().lower()


def check_white_on_red(text: str, css: bool = False) -> list[tuple[int, str]]:
    """Find white foreground and red background in one CSS/JS block or class literal."""
    clean = mask_comments(text, css=css)
    hits: list[tuple[int, str]] = []
    for block in BLOCK.finditer(clean):
        body_start = block.start(1)
        fields = _fields(block.group(1))
        foreground = fields.get("color")
        backgrounds = [fields[key] for key in ("background", "background-color") if key in fields]
        background = max(backgrounds, key=lambda field: (field[2], field[1]), default=None)
        if (
            foreground
            and WHITE.fullmatch(_value(foreground[0]))
            and background
            and RED.fullmatch(_value(background[0]))
        ):
            hits.append(
                (body_start + foreground[1], "white foreground co-occurs with red background")
            )
    for match in CLASS.finditer(clean):
        if _inside_string(clean, match.start()) or clean.rfind(
            "<", 0, match.start()
        ) <= clean.rfind(">", 0, match.start()):
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
            red, white = RED_CLASS.search(classes), WHITE_CLASS.search(classes)
            if red and white:
                hits.append(
                    (
                        offset + white.start(1),
                        "white text class co-occurs with red background class",
                    )
                )
    return sorted(set(hits))


def _self_test() -> None:
    root = Path(__file__).with_name("rules")
    _expect(check_white_on_red((root / "contrast.good.css").read_text(), css=True) == [])
    _expect(len(check_white_on_red((root / "contrast.bad.css").read_text(), css=True)) == 2)
    cases = [
        ("x { color:#fff; background:var(--nb-red) !important; }", True, True),
        ("x { color:var(--color-paper); background-color:#ff6b6b; }", True, True),
        ('({ color: "white", "backgroundColor": "#FF6B6B" })', False, True),
        ('({ "color": "#fff", "background": "var(--color-red)" })', False, True),
        ('<i class="bg-red-500 text-white" />', False, False),
        ('<i className="text-paper bg-[#FF6B6B]" />', False, True),
        ('<i class="bg-red text-[#fff]" />', False, True),
        ('<i class="bg-red text-black" />', True, False),
        ('<i class="bg-ink text-white" />', True, False),
        ('<i class="bg-red text-black"/><i class="bg-ink text-white"/>', True, False),
        ("red and white are named in this ordinary prose.", False, False),
        ('const prose = "class=\\"bg-red text-white\\"";', False, False),
        ("/* x { color:white; background:red } */", True, False),
        ('const url = "https://x.test/#FF6B6B"; x { content:"white #FF6B6B"; }', False, False),
        ("a { color:white; }\na { background:#FF6B6B; }", True, False),
        ("a { color:white; background:#FF6B6B; background-color:black; }", True, False),
        ("a { color:white; background:#FF6B6B !important; background-color:black; }", True, True),
        ('<i className={danger ? "bg-red text-white" : "bg-cream text-ink"} />', False, True),
        ('<i className={danger ? "bg-red text-black" : "bg-cream text-white"} />', False, False),
    ]
    for source, is_css, expected in cases:
        _expect(bool(check_white_on_red(source, css=is_css)) is expected)
    source = "\na { color:white; background:#FF6B6B; }"
    offset = check_white_on_red(source, css=True)[0][0]
    _expect(offset == source.index("color"))
    _expect(source.count("\n", 0, offset) + 1 == 2)
    source = "x {color:white;background:#ff6b6b}"
    offset = check_white_on_red(source, css=True)[0][0]
    _expect(offset == source.index("color"))
    _expect(source.count("\n", 0, offset) + 1 == 1)
    source = "<i class='bg-red text-white'/>"
    offset = check_white_on_red(source)[0][0]
    _expect(offset == source.index("text-white"))
    _expect(source.count("\n", 0, offset) + 1 == 1)


def _expect(condition: bool) -> None:
    if not condition:
        raise AssertionError("contrast self-test failed")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        _self_test()
    else:
        raise SystemExit("usage: neo_contrast.py --self-test")
