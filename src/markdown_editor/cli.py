"""
CLI interface for markdown-editor.
"""

import click
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .exporter import export_to_html, export_to_pdf
from .file_ops import create_new_file, open_file
from .preview import save_preview
from .search import replace_in_file, search_in_file
from .stats import analyze_markdown, extract_outline

console = Console()
error_console = Console(stderr=True)


def _fail(message: str) -> None:
    """Print a one-line error and exit. Rich's print() has no ``err`` argument."""
    error_console.print(f"❌ {message}", markup=False)
    raise SystemExit(1)


@click.group()
@click.version_option(version=__version__)
def main():
    """Markdown Editor - Full-featured terminal Markdown editor."""
    pass


@main.command()
@click.argument("filename")
def new(filename):
    """Create a new markdown file."""
    try:
        path = create_new_file(filename)
        console.print(f"✅ Created new file: [bold green]{escape(str(path))}[/bold green]")
    except (OSError, UnicodeError) as error:
        _fail(str(error))


@main.command("open")
@click.argument("filename")
def open_command(filename):
    """Open and display a markdown file."""
    try:
        content = open_file(filename)
        console.print(
            Panel(escape(content), title=escape(filename), border_style="blue")
        )
    except (OSError, UnicodeError) as error:
        _fail(str(error))


@main.command()
@click.argument("filename")
def stats(filename):
    """Show file statistics."""
    try:
        content = open_file(filename)
        stats_result = analyze_markdown(content)

        table = Table(title=escape(f"Statistics: {filename}"))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Words", str(stats_result["total_words"]))
        table.add_row("Characters", str(stats_result["total_characters"]))
        table.add_row("Lines", str(stats_result["total_lines"]))
        table.add_row("H1 Headings", str(stats_result["headings"]["h1"]))
        table.add_row("H2 Headings", str(stats_result["headings"]["h2"]))
        table.add_row("H3 Headings", str(stats_result["headings"]["h3"]))
        table.add_row("Code Blocks", str(stats_result["code_blocks"]))
        table.add_row("Links", str(stats_result["links"]))
        table.add_row("Images", str(stats_result["images"]))
        table.add_row("List Items", str(stats_result["list_items"]))
        table.add_row("Reading Time", f"{stats_result['reading_time_minutes']} min")

        console.print(table)
    except (OSError, UnicodeError) as error:
        _fail(str(error))


@main.command()
@click.argument("filename")
def outline(filename):
    """List headings with their levels and line numbers."""
    try:
        headings = extract_outline(open_file(filename))
    except (OSError, UnicodeError) as error:
        _fail(str(error))

    if not headings:
        console.print("ℹ️ No headings found")
        return

    table = Table(title=escape(f"Outline: {filename}"))
    table.add_column("Line", style="cyan", justify="right")
    table.add_column("Heading", style="green")
    for item in headings:
        indent = "  " * (item["level"] - 1)
        label = f"{indent}{'#' * item['level']} {item['text']}".rstrip()
        table.add_row(str(item["line"]), escape(label))
    console.print(table)


@main.command()
@click.argument("filename")
@click.option("--browser", is_flag=True, help="Open in browser (not implemented)")
def preview(filename, browser):
    """Preview markdown as HTML."""
    try:
        preview_file = save_preview(filename)

        console.print(
            f"✅ Preview saved to: [bold green]{escape(str(preview_file))}[/bold green]"
        )
        if browser:
            console.print("ℹ️ Open this file in your browser to view the preview")
    except (OSError, UnicodeError) as e:
        raise click.ClickException(str(e)) from e


@main.command()
@click.argument("filename")
@click.option(
    "-o",
    "--output",
    required=True,
    help="New output file path (existing files are never overwritten)",
)
@click.option(
    "--format",
    "output_format",
    default="html",
    type=click.Choice(["html", "pdf"]),
    help="Output format (PDF is not supported)",
)
def export(filename, output, output_format):
    """Export markdown to a new HTML file. PDF is not supported."""
    try:
        if output_format == "html":
            path = export_to_html(filename, output)
        else:
            path = export_to_pdf(filename, output)
        console.print(f"✅ Exported to: [bold green]{escape(str(path))}[/bold green]")
    except (OSError, UnicodeError, NotImplementedError) as e:
        raise click.ClickException(str(e)) from e


@main.command()
@click.argument("filename")
@click.argument("query")
@click.option("--case-sensitive", is_flag=True, help="Case sensitive search")
def search(filename, query, case_sensitive):
    """Search for literal text in a markdown file."""
    try:
        results = search_in_file(filename, query, case_sensitive=case_sensitive)
    except (OSError, UnicodeError, ValueError) as error:
        _fail(str(error))

    if not results:
        console.print("ℹ️ No matches found")
        return

    noun = "matching line" if len(results) == 1 else "matching lines"
    console.print(f"\n🔍 Found {len(results)} {noun}:\n")
    for line_num, line in results:
        console.print(f"  Line {line_num}: {line.strip()}", markup=False)


@main.command()
@click.argument("filename")
@click.argument("old-text")
@click.argument("new-text")
@click.option("--case-sensitive", is_flag=True, help="Case sensitive replacement")
def replace(filename, old_text, new_text, case_sensitive):
    """Replace literal text in a markdown file."""
    try:
        count = replace_in_file(filename, old_text, new_text, case_sensitive=case_sensitive)
        console.print(f"✅ Replaced {count} occurrences")
    except (OSError, UnicodeError, ValueError) as error:
        _fail(str(error))


if __name__ == "__main__":
    main()
