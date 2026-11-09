"""
Export functionality.
"""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from .preview import render_to_html


def export_to_html(input_path: str, output_path: str) -> Path:
    """Export to a new HTML file, refusing to replace existing files or links.

    The complete document is staged beside the destination before publication.
    Hard-link publication fails safely if another process creates the destination
    or if the filesystem does not support hard links.
    """
    from .file_ops import open_file

    content = open_file(input_path)
    html = render_to_html(content)

    output_p = Path(output_path)
    _ensure_output_absent(output_p)
    output_p.parent.mkdir(parents=True, exist_ok=True)
    staging = None
    published = False
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=str(output_p.parent),
            prefix=".mdedit-export-", suffix=".tmp", delete=False,
        ) as stream:
            staging = Path(stream.name)
            stream.write(html)

        try:
            # Unlike a check followed by write_text(), this cannot replace an
            # output that appears during export or follow its symlink target.
            os.link(staging, output_p)
            published = True
        except (FileExistsError, PermissionError):
            # Windows may report a directory collision as PermissionError.
            # Preserve the original permission error when no output exists.
            _ensure_output_absent(output_p)
            raise
    finally:
        if staging is not None:
            try:
                staging.unlink()
            except OSError as error:
                if published:
                    raise OSError(
                        f"HTML export was created at {output_p}, but temporary "
                        f"file {staging} could not be removed: {error}"
                    ) from error
                raise
    return output_p


def _ensure_output_absent(output_path: Path) -> None:
    """Check directory entries too, including dangling symlinks."""
    try:
        output_path.lstat()
    except FileNotFoundError:
        return
    raise FileExistsError(f"Output already exists: {output_path}. Choose a new output path.")


def export_to_pdf(input_path: str, output_path: str) -> Path:
    """Reject unsupported PDF export without reading or writing any files."""
    raise NotImplementedError(
        "PDF export is not supported. Export with --format html to a new .html "
        "file, then use your browser's Print / Save as PDF feature."
    )
