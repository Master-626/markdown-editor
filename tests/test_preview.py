"""Regression tests for preview path handling and source preservation."""

import os
from contextlib import contextmanager
from pathlib import Path

import pytest
from click.testing import CliRunner

import markdown_editor.preview as preview_module
from markdown_editor.cli import main
from markdown_editor.preview import save_preview

SOURCE = "# Keep this source\n\nPrivate draft: café 中文\n".encode("utf-8")


@pytest.mark.parametrize(
    "filename, output_name",
    [
        ("notes.md", "notes_preview.html"),
        ("notes.markdown", "notes_preview.html"),
        ("notes.MD", "notes_preview.html"),
        ("notes.MARKDOWN", "notes_preview.html"),
        ("notes", "notes_preview.html"),
        ("notes.txt", "notes_preview.html"),
        ("notes.md.backup", "notes.md_preview.html"),
        ("notes.md.md", "notes.md_preview.html"),
        ("notes_preview.html", "notes_preview_preview.html"),
        (".notes", ".notes_preview.html"),
        ("my notes 中文.md", "my notes 中文_preview.html"),
    ],
)
def test_preview_preserves_source_for_every_filename(tmp_path, filename, output_name):
    source = tmp_path / filename
    source.write_bytes(SOURCE)

    result = CliRunner().invoke(main, ["preview", str(source)])

    assert result.exit_code == 0, result.output
    assert source.read_bytes() == SOURCE
    html = (tmp_path / output_name).read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html
    assert "Keep this source" in html
    assert "café 中文" in html
    assert set(tmp_path.iterdir()) == {source, tmp_path / output_name}


def test_preview_does_not_replace_md_in_parent_directories(tmp_path):
    directory = tmp_path / "drafts.md" / "nested.md"
    directory.mkdir(parents=True)
    source = directory / "notes.md"
    source.write_bytes(SOURCE)

    result = CliRunner().invoke(main, ["preview", str(source)])

    assert result.exit_code == 0, result.output
    assert source.read_bytes() == SOURCE
    assert (directory / "notes_preview.html").exists()
    assert not (tmp_path / "drafts_preview.html").exists()


def test_preview_accepts_relative_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("notes.markdown").write_bytes(SOURCE)

    result = CliRunner().invoke(main, ["preview", "notes.markdown"])

    assert result.exit_code == 0, result.output
    assert Path("notes.markdown").read_bytes() == SOURCE
    assert Path("notes_preview.html").is_file()


def test_repeated_preview_preserves_existing_outputs(tmp_path):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)
    existing = tmp_path / "notes_preview.html"
    existing.write_bytes(b"Important existing HTML")
    occupied = tmp_path / "notes_preview_1.html"
    occupied.mkdir()

    first = save_preview(str(source))
    first_bytes = first.read_bytes()
    source.write_bytes(b"# Updated draft\n")
    second = save_preview(str(source))

    assert first == tmp_path / "notes_preview_2.html"
    assert second == tmp_path / "notes_preview_3.html"
    assert source.read_bytes() == b"# Updated draft\n"
    assert existing.read_bytes() == b"Important existing HTML"
    assert occupied.is_dir()
    assert first.read_bytes() == first_bytes
    assert b"Updated draft" in second.read_bytes()


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "dangling_symlink"])
def test_existing_output_links_are_not_followed(tmp_path, kind):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)
    output = tmp_path / "notes_preview.html"
    missing_target = tmp_path / "missing.md"
    try:
        if kind == "hardlink":
            os.link(str(source), str(output))
        else:
            output.symlink_to(missing_target if kind == "dangling_symlink" else source)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"This platform cannot create the test link: {error}")

    result = CliRunner().invoke(main, ["preview", str(source)])

    assert result.exit_code == 0, result.output
    assert source.read_bytes() == SOURCE
    assert (tmp_path / "notes_preview_1.html").is_file()
    if kind == "dangling_symlink":
        assert output.is_symlink()
        assert not missing_target.exists()
    else:
        assert output.read_bytes() == SOURCE
        assert output.samefile(source)


@pytest.mark.parametrize("kind", ["file", "dangling_symlink", "directory"])
def test_atomic_publication_preserves_a_concurrent_output(tmp_path, monkeypatch, kind):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)
    output = tmp_path / "notes_preview.html"
    missing_target = tmp_path / "missing.md"
    original_link = os.link

    def create_competing_output(staging, destination):
        if destination == output:
            if kind == "file":
                output.write_bytes(b"Another process created this file")
            elif kind == "directory":
                output.mkdir()
                # Simulate the Windows error for a raced directory.
                raise PermissionError("Directory already occupies this name")
            else:
                try:
                    output.symlink_to(missing_target)
                except (OSError, NotImplementedError) as error:
                    pytest.skip(f"This platform cannot create the test link: {error}")
        return original_link(staging, destination)

    monkeypatch.setattr(os, "link", create_competing_output)
    result = CliRunner().invoke(main, ["preview", str(source)])

    assert result.exit_code == 0, result.output
    assert source.read_bytes() == SOURCE
    if kind == "file":
        assert output.read_bytes() == b"Another process created this file"
    elif kind == "directory":
        assert output.is_dir()
    else:
        assert output.is_symlink()
        assert not missing_target.exists()
    assert (tmp_path / "notes_preview_1.html").is_file()
    assert not list(tmp_path.glob(".mdedit-preview-*"))


