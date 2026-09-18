"""
Search and replace functionality.
"""

from pathlib import Path
from typing import List, Tuple


def search_in_file(file_path: str, query: str, case_sensitive: bool = False) -> List[Tuple[int, str]]:
    """Search for text in a markdown file."""
    content = Path(file_path).read_text(encoding="utf-8")
    lines = content.splitlines()

    results = []
    for i, line in enumerate(lines, 1):
        if case_sensitive:
            if query in line:
                results.append((i, line))
        else:
            if query.lower() in line.lower():
                results.append((i, line))

    return results


def replace_in_file(file_path: str, old_text: str, new_text: str, case_sensitive: bool = False) -> int:
    """Replace text in a file. Returns number of replacements."""
    content = Path(file_path).read_text(encoding="utf-8")

    if case_sensitive:
        count = content.count(old_text)
        new_content = content.replace(old_text, new_text)
    else:
        # Case-insensitive replacement
        import re
        pattern = re.compile(re.escape(old_text), re.IGNORECASE)
        count = len(pattern.findall(content))
        new_content = pattern.sub(new_text, content)

    Path(file_path).write_text(new_content, encoding="utf-8")
    return count
