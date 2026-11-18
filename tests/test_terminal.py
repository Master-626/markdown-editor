"""Terminal preview must not treat code, or Rich markup, as headings."""

from rich.console import Console

from markdown_editor.preview import preview_to_terminal


def _plain(markup: str) -> str:
    console = Console(force_terminal=False, color_system=None, width=80)
    with console.capture() as captured:
        console.print(markup)
    return captured.get()


def test_code_fence_headings_are_not_styled():
    preview = preview_to_terminal("```\n# not title\n```\n# Real\n")
    plain = _plain(preview)

    assert "[bold]not title[/bold]" not in preview
    assert "not title" in plain
    assert "Real" in plain
    assert preview.splitlines()[0].startswith("[dim]")


def test_heading_brackets_survive_rich_markup():
    plain = _plain(preview_to_terminal("# [draft] Title\n"))

    assert "[draft] Title" in plain


def test_hash_heading_without_a_space_is_rendered():
    plain = _plain(preview_to_terminal("#Title\n"))

    assert "Title" in plain


def test_list_marker_inside_a_fence_stays_literal():
    preview = preview_to_terminal("```\n- not a bullet\n```\n- real\n")
    plain = _plain(preview)

    assert "• not a bullet" not in plain
    assert "• real" in plain
