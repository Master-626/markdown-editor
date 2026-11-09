"""Export must be honest about formats and must never destroy existing data."""

import os
from contextlib import contextmanager
from pathlib import Path

import pytest
from click.testing import CliRunner

from markdown_editor.cli import main
from markdown_editor.exporter import export_to_html, export_to_pdf
import markdown_editor.exporter as exporter_module


SOURCE = "# Keep this source\n\nPrivate draft: café 中文\n".encode("utf-8")


def run_export(source, output, output_format="html"):
    return CliRunner().invoke(
        main, ["export", str(source), "-o", str(output), "--format", output_format]
    )


def assert_export_failed(result):
    assert result.exit_code != 0
    assert "Error:" in result.output
    assert "Exported to:" not in result.output


def test_html_export_creates_complete_output_in_new_directory(tmp_path):
    source = tmp_path / "my notes 中文.MD"
    source.write_bytes(SOURCE)
    output = tmp_path / "exports.md" / "nested" / "result.html"

    result = export_to_html(str(source), str(output))

    assert result == output
    html = output.read_text(encoding="utf-8")
    assert html.startswith("<!DOCTYPE html>")
    assert html.endswith("</html>")
    assert "café 中文" in html
    assert source.read_bytes() == SOURCE
    assert set(output.parent.iterdir()) == {output}


def test_html_export_cli_accepts_relative_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("notes.markdown").write_bytes(SOURCE)

    result = run_export("notes.markdown", "out.html")

    assert result.exit_code == 0, result.output
    assert "Exported to:" in result.output
    assert Path("out.html").read_text(encoding="utf-8").endswith("</html>")
    assert Path("notes.markdown").read_bytes() == SOURCE


@pytest.mark.parametrize("kind", ["source", "file", "directory", "symlink", "hardlink", "dangling_symlink"])
def test_html_export_refuses_existing_output_without_changing_it(tmp_path, kind):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)
    output = source if kind == "source" else tmp_path / "out.html"
    missing_target = tmp_path / "missing.md"
    if kind == "file":
        output.write_bytes(b"Existing HTML must survive")
    elif kind == "directory":
        output.mkdir()
    elif kind in {"symlink", "hardlink", "dangling_symlink"}:
        try:
            if kind == "hardlink":
                os.link(source, output)
            else:
                output.symlink_to(missing_target if kind == "dangling_symlink" else source)
        except (OSError, NotImplementedError) as error:
            pytest.skip(f"This platform cannot create the test link: {error}")
    before = set(tmp_path.iterdir())

    result = run_export(source, output)

    assert_export_failed(result)
    assert "already exists" in result.output.lower()
    assert source.read_bytes() == SOURCE
    assert set(tmp_path.iterdir()) == before
    if kind == "file":
        assert output.read_bytes() == b"Existing HTML must survive"
    elif kind == "directory":
        assert output.is_dir()
    elif kind == "dangling_symlink":
        assert output.is_symlink()
        assert not missing_target.exists()
    else:
        assert output.samefile(source)


def test_html_export_library_reports_existing_output(tmp_path):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)

    with pytest.raises(FileExistsError, match="already exists"):
        export_to_html(str(source), str(source))

    assert source.read_bytes() == SOURCE


def test_repeated_export_preserves_previous_output(tmp_path):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)
    output = export_to_html(str(source), str(tmp_path / "out.html"))
    original = output.read_bytes()
    source.write_bytes(b"# Changed draft\n")

    result = run_export(source, output)

    assert_export_failed(result)
    assert output.read_bytes() == original
    assert source.read_bytes() == b"# Changed draft\n"
    assert set(tmp_path.iterdir()) == {source, output}


@pytest.mark.parametrize("kind", ["file", "symlink", "dangling_symlink", "directory"])
def test_html_publication_does_not_replace_concurrently_created_output(tmp_path, monkeypatch, kind):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)
    output = tmp_path / "out.html"
    missing_target = tmp_path / "missing.md"
    original_link = os.link

    def create_competing_output(staging, destination):
        assert destination == output
        if kind == "file":
            output.write_bytes(b"Concurrent output must survive")
        elif kind == "directory":
            output.mkdir()
            # Windows may report directory collisions as PermissionError.
            raise PermissionError("Output directory already exists")
        else:
            try:
                output.symlink_to(missing_target if kind == "dangling_symlink" else source)
            except (OSError, NotImplementedError) as error:
                pytest.skip(f"This platform cannot create the test link: {error}")
        return original_link(staging, destination)

    monkeypatch.setattr(os, "link", create_competing_output)

    result = run_export(source, output)

    assert_export_failed(result)
    assert "already exists" in result.output.lower()
    assert source.read_bytes() == SOURCE
    assert set(tmp_path.iterdir()) == {source, output}
    if kind == "file":
        assert output.read_bytes() == b"Concurrent output must survive"
    elif kind == "directory":
        assert output.is_dir()
    elif kind == "dangling_symlink":
        assert output.is_symlink()
        assert not missing_target.exists()
    else:
        assert output.is_symlink()
        assert output.samefile(source)


