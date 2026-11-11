"""
Search and replace functionality.
"""

import re
from pathlib import Path
from typing import List, Tuple


def search_in_file(
    file_path: str, query: str, case_sensitive: bool = False
) -> List[Tuple[int, str]]:
    """Search for literal text and return ``(line_number, line)`` pairs.

    A line that contains the query more than once is returned once. An empty
    query is rejected instead of matching every line.
    """
    if query == "":
        raise ValueError("Search query must not be empty")

    content = _read_text(file_path)
    results = []
    for line_number, line in enumerate(content.splitlines(), 1):
        haystack = line if case_sensitive else line.lower()
        needle = query if case_sensitive else query.lower()
        if needle in haystack:
            results.append((line_number, line))
    return results


def replace_in_file(
    file_path: str, old_text: str, new_text: str, case_sensitive: bool = False
) -> int:
    """Replace literal text in a file. Returns the number of replacements.

    The replacement is literal, including backslashes. Newline characters
    already in the file are preserved. An empty search string is rejected
    because it would otherwise be inserted between every character.
    """
    if old_text == "":
        raise ValueError("Text to replace must not be empty")

    path = Path(file_path)
    content = _read_text(file_path, preserve_newlines=True)
    if case_sensitive:
        count = content.count(old_text)
        new_content = content.replace(old_text, new_text)
    else:
        pattern = re.compile(re.escape(old_text), re.IGNORECASE)
        count = len(pattern.findall(content))
        new_content = pattern.sub(lambda _match: new_text, content)

    if new_content != content:
        _write_text(path, new_content)
    return count


def _read_text(file_path: str, preserve_newlines: bool = False) -> str:
    """Read text. ``newline=""`` keeps CR and LF bytes on Python 3.8+."""
    path = Path(file_path)
    newline = "" if preserve_newlines else None
    try:
        with path.open("r", encoding="utf-8", newline=newline) as handle:
            return handle.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}") from None


def _write_text(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)
