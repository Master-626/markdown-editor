"""Terminal Markdown tools for preview, export, search, and statistics."""

from .exporter import export_to_html, export_to_pdf
from .file_ops import create_new_file, get_file_stats, open_file, save_file
from .preview import preview_to_terminal, render_to_html, save_preview
from .search import replace_in_file, search_in_file
from .stats import analyze_markdown, extract_outline

__version__ = "0.1.0"
__author__ = "Xu Jiaqi"
__email__ = "jiaqixu12138@gmail.com"

__all__ = [
    "analyze_markdown",
    "create_new_file",
    "export_to_html",
    "export_to_pdf",
    "extract_outline",
    "get_file_stats",
    "open_file",
    "preview_to_terminal",
    "render_to_html",
    "replace_in_file",
    "save_file",
    "save_preview",
    "search_in_file",
]
