"""
File handling operations for markdown-editor.
"""

import os
from pathlib import Path


def create_new_file(file_path: str, template: str = "") -> Path:
    """Create a new markdown file.

    Existing files, directories, and symlinks are left untouched. A dangling
    symlink is not followed, so its target is not created. An empty
    ``template`` selects the built-in starter text.
    """
    path = Path(file_path)
    content = template if template else "# New Document\n\nStart writing here...\n"
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except OSError as error:
        if path.is_symlink() or path.exists():
            raise FileExistsError(f"File already exists: {file_path}") from error
        raise
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
    except Exception:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise
    return path


def open_file(file_path: str) -> str:
    """Open and read a markdown file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return path.read_text(encoding="utf-8")


def save_file(file_path: str, content: str) -> Path:
    """Save content to a markdown file without changing its newline characters."""
    path = Path(file_path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)
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
