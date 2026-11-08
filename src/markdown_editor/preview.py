"""
Markdown preview and rendering.
"""

import markdown
from itertools import count
from pathlib import Path
from typing import Optional


def save_preview(file_path: str) -> Path:
    """Save a sibling HTML preview without overwriting any existing file."""
    from .file_ops import open_file

    source = Path(file_path)
    html = render_to_html(open_file(file_path))

    for number in count():
        suffix = "" if number == 0 else f"_{number}"
        output = source.with_name(f"{source.stem}_preview{suffix}.html")
        try:
            # Exclusive creation also protects existing symlinks and hard links.
            stream = output.open("x", encoding="utf-8")
        except FileExistsError:
            continue
        with stream:
            stream.write(html)
        return output


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
    """Generate a simple terminal-friendly preview."""
    lines = markdown_text.splitlines()
    result = []

    for line in lines:
        # Simple markdown rendering for terminal
        if line.startswith("# "):
            result.append(f"\n[bold]{line[2:]}[/bold]")
        elif line.startswith("## "):
            result.append(f"\n[cyan]{line[3:]}[/cyan]")
        elif line.startswith("### "):
            result.append(f"\n[green]{line[4:]}[/green]")
        elif line.startswith("- "):
            result.append(f"  • {line[2:]}")
        elif line.startswith("```"):
            result.append("[dim]" + line + "[/dim]")
        else:
            result.append(line)

    return "\n".join(result)
