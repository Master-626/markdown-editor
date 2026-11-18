"""Search and replace stay literal and do not destroy the file."""


import pytest
from click.testing import CliRunner

from markdown_editor.cli import main
from markdown_editor.search import replace_in_file, search_in_file


def test_search_is_case_insensitive_by_default_and_reports_lines(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("Hello hello\nGoodbye\n")

    assert search_in_file(str(path), "HELLO") == [(1, "Hello hello")]
    assert search_in_file(str(path), "HELLO", case_sensitive=True) == []
    assert search_in_file(str(path), "hello", case_sensitive=True) == [(1, "Hello hello")]


def test_empty_search_does_not_match_every_line(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("Hello\nWorld\n")

    with pytest.raises(ValueError, match="must not be empty"):
        search_in_file(str(path), "")
    assert path.read_text() == "Hello\nWorld\n"


def test_empty_replace_does_not_modify_the_file(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("abc")

    with pytest.raises(ValueError, match="must not be empty"):
        replace_in_file(str(path), "", "X")

    assert path.read_text(encoding="utf-8") == "abc"


def test_case_insensitive_replace_is_literal(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("Cost is PRICE today")

    count = replace_in_file(str(path), "price", r"\1 usd", case_sensitive=False)

    assert count == 1
    assert path.read_text(encoding="utf-8") == r"Cost is \1 usd today"


def test_replace_preserves_crlf_and_skips_rewrites_without_a_match(tmp_path):
    path = tmp_path / "notes.md"
    path.write_bytes(b"Hello\r\nWorld\r\n")

    assert replace_in_file(str(path), "missing", "x") == 0
    assert path.read_bytes() == b"Hello\r\nWorld\r\n"

    assert replace_in_file(str(path), "world", "There", case_sensitive=False) == 1
    assert path.read_bytes() == b"Hello\r\nThere\r\n"


def test_replace_preserves_case_sensitive_backslashes(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("price")

    replace_in_file(str(path), "price", r"C:\notes", case_sensitive=True)

    assert path.read_text(encoding="utf-8") == r"C:\notes"


def test_missing_file_uses_a_clear_message(tmp_path):
    missing = tmp_path / "missing.md"

    with pytest.raises(FileNotFoundError, match="File not found"):
        search_in_file(str(missing), "Hello")
    with pytest.raises(FileNotFoundError, match="File not found"):
        replace_in_file(str(missing), "Hello", "Hi")


def test_cli_rejects_empty_replace_without_rewriting(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("abc")

    result = CliRunner().invoke(main, ["replace", str(path), "", "X"])

    assert result.exit_code == 1
    assert "must not be empty" in result.output
    assert "Traceback" not in result.output
    assert path.read_text(encoding="utf-8") == "abc"


def test_search_cli_reports_matching_lines(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("Hello Hello\n")

    result = CliRunner().invoke(main, ["search", str(path), "Hello"])

    assert result.exit_code == 0
    assert "Found 1 matching line:" in result.output
    assert "Found 1 matching lines" not in result.output
    assert "Line 1:" in result.output
