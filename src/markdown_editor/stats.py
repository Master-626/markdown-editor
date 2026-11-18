"""
Statistics and outline for markdown files.

Structural counts follow the same Markdown engine used for HTML preview
(Python-Markdown with the extensions enabled by ``render_to_html``): closed
fenced code is not structure, images are not links, and ATX headings do not
require a space after the hashes.
"""

import re
from typing import Dict, List, Optional, Set, Tuple

_FENCE_OPENER = re.compile(r"^(`{3,}|~{3,})")
_ATX_HEADING = re.compile(
    r"^(?P<level>#{1,6})(?P<header>(?:\\.|[^\\#]|#+(?=[^#]))*?)#*$"
)
_SETEXT_UNDERLINE = re.compile(r"^(?:=+|-+)[ ]*$")
_QUOTE_PREFIX = re.compile(r"^[ ]{0,3}>[ ]?")
_LIST_ITEM = re.compile(r"^(?P<indent> *)(?:[+*-]|\d+\.)[ ]+")
_THEMATIC_BREAK = re.compile(
    r"^[ ]{0,3}(?:(?:-[ ]{0,2}){3,}|(?:_[ ]{0,2}){3,}|(?:\*[ ]{0,2}){3,})[ ]*$"
)
_CJK_CHAR = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")
_CJK_PUNCTUATION = re.compile(r"[\u3000-\u303f]")
_DEFINITION = re.compile(r"^[ ]{0,3}\[([^\]]+)\]:[ \t]*\S", re.MULTILINE)
_INLINE_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\n]*)\)")
_IMAGE_REFERENCE = re.compile(r"!\[([^\]]*)\]\[([^\]]*)\]")
_INLINE_LINK = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\n]*)\)")
_REFERENCE_LINK = re.compile(r"(?<!!)\[([^\]]+)\]\[([^\]]*)\]")
_AUTOLINK = re.compile(r"<[A-Za-z][A-Za-z0-9+.-]*://[^<>\s]+>")
_EMAIL_LINK = re.compile(r"<[^<> !\n]+@[^@<> \n]+>")
_SHORTCUT_LINK = re.compile(r"(?<!!)\[([^\]]+)\](?!\s*[\[(:])")
_ESCAPE = re.compile(r"\\(.)")


def analyze_markdown(content: str) -> Dict:
    """Analyze markdown content and return statistics."""
    lines = _prepared_lines(content)
    fenced, code_blocks, _delimiters = _scan_fences(lines)
    outline, setext_lines = _collect_headings(lines, fenced)
    headings = {
        "h1": sum(1 for item in outline if item["level"] == 1),
        "h2": sum(1 for item in outline if item["level"] == 2),
        "h3": sum(1 for item in outline if item["level"] == 3),
        "h4+": sum(1 for item in outline if item["level"] >= 4),
    }
    structural = _mask_inline_code(_structural_text(lines, fenced))
    links, images = _count_links_and_images(structural)
    words_count = _count_words(content)

    return {
        "total_words": words_count,
        "total_characters": len(content),
        "total_lines": len(content.splitlines()),
        "headings": headings,
        "code_blocks": code_blocks,
        "links": links,
        "images": images,
        "list_items": _count_list_items(lines, fenced, setext_lines),
        "reading_time_minutes": round(words_count / 200, 1),
    }


def extract_outline(content: str) -> List[Dict]:
    """Return headings outside closed fenced code blocks.

    Each item is ``{"level": int, "text": str, "line": int}``. Levels are
    1 through 6. Line numbers start at 1 and refer to the heading text, not a
    setext underline. ATX headings (with or without a space after the hashes)
    and setext headings are included, including headings inside blockquotes.
    """
    lines = _prepared_lines(content)
    fenced, _code_blocks, _delimiters = _scan_fences(lines)
    outline, _setext_lines = _collect_headings(lines, fenced)
    return outline


def parse_atx_heading(line: str) -> Optional[Tuple[int, str]]:
    """Return ``(level, text)`` when ``line`` is an ATX heading."""
    match = _ATX_HEADING.match(line)
    if match is None:
        return None
    return len(match.group("level")), _heading_text(match.group("header"))


def fence_regions(content: str) -> Tuple[Set[int], Set[int]]:
    """Return ``(delimiter lines, all fenced lines)`` using 1-based numbers.

    Only closed fences that start at column zero are included, matching the
    HTML preview. The delimiter set is the opening and closing lines.
    """
    lines = _prepared_lines(content)
    fenced, _code_blocks, delimiters = _scan_fences(lines)
    return delimiters, fenced


def _prepared_lines(content: str) -> List[str]:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    return [line.expandtabs(4) for line in normalized.splitlines()]


def _scan_fences(lines: List[str]) -> Tuple[Set[int], int, Set[int]]:
    """Return covered lines, the closed-fence count, and delimiter lines."""
    covered: Set[int] = set()
    delimiters: Set[int] = set()
    code_blocks = 0
    index = 0
    while index < len(lines):
        opener = _fence_opener(lines[index])
        if opener is None:
            index += 1
            continue
        close_at = None
        for candidate in range(index + 1, len(lines)):
            if _fence_closer(lines[candidate], opener):
                close_at = candidate
                break
        if close_at is None:
            # An unclosed opener is literal text, as in the HTML preview.
            index += 1
            continue
        code_blocks += 1
        for covered_index in range(index, close_at + 1):
            covered.add(covered_index + 1)
        delimiters.add(index + 1)
        delimiters.add(close_at + 1)
        index = close_at + 1
    return covered, code_blocks, delimiters


def _fence_opener(line: str) -> Optional[str]:
    match = _FENCE_OPENER.match(line)
    if match is None:
        return None
    return match.group(1)