@pytest.mark.parametrize("kind", ["missing", "directory", "invalid_utf8"])
def test_invalid_input_creates_neither_output_nor_parent_directory(tmp_path, kind):
    source = tmp_path / "notes.md"
    output = tmp_path / "exports" / "out.html"
    if kind == "directory":
        source.mkdir()
    elif kind == "invalid_utf8":
        source.write_bytes(b"\xff\xfe")
    before = set(tmp_path.iterdir())

    result = run_export(source, output)

    assert_export_failed(result)
    assert set(tmp_path.iterdir()) == before
    if kind == "invalid_utf8":
        assert source.read_bytes() == b"\xff\xfe"


def test_output_parent_is_file_reports_clean_error(tmp_path):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)
    output_parent = tmp_path / "exports"
    output_parent.write_bytes(b"Keep this file")

    result = run_export(source, output_parent / "out.html")

    assert_export_failed(result)
    assert source.read_bytes() == SOURCE
    assert output_parent.read_bytes() == b"Keep this file"
    assert set(tmp_path.iterdir()) == {source, output_parent}


@pytest.mark.parametrize("error", [PermissionError("Cannot write export"), OSError("Hard links are not supported")])
def test_publication_failure_leaves_no_partial_output(tmp_path, monkeypatch, error):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)

    def fail_publication(staging, destination):
        raise error

    monkeypatch.setattr(os, "link", fail_publication)

    result = run_export(source, tmp_path / "out.html")

    assert_export_failed(result)
    assert str(error) in result.output
    assert source.read_bytes() == SOURCE
    assert set(tmp_path.iterdir()) == {source}


def test_html_is_complete_before_publication(tmp_path, monkeypatch):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)
    original_link = os.link

    def inspect_staging(staging, destination):
        assert staging.read_text(encoding="utf-8").endswith("</html>")
        assert not destination.exists()
        return original_link(staging, destination)

    monkeypatch.setattr(os, "link", inspect_staging)

    output = export_to_html(str(source), str(tmp_path / "out.html"))

    assert output.read_text(encoding="utf-8").endswith("</html>")
    assert set(tmp_path.iterdir()) == {source, output}


def test_staging_write_failure_is_cleaned_up(tmp_path, monkeypatch):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)
    original_temporary_file = exporter_module.NamedTemporaryFile

    @contextmanager
    def failing_temporary_file(*args, **kwargs):
        with original_temporary_file(*args, **kwargs) as stream:
            class FailingStream:
                name = stream.name

                def write(self, text):
                    stream.write(text[:10])
                    raise OSError("Export disk is full")

            yield FailingStream()

    monkeypatch.setattr(exporter_module, "NamedTemporaryFile", failing_temporary_file)

    result = run_export(source, tmp_path / "out.html")

    assert_export_failed(result)
    assert "Export disk is full" in result.output
    assert source.read_bytes() == SOURCE
    assert set(tmp_path.iterdir()) == {source}


def test_staging_creation_failure_preserves_source(tmp_path, monkeypatch):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)

    def deny_staging(*args, **kwargs):
        raise PermissionError("Cannot create export staging file")

    monkeypatch.setattr(exporter_module, "NamedTemporaryFile", deny_staging)

    result = run_export(source, tmp_path / "out.html")

    assert_export_failed(result)
    assert "Cannot create export staging file" in result.output
    assert source.read_bytes() == SOURCE
    assert set(tmp_path.iterdir()) == {source}


def test_post_publication_cleanup_failure_reports_created_output(tmp_path, monkeypatch):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)
    output = tmp_path / "out.html"
    original_unlink = Path.unlink

    def deny_staging_cleanup(path, *args, **kwargs):
        if path.name.startswith(".mdedit-export-"):
            raise PermissionError("Cleanup denied")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", deny_staging_cleanup)

    result = run_export(source, output)

    assert_export_failed(result)
    assert "HTML export was created at" in result.output
    assert "could not be removed: Cleanup denied" in result.output
    assert output.read_text(encoding="utf-8").endswith("</html>")
    assert source.read_bytes() == SOURCE
    staging_files = list(tmp_path.glob(".mdedit-export-*"))
    assert len(staging_files) == 1
    assert staging_files[0].samefile(output)


@pytest.mark.parametrize("filename", ["out.pdf", "out.PDF", "out", "directory.pdf/out.pdf", "new/nested/out.pdf", "notes.md"])
def test_pdf_cli_refuses_format_without_writing_anything(tmp_path, filename):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)
    before = set(tmp_path.rglob("*"))

    result = run_export(source, tmp_path / filename, "pdf")

    assert_export_failed(result)
    assert "PDF export is not supported" in result.output
    assert "--format html" in result.output
    assert source.read_bytes() == SOURCE
    assert set(tmp_path.rglob("*")) == before


def test_pdf_library_refuses_format_without_touching_files(tmp_path):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)
    output = tmp_path / "out.pdf"
    output.write_bytes(b"%PDF-1.7 existing file")
    sibling = tmp_path / "out.html"
    sibling.write_bytes(b"Existing HTML must survive")

    with pytest.raises(NotImplementedError, match="PDF export is not supported"):
        export_to_pdf(str(source), str(output))

    assert source.read_bytes() == SOURCE
    assert output.read_bytes() == b"%PDF-1.7 existing file"
    assert sibling.read_bytes() == b"Existing HTML must survive"
    assert set(tmp_path.iterdir()) == {source, output, sibling}


def test_export_help_discloses_unavailable_pdf_format():
    result = CliRunner().invoke(main, ["export", "--help"])

    assert result.exit_code == 0
    assert "PDF is not supported" in result.output
