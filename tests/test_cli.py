"""CLI errors are reported without a traceback, and the public API imports."""


import pytest
from click.testing import CliRunner

from markdown_editor import (
    analyze_markdown,
    extract_outline,
    open_file,
    render_to_html,
    save_file,
)
from markdown_editor.cli import main
from markdown_editor.file_ops import create_new_file


def test_readme_api_imports_work(tmp_path):
    path = tmp_path / "document.md"
    save_file(str(path), "# Title\n\nHello [docs](http://example.com).\n")

    content = open_file(str(path))
    stats = analyze_markdown(content)
    html = render_to_html(content)
    outline = extract_outline(content)

    assert stats["total_words"] > 0
    assert "<h1" in html
    assert outline[0]["text"] == "Title"


def test_save_file_preserves_crlf(tmp_path):
    path = tmp_path / "notes.md"
    save_file(str(path), "Hello\r\nWorld\r\n")

    assert path.read_bytes() == b"Hello\r\nWorld\r\n"


@pytest.mark.parametrize(
    "args",
    [
        ["open", "missing.md"],
        ["stats", "missing.md"],
        ["search", "missing.md", "text"],
        ["replace", "missing.md", "old", "new"],
        ["outline", "missing.md"],
        ["preview", "missing.md"],
    ],
)
def test_missing_file_exits_nonzero_with_a_message(tmp_path, monkeypatch, args):
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(main, args)

    assert result.exit_code == 1
    assert "File not found" in result.output or "No such file" in result.output
    assert "Traceback" not in result.output
    assert "unexpected keyword argument" not in result.output


def test_new_refuses_existing_file_and_directory(tmp_path):
    existing = tmp_path / "notes.md"
    existing.write_text("keep")
    directory = tmp_path / "drafts.md"
    directory.mkdir()
    runner = CliRunner()

    file_result = runner.invoke(main, ["new", str(existing)])
    directory_result = runner.invoke(main, ["new", str(directory)])

    assert file_result.exit_code == 1
    assert "already exists" in file_result.output
    assert "Traceback" not in file_result.output
    assert existing.read_text(encoding="utf-8") == "keep"
    assert directory_result.exit_code == 1
    assert "already exists" in directory_result.output
    assert directory.is_dir()


def test_create_new_file_does_not_follow_a_dangling_symlink(tmp_path):
    target = tmp_path / "target.md"
    link = tmp_path / "link.md"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"This platform cannot create the test link: {error}")

    with pytest.raises(FileExistsError, match="already exists"):
        create_new_file(str(link))

    assert link.is_symlink()
    assert not target.exists()


def test_invalid_utf8_exits_nonzero_without_a_traceback(tmp_path):
    path = tmp_path / "notes.md"
    path.write_bytes(b"\xff\xfe")

    result = CliRunner().invoke(main, ["stats", str(path)])

    assert result.exit_code == 1
    assert "Traceback" not in result.output
    assert path.read_bytes() == b"\xff\xfe"


def test_outline_lists_headings_and_skips_code(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("# Title\n\n```\n# Hidden\n```\n\n## Section\n\nBody\n")

    result = CliRunner().invoke(main, ["outline", str(path)])

    assert result.exit_code == 0, result.output
    assert "Title" in result.output
    assert "Section" in result.output
    assert "Hidden" not in result.output
    assert "## Section" in result.output


def test_outline_of_a_document_without_headings(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("Just a paragraph.\n")

    result = CliRunner().invoke(main, ["outline", str(path)])

    assert result.exit_code == 0
    assert "No headings found" in result.output


def test_open_and_outline_show_brackets_literally(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("# [draft] Title\n\nSee [link](http://example.com).\n")
    runner = CliRunner()

    opened = runner.invoke(main, ["open", str(path)])
    outlined = runner.invoke(main, ["outline", str(path)])

    assert opened.exit_code == 0, opened.output
    assert "[draft] Title" in opened.output
    assert "[link](http://example.com)" in opened.output
    assert outlined.exit_code == 0, outlined.output
    assert "[draft] Title" in outlined.output


def test_new_missing_parent_and_open_directory_exit_nonzero(tmp_path):
    missing_parent = tmp_path / "missing" / "notes.md"
    directory = tmp_path / "folder.md"
    directory.mkdir()
    runner = CliRunner()

    new_result = runner.invoke(main, ["new", str(missing_parent)])
    open_result = runner.invoke(main, ["open", str(directory)])

    assert new_result.exit_code == 1
    assert open_result.exit_code == 1
    assert "Traceback" not in new_result.output
    assert "Traceback" not in open_result.output
    assert not missing_parent.exists()


def test_commands_are_listed_in_help():
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    for command in ("new", "open", "stats", "outline", "preview", "export", "search", "replace"):
        assert command in result.output


def test_version_matches_the_package():
    from markdown_editor import __version__

    result = CliRunner().invoke(main, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.output
