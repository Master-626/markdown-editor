"""
Statistics and analysis for markdown files.
"""

import re
from typing import Dict


def analyze_markdown(content: str) -> Dict:
    """Analyze markdown content and return statistics."""
    lines = content.splitlines()
    words = content.split()

    # Count headings
    headings = {
        "h1": len(re.findall(r"^# ", content, re.MULTILINE)),
        "h2": len(re.findall(r"^## ", content, re.MULTILINE)),
        "h3": len(re.findall(r"^### ", content, re.MULTILINE)),
        "h4+": len(re.findall(r"^#{4,} ", content, re.MULTILINE)),
    }

    # Count code blocks
    code_blocks = len(re.findall(r"```", content)) // 2

    # Count links
    links = len(re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content))

    # Count images
    images = len(re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", content))

    # Count lists
    list_items = len(re.findall(r"^[-*] ", content, re.MULTILINE))

    # Reading time (words per minute)
    words_count = len(words)
    reading_time_min = round(words_count / 200, 1)

    return {
        "total_words": words_count,
        "total_characters": len(content),
        "total_lines": len(lines),
        "headings": headings,
        "code_blocks": code_blocks,
        "links": links,
        "images": images,
        "list_items": list_items,
        "reading_time_minutes": reading_time_min,
    }
