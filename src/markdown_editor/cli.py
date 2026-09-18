"""
CLI interface for markdown-editor.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .file_ops import create_new_file, open_file, save_file, get_file_stats
from .preview import render_to_html, preview_to_terminal
from .stats import analyze_markdown
from .search import search_in_file, replace_in_file
from .exporter import export_to_html, export_to_pdf

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Markdown Editor - Full-featured terminal Markdown editor."""
    pass


@main.command()
@click.argument("filename")
def new(filename):
    """Create a new markdown file."""
    try:
        path = create_new_file(filename)
        console.print(f"✅ Created new file: [bold green]{path}[/bold green]")
    except FileExistsError as e:
        console.print(f"❌ {e}", err=True)


@main.command()
@click.argument("filename")
def open(filename):
    """Open and display a markdown file."""
    try:
        content = open_file(filename)
        console.print(Panel(content, title=filename, border_style="blue"))
    except FileNotFoundError as e:
        console.print(f"❌ {e}", err=True)


@main.command()
@click.argument("filename")
def stats(filename):
    """Show file statistics."""
    try:
        content = open_file(filename)
        stats = analyze_markdown(content)

        table = Table(title=f"Statistics: {filename}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Words", str(stats["total_words"]))
        table.add_row("Characters", str(stats["total_characters"]))
        table.add_row("Lines", str(stats["total_lines"]))
        table.add_row("H1 Headings", str(stats["headings"]["h1"]))
        table.add_row("H2 Headings", str(stats["headings"]["h2"]))
        table.add_row("H3 Headings", str(stats["headings"]["h3"]))
        table.add_row("Code Blocks", str(stats["code_blocks"]))
        table.add_row("Links", str(stats["links"]))
        table.add_row("Images", str(stats["images"]))
        table.add_row("List Items", str(stats["list_items"]))
        table.add_row("Reading Time", f"{stats['reading_time_minutes']} min")

        console.print(table)
    except FileNotFoundError as e:
        console.print(f"❌ {e}", err=True)


@main.command()
@click.argument("filename")
@click.option("--browser", is_flag=True, help="Open in browser (not implemented)")
def preview(filename, browser):
    """Preview markdown as HTML."""
    try:
        content = open_file(filename)
        html = render_to_html(content)

        # Save preview HTML
        preview_file = filename.replace(".md", "_preview.html")
        from pathlib import Path
        Path(preview_file).write_text(html, encoding="utf-8")

        console.print(f"✅ Preview saved to: [bold green]{preview_file}[/bold green]")
        if browser:
            console.print("ℹ️ Open this file in your browser to view the preview")
    except FileNotFoundError as e:
        console.print(f"❌ {e}", err=True)


@main.command()
@click.argument("filename")
@click.option("-o", "--output", required=True, help="Output file path")
@click.option("--format", "output_format", default="html", type=click.Choice(["html", "pdf"]), help="Output format")
def export(filename, output, output_format):
    """Export markdown to HTML or PDF."""
    try:
        if output_format == "html":
            path = export_to_html(filename, output)
        else:
            path = export_to_pdf(filename, output)
        console.print(f"✅ Exported to: [bold green]{path}[/bold green]")
    except FileNotFoundError as e:
        console.print(f"❌ {e}", err=True)


@main.command()
@click.argument("filename")
@click.argument("query")
@click.option("--case-sensitive", is_flag=True, help="Case sensitive search")
def search(filename, query, case_sensitive):
    """Search for text in a markdown file."""
    try:
        results = search_in_file(filename, query, case_sensitive=case_sensitive)

        if not results:
            console.print("ℹ️ No matches found")
            return

        console.print(f"\n🔍 Found {len(results)} matches:\n")
        for line_num, line in results:
            console.print(f"  Line {line_num}: {line.strip()}")
    except FileNotFoundError as e:
        console.print(f"❌ {e}", err=True)


@main.command()
@click.argument("filename")
@click.argument("old-text")
@click.argument("new-text")
@click.option("--case-sensitive", is_flag=True, help="Case sensitive replacement")
def replace(filename, old_text, new_text, case_sensitive):
    """Replace text in a markdown file."""
    try:
        count = replace_in_file(filename, old_text, new_text, case_sensitive=case_sensitive)
        console.print(f"✅ Replaced {count} occurrences")
    except FileNotFoundError as e:
        console.print(f"❌ {e}", err=True)


if __name__ == "__main__":
    main()
