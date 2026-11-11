"""
Markdown preview and rendering.
"""

import os
from itertools import count
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

import markdown
from rich.markup import escape

from .stats import extract_outline, fence_regions


def save_preview(file_path: str) -> Path:
    """Save a sibling HTML preview without overwriting any existing file."""
    from .file_ops import open_file

    source = Path(file_path)
    html = render_to_html(open_file(file_path))

    staging = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=str(source.parent),
            prefix=".mdedit-preview-", suffix=".tmp", delete=False,
        ) as stream:
            staging = Path(stream.name)
            stream.write(html)

        for number in count():
            suffix = "" if number == 0 else f"_{number}"
            output = source.with_name(f"{source.stem}_preview{suffix}.html")
            try:
                output.lstat()
            except FileNotFoundError:
                pass
            else:
                continue
            try:
                # Publishing a hard link cannot replace or follow a destination
                # symlink, even on Windows where open("x") may follow one.
                os.link(staging, output)
            except FileExistsError:
                continue
            except PermissionError as error:
                # Windows may report a raced directory collision as EACCES.
                try:
                    output.lstat()
                except FileNotFoundError:
                    raise error
                continue
            return output
    finally:
        if staging is not None:
            staging.unlink()


def render_to_html(markdown_text: str, extensions: Optional[list] = None) -> str:
    """Render markdown text to HTML."""
    if extensions is None:
        extensions = ["extra", "codehilite", "toc", "tables", "fenced_code"]

    html_body = markdown.markdown(markdown_text, extensions=extensions)

    # Wrap in full HTML document
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Markdown Preview</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.7;
            color: #333;
        }}
        pre {{
            background: #f5f5f5;
            padding: 1rem;
            border-radius: 6px;
            overflow-x: auto;
        }}
        code {{
            background: #f5f5f5;
            padding: 0.2em 0.4em;
            border-radius: 3px;
        }}
        pre code {{
            background: none;
            padding: 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
        }}
        table th, table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""

    return html


def preview_to_terminal(markdown_text: str) -> str:
    """Generate a Rich-markup preview.

    Heading text and other document text are escaped so characters such as
    ``[draft]`` survive when the result is printed. Lines inside a closed
    fenced code block are not styled as headings or lists.
    """
    lines = markdown_text.splitlines()
    headings = {item["line"]: item for item in extract_outline(markdown_text)}
    delimiters, fenced = fence_regions(markdown_text)
    result = []

    for number, line in enumerate(lines, 1):
        if number in delimiters:
            result.append(f"[dim]{escape(line)}[/dim]")
        elif number in fenced:
            result.append(escape(line))
        elif number in headings and headings[number]["level"] <= 3:
            result.append(_format_heading(headings[number]))
        elif line.startswith("- "):
            result.append(f"  • {escape(line[2:])}")
        else:
            result.append(escape(line))

    return "\n".join(result)


def _format_heading(item: dict) -> str:
    styles = {1: "bold", 2: "cyan", 3: "green"}
    style = styles[item["level"]]
    return f"\n[{style}]{escape(item['text'])}[/{style}]"
