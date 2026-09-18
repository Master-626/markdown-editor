"""
Export functionality.
"""

from pathlib import Path

from .preview import render_to_html


def export_to_html(input_path: str, output_path: str) -> Path:
    """Export markdown file to HTML."""
    from .file_ops import open_file

    content = open_file(input_path)
    html = render_to_html(content)

    output_p = Path(output_path)
    output_p.parent.mkdir(parents=True, exist_ok=True)
    output_p.write_text(html, encoding="utf-8")
    return output_p


def export_to_pdf(input_path: str, output_path: str) -> Path:
    """Export markdown file to PDF (placeholder - requires weasyprint or similar)."""
    # For now, just export to HTML as a fallback
    # Real implementation would use weasyprint or pdfkit
    html_output = output_path.replace(".pdf", ".html")
    export_to_html(input_path, html_output)

    # Return note that PDF conversion requires additional setup
    output_p = Path(output_path)
    output_p.write_text(
        f"PDF export placeholder. HTML file saved to: {html_output}\n"
        f"Install weasyprint for full PDF support.",
        encoding="utf-8"
    )
    return output_p