@pytest.mark.parametrize("kind", ["missing", "directory", "invalid_utf8"])
def test_invalid_input_exits_nonzero_without_creating_output(tmp_path, kind):
    source = tmp_path / "notes.md"
    if kind == "directory":
        source.mkdir()
    elif kind == "invalid_utf8":
        source.write_bytes(b"\xff\xfe")
    before = set(tmp_path.iterdir())

    result = CliRunner().invoke(main, ["preview", str(source)])

    assert result.exit_code != 0
    assert "Error:" in result.output
    assert "Preview saved" not in result.output
    assert set(tmp_path.iterdir()) == before
    if kind == "invalid_utf8":
        assert source.read_bytes() == b"\xff\xfe"


def test_output_permission_error_exits_nonzero_without_touching_source(tmp_path, monkeypatch):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)
    def deny_output(staging, destination):
        raise PermissionError("Cannot write preview")

    monkeypatch.setattr(os, "link", deny_output)
    result = CliRunner().invoke(main, ["preview", str(source)])

    assert result.exit_code != 0
    assert "Cannot write preview" in result.output
    assert "Preview saved" not in result.output
    assert source.read_bytes() == SOURCE
    assert set(tmp_path.iterdir()) == {source}


def test_unsupported_link_filesystem_fails_without_partial_output(tmp_path, monkeypatch):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)

    def unsupported_link(staging, destination):
        raise OSError("Hard links are not supported on this filesystem")

    monkeypatch.setattr(os, "link", unsupported_link)
    result = CliRunner().invoke(main, ["preview", str(source)])

    assert result.exit_code != 0
    assert "Hard links are not supported" in result.output
    assert "Preview saved" not in result.output
    assert source.read_bytes() == SOURCE
    assert set(tmp_path.iterdir()) == {source}


def test_preview_is_complete_before_publication(tmp_path, monkeypatch):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)
    original_link = os.link

    def inspect_staging(staging, destination):
        assert staging.read_text(encoding="utf-8").endswith("</html>")
        assert not destination.exists()
        return original_link(staging, destination)

    monkeypatch.setattr(os, "link", inspect_staging)

    output = save_preview(str(source))

    assert output.read_text(encoding="utf-8").endswith("</html>")
    assert source.read_bytes() == SOURCE
    assert not list(tmp_path.glob(".mdedit-preview-*"))


def test_staging_write_failure_is_cleaned_up(tmp_path, monkeypatch):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)
    original_temporary_file = preview_module.NamedTemporaryFile

    @contextmanager
    def failing_temporary_file(*args, **kwargs):
        with original_temporary_file(*args, **kwargs) as stream:
            class FailingStream:
                name = stream.name

                def write(self, text):
                    stream.write(text[:10])
                    raise OSError("Preview disk is full")

            yield FailingStream()

    monkeypatch.setattr(preview_module, "NamedTemporaryFile", failing_temporary_file)
    result = CliRunner().invoke(main, ["preview", str(source)])

    assert result.exit_code != 0
    assert "Preview disk is full" in result.output
    assert source.read_bytes() == SOURCE
    assert set(tmp_path.iterdir()) == {source}


def test_staging_creation_failure_preserves_source(tmp_path, monkeypatch):
    source = tmp_path / "notes.md"
    source.write_bytes(SOURCE)

    def denied_temporary_file(*args, **kwargs):
        raise PermissionError("Cannot create preview staging file")

    monkeypatch.setattr(preview_module, "NamedTemporaryFile", denied_temporary_file)
    result = CliRunner().invoke(main, ["preview", str(source)])

    assert result.exit_code != 0
    assert "Cannot create preview staging file" in result.output
    assert source.read_bytes() == SOURCE
    assert set(tmp_path.iterdir()) == {source}


def test_browser_option_still_saves_a_safe_preview(tmp_path):
    source = tmp_path / "notes.markdown"
    source.write_bytes(SOURCE)

    result = CliRunner().invoke(main, ["preview", str(source), "--browser"])

    assert result.exit_code == 0, result.output
    assert "Open this file in your browser" in result.output
    assert source.read_bytes() == SOURCE
    assert (tmp_path / "notes_preview.html").is_file()