def _fence_closer(line: str, opener: str) -> bool:
    return re.match("^" + re.escape(opener) + r"[ ]*$", line) is not None


def _collect_headings(
    lines: List[str], fenced: Set[int]
) -> Tuple[List[Dict], Set[int]]:
    outline: List[Dict] = []
    setext_lines: Set[int] = set()
    index = 0
    while index < len(lines):
        number = index + 1
        if number in fenced:
            index += 1
            continue
        visible = _strip_quotes(lines[index])
        atx = parse_atx_heading(visible)
        if atx is not None:
            level, text = atx
            outline.append({"level": level, "text": text, "line": number})
            index += 1
            continue
        if (
            index + 1 < len(lines)
            and (index + 2) not in fenced
            and _starts_block(lines, index, fenced)
            and visible.strip()
        ):
            underline = _strip_quotes(lines[index + 1])
            if _SETEXT_UNDERLINE.match(underline):
                level = 1 if underline.startswith("=") else 2
                outline.append(
                    {"level": level, "text": _heading_text(visible), "line": number}
                )
                setext_lines.add(number)
                index += 2
                continue
        index += 1
    return outline, setext_lines


def _starts_block(lines: List[str], index: int, fenced: Set[int]) -> bool:
    if index == 0:
        return True
    if index in fenced:
        return True
    return lines[index - 1].strip() == ""


def _strip_quotes(line: str) -> str:
    while True:
        match = _QUOTE_PREFIX.match(line)
        if match is None:
            return line
        line = line[match.end():]


def _heading_text(text: str) -> str:
    return _ESCAPE.sub(r"\1", text.strip())


def _structural_text(lines: List[str], fenced: Set[int]) -> str:
    visible = ["" if number in fenced else line for number, line in enumerate(lines, 1)]
    return "\n".join(visible)


def _mask_inline_code(text: str) -> str:
    """Replace single-line code spans with spaces so they are not structure."""
    masked_lines = [_mask_inline_code_line(line) for line in text.split("\n")]
    return "\n".join(masked_lines)


def _mask_inline_code_line(line: str) -> str:
    chars = list(line)
    index = 0
    while index < len(chars):
        if chars[index] == "\\" and index + 1 < len(chars):
            index += 2
            continue
        if chars[index] != "`":
            index += 1
            continue
        end_of_run = index
        while end_of_run < len(chars) and chars[end_of_run] == "`":
            end_of_run += 1
        run = end_of_run - index
        cursor = end_of_run
        closing = None
        while cursor < len(chars):
            if chars[cursor] != "`":
                cursor += 1
                continue
            closing_end = cursor
            while closing_end < len(chars) and chars[closing_end] == "`":
                closing_end += 1
            if closing_end - cursor == run:
                closing = closing_end
                break
            cursor = closing_end
        if closing is None:
            index = end_of_run
            continue
        for position in range(index, closing):
            chars[position] = " "
        index = closing
    return "".join(chars)


def _count_links_and_images(text: str) -> Tuple[int, int]:
    definitions = {
        _label_key(match.group(1)) for match in _DEFINITION.finditer(text)
    }
    images = len(_INLINE_IMAGE.findall(text))
    text = _blank_matches(_INLINE_IMAGE, text)
    for alt, reference in _IMAGE_REFERENCE.findall(text):
        if _label_key(reference or alt) in definitions:
            images += 1
    text = _blank_matches(_IMAGE_REFERENCE, text)

    links = len(_INLINE_LINK.findall(text))
    text = _blank_matches(_INLINE_LINK, text)
    for label, reference in _REFERENCE_LINK.findall(text):
        if _label_key(reference or label) in definitions:
            links += 1
    text = _blank_matches(_REFERENCE_LINK, text)
    links += len(_AUTOLINK.findall(text))
    text = _blank_matches(_AUTOLINK, text)
    links += len(_EMAIL_LINK.findall(text))
    text = _blank_matches(_EMAIL_LINK, text)
    for match in _SHORTCUT_LINK.finditer(text):
        if _label_key(match.group(1)) in definitions:
            links += 1
    return links, images


def _label_key(label: str) -> str:
    return re.sub(r"\s+", " ", label.strip().lower())


def _blank_matches(pattern: re.Pattern, text: str) -> str:
    return pattern.sub(lambda match: re.sub(r"[^\n]", " ", match.group(0)), text)


def _count_list_items(lines: List[str], fenced: Set[int], setext_lines: Set[int]) -> int:
    count = 0
    in_list = False
    for index, line in enumerate(lines):
        number = index + 1
        if number in fenced or number in setext_lines:
            in_list = False
            continue
        visible = _strip_quotes(line)
        if visible.strip() == "" or _THEMATIC_BREAK.match(visible):
            in_list = False
            continue
        match = _LIST_ITEM.match(visible)
        if match is None:
            indent = len(visible) - len(visible.lstrip(" "))
            if not (in_list and indent >= 4):
                in_list = False
            continue
        indent = len(match.group("indent"))
        if indent <= 3 or in_list:
            count += 1
            in_list = True
        else:
            in_list = False
    return count


def _count_words(content: str) -> int:
    """Count whitespace-separated words, with one word per CJK character.

    A run of Chinese, Japanese, or Korean letters has no spaces, so
    ``str.split`` would report the whole run as one word and the reading
    time would collapse. ASCII word counts are unchanged.
    """
    cjk_words = len(_CJK_CHAR.findall(content))
    remainder = _CJK_CHAR.sub(" ", content)
    remainder = _CJK_PUNCTUATION.sub(" ", remainder)
    return cjk_words + len(remainder.split())
