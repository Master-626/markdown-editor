"""
File handling operations for markdown-editor.
"""

from pathlib import Path
from typing import Optional


def create_new_file(file_path: str, template: str = "") -> Path:
    """Create a new markdown file."""
    path = Path(file_path)
    if path.exists():
        raise FileExistsError(f"File already exists: {file_path}")

    content = template or "# New Document\n\nStart writing here...\n"
    path.write_text(content, encoding="utf-8")
    return path


def open_file(file_path: str) -> str:
    """Open and read a markdown file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return path.read_text(encoding="utf-8")


def save_file(file_path: str, content: str) -> Path:
    """Save content to a markdown file."""
    path = Path(file_path)
    path.write_text(content, encoding="utf-8")
    return path


def get_file_stats(file_path: str) -> dict:
    """Get file statistics."""
    content = open_file(file_path)
    path = Path(file_path)

    lines = content.splitlines()
    words = len(content.split())
    characters = len(content)

    return {
        "name": path.name,
        "size_bytes": path.stat().st_size,
        "lines": len(lines),
        "words": words,
        "characters": characters,
    }
