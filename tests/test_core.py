from markdown_editor.file_ops import create_new_file, open_file, save_file
from markdown_editor.preview import render_to_html
from markdown_editor.search import replace_in_file, search_in_file
from markdown_editor.stats import analyze_markdown


def test_create_new_file(tmp_path):
    """Test creating a new file."""
    file_path = tmp_path / "test.md"
    path = create_new_file(str(file_path))
    assert path.exists()
    assert "# New Document" in path.read_text()


def test_open_file(tmp_path):
    """Test opening a file."""
    file_path = tmp_path / "test.md"
    file_path.write_text("# Hello\nWorld")
    content = open_file(str(file_path))
    assert "Hello" in content


def test_save_file(tmp_path):
    """Test saving a file."""
    file_path = tmp_path / "test.md"
    save_file(str(file_path), "# Saved Content")
    assert "Saved Content" in file_path.read_text()


def test_analyze_markdown():
    """Test markdown analysis."""
    content = "# Title\n\n## Subtitle\n\nSome text with **bold** and [link](http://example.com)."
    stats = analyze_markdown(content)
    assert stats["total_words"] > 0
    assert stats["headings"]["h1"] == 1
    assert stats["headings"]["h2"] == 1
    assert stats["links"] == 1


def test_search_in_file(tmp_path):
    """Test searching in a file."""
    file_path = tmp_path / "test.md"
    file_path.write_text("Hello World\nHello Again\nGoodbye")
    results = search_in_file(str(file_path), "Hello")
    assert len(results) == 2


def test_replace_in_file(tmp_path):
    """Test replacing text in a file."""
    file_path = tmp_path / "test.md"
    file_path.write_text("Hello World\nHello Again")
    count = replace_in_file(str(file_path), "Hello", "Hi")
    assert count == 2
    assert "Hi World" in file_path.read_text()


def test_render_to_html():
    """Test markdown to HTML rendering."""
    html = render_to_html("# Hello World")
    assert "<h1" in html
    assert "<!DOCTYPE html>" in html
