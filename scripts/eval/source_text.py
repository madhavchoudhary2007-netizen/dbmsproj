"""Source text helpers shared by evaluation checkers."""


def _mask_comment(text: str, chars: list[str], i: int, css: bool) -> int | None:
    if text.startswith("/*", i):
        end = text.find("*/", i + 2)
        end = len(text) if end < 0 else end + 2
        for j in range(i, end):
            if chars[j] != "\n":
                chars[j] = " "
        return end
    if not css and text.startswith("//", i):
        end = text.find("\n", i + 2)
        end = len(text) if end < 0 else end
        for j in range(i, end):
            chars[j] = " "
        return end
    return None


def mask_comments(text: str, css: bool = False) -> str:
    """Mask comments while preserving offsets, newlines, and quoted text."""
    chars = list(text)
    i = 0
    quote = ""
    while i < len(chars):
        char = chars[i]
        if quote:
            if char == "\\":
                i += 2
                continue
            if char == quote:
                quote = ""
        elif char in "'\"`":
            quote = char
        else:
            end = _mask_comment(text, chars, i, css)
            if end is not None:
                i = end
                continue
        i += 1
    return "".join(chars)
