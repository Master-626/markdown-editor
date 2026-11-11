"""Statistics and outline follow the HTML preview."""

import markdown
import pytest

from markdown_editor.stats import analyze_markdown, extract_outline

EXTENSIONS = ["extra", "codehilite", "toc", "tables", "fenced_code"]


def test_images_are_not_counted_as_links():
    stats = analyze_markdown("![alt](a.png)\n\n[site](http://example.com)\n")

    assert stats["images"] == 1
    assert stats["links"] == 1


def test_fenced_code_is_not_counted_as_structure():
    content = """# Real

```python
# not heading
![nope](x.png)
[nope](http://x.test)
- not list
```

- real list
[yes](http://example.com)
"""
    stats = analyze_markdown(content)

    assert stats["headings"] == {"h1": 1, "h2": 0, "h3": 0, "h4+": 0}
    assert stats["images"] == 0
    assert stats["links"] == 1
    assert stats["list_items"] == 1
    assert stats["code_blocks"] == 1


def test_inline_code_and_prose_backticks_are_not_blocks():
    stats = analyze_markdown("See `[example](http://example.com)` and ``` not a fence ```.\n")

    assert stats["links"] == 0
    assert stats["code_blocks"] == 0


def test_closed_tilde_fences_are_code_blocks():
    stats = analyze_markdown("~~~\n# not heading\n~~~\n\n# Yes\n")

    assert stats["code_blocks"] == 1
    assert stats["headings"]["h1"] == 1


def test_unclosed_fence_stays_visible_text():
    stats = analyze_markdown("```\n# Yes\n- item\n")

    assert stats["code_blocks"] == 0
    assert stats["headings"]["h1"] == 1
    assert stats["list_items"] == 1


def test_longer_fence_is_not_closed_by_three_backticks():
    content = "````\n```\n# inside\n````\n# Yes\n"
    stats = analyze_markdown(content)

    assert stats["code_blocks"] == 1
    assert stats["headings"]["h1"] == 1


def test_atx_headings_allow_tabs_and_no_space():
    stats = analyze_markdown("#Title\n##\tSub\n###### Six\n####### Extra\n")

    assert stats["headings"]["h1"] == 1
    assert stats["headings"]["h2"] == 1
    assert stats["headings"]["h4+"] == 2
    outline = extract_outline("#Title\n##\tSub\n###### Six\n####### Extra\n")
    assert [(item["level"], item["text"]) for item in outline] == [
        (1, "Title"),
        (2, "Sub"),
        (6, "Six"),
        (6, "# Extra"),
    ]


def test_setext_and_blockquote_headings():
    content = "Title\n=====\n\n> Subtitle\n> -----\n\n> # Quoted\n"
    outline = extract_outline(content)

    assert [(item["level"], item["text"], item["line"]) for item in outline] == [
        (1, "Title", 1),
        (2, "Subtitle", 4),
        (1, "Quoted", 7),
    ]


def test_setext_list_marker_is_a_heading_not_a_list():
    stats = analyze_markdown("1. Title\n========\n")

    assert stats["headings"]["h1"] == 1
    assert stats["list_items"] == 0


def test_ordered_plus_and_nested_lists():
    content = "- a\n* b\n+ c\n1. d\n  - nested\n    - deeper\n\n    - code\n"
    stats = analyze_markdown(content)

    assert stats["list_items"] == 6


def test_indented_code_is_not_a_top_level_list():
    stats = analyze_markdown("    - code\n- real\n")

    assert stats["list_items"] == 1
    assert stats["code_blocks"] == 0


def test_reference_links_autolinks_and_undefined_references():
    content = (
        "Inline [in](http://a) and [ref][id] and <https://b> and <me@example.com>.\n"
        "\n"
        "[id]: http://id\n"
        "\n"
        "Shortcut [id] and missing [nope][missing].\n"
        "![pic][id]\n"
        "![missing][nope]\n"
    )
    stats = analyze_markdown(content)

    assert stats["links"] == 5
    assert stats["images"] == 1


def test_cjk_characters_count_as_words_without_changing_english_counts():
    assert analyze_markdown("one two three").get("total_words") == 3
    assert analyze_markdown("# Title\n\nHello").get("total_words") == 3
    assert analyze_markdown("hello, world").get("total_words") == 2
    assert analyze_markdown("你好").get("total_words") == 2
    assert analyze_markdown("你好 world").get("total_words") == 3
    assert analyze_markdown("你好。世界").get("total_words") == 4
    assert analyze_markdown("こんにちは").get("total_words") == 5
    assert analyze_markdown("한글").get("total_words") == 2


def test_reading_time_uses_the_word_count():
    english = analyze_markdown(" ".join(["word"] * 200))
    chinese = analyze_markdown("字" * 200)

    assert english["reading_time_minutes"] == 1.0
    assert chinese["reading_time_minutes"] == 1.0
    assert analyze_markdown("").get("reading_time_minutes") == 0.0


def test_crlf_document_keeps_heading_line_numbers():
    outline = extract_outline("# Title\r\n\r\n## Next\r\n")

    assert [item["line"] for item in outline] == [1, 3]


@pytest.mark.parametrize(
    "content",
    [
        "# Title\n\nParagraph [link](http://example.com) and ![alt](a.png).\n",
        "Title\n====\n\nSub\n----\n",
        "> # Quoted\n>\n> - item\n> 1. two\n",
        "```\n# no\n- no\n[no](http://no.test)\n```\n# Yes\n- yes\n",
        "~~~\ncode\n~~~\n\n+ one\n* two\n1. three\n",
        "See `[no](http://no.test)` and `# no`.\n\n[yes](http://yes.test)\n",
        "A [ref][id] and <https://example.com> and <a@b.co>.\n\n[id]: http://id\n",
        "#Title\n##\tSub\n\n- a\n  - b\n    - c\n",
        "1. Title\n========\n\n- real\n",
        "```python\nprint('hi')\n```\n\n#### Deep\n",
        "Not a heading\n\n---\n\n# After\n",
        "> Title\n> =====\n",
    ],
)
def test_counts_match_html_preview(content):
    html = markdown.markdown(content, extensions=EXTENSIONS)
    stats = analyze_markdown(content)

    assert stats["headings"]["h1"] == html.count("<h1")
    assert stats["headings"]["h2"] == html.count("<h2")
    assert stats["headings"]["h3"] == html.count("<h3")
    assert stats["headings"]["h4+"] == html.count("<h4") + html.count("<h5") + html.count("<h6")
    assert stats["links"] == html.count("<a ")
    assert stats["images"] == html.count("<img ")
    assert stats["list_items"] == html.count("<li")
