# Markdown Editor

## 简介

`markdown-editor`（命令 `mdedit`）是一个在终端里使用的 Markdown 工具。它可以新建和查看文件，统计字数、阅读时间和文档结构，按标题列出大纲，搜索和替换文本，以及生成 HTML 预览或导出。PDF 导出尚未实现。统计规则与 HTML 预览使用同一个 Markdown 引擎：已闭合的围栏代码块不会被当成标题、链接或列表；连续的中文、日文假名和韩文按每个字符计为一个词。下面是完整的英文说明。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)

## Purpose

`markdown-editor` is a small terminal toolkit for Markdown notes. It creates and displays files, reports writing statistics, lists a heading outline, searches and replaces literal text, and writes an HTML preview or export. It is a library as well as the `mdedit` and `markdown-editor` commands.

HTML rendering uses [Python-Markdown](https://python-markdown.github.io/) with the `extra`, `codehilite`, `toc`, `tables`, and `fenced_code` extensions. Statistics and the outline follow that preview, not a separate Markdown dialect.

## Installation

Python 3.8 or newer is required.

```bash
git clone https://github.com/Master-626/markdown-editor.git
cd markdown-editor
pip install .
```

Install the test and lint tools with the development extra:

```bash
pip install -e ".[dev]"
```

## Usage

```bash
mdedit --help
mdedit --version
```

`markdown-editor` accepts the same commands. Paths may be relative or absolute. The filename is used as given; a `.md` extension is not added for you. Failed commands exit with status 1 and print a one-line error.

### Create a file

```bash
mdedit new notes.md
```

This writes a short starter document. If `notes.md` already exists, is a directory, or is a symlink (including a dangling symlink), the command stops and leaves that path unchanged.

### Show a file

```bash
mdedit open notes.md
```

The file is printed literally. Square brackets in the document are not treated as terminal formatting.

### Statistics

```bash
mdedit stats notes.md
```

The report includes:

| Metric | Meaning |
| --- | --- |
| Words | Whitespace-separated words, plus one word for each Chinese, Japanese kana, or Hangul character. English counts match `str.split` after those characters are removed. |
| Characters | Unicode code points, including whitespace. |
| Lines | Logical lines. |
| H1, H2, H3 | ATX and setext headings at that level, including headings in blockquotes. Deeper headings are not separate rows; `analyze_markdown()` reports them as `h4+`, and `mdedit outline` lists every level. |
| Code blocks | Closed fenced blocks opened by a line-start `` ``` `` or `~~~`. |
| Links | Inline links, reference links that resolve, autolinks, and email addresses. Images are not links. |
| Images | Inline images and image references that resolve. |
| List items | `-`, `*`, `+`, and `1.` items, including items in blockquotes. A marker indented by four spaces counts only while a list is already open; otherwise it is indented code. |
| Reading time | `words / 200`, rounded to one decimal place. |

Closed fenced code is ignored for headings, links, images, and list items. An unclosed fence is ordinary text, as it is in the HTML preview. Single-line inline code is ignored for those counts too.

### Outline

```bash
mdedit outline notes.md
```

This prints each heading's line number, level, and text. Headings inside closed fenced code are omitted. A document with no headings prints `No headings found`.

```markdown
# Title

## Section
```

```text
Line  Heading
   1  # Title
   3    ## Section
```

### Preview

```bash
mdedit preview notes.md
mdedit preview notes.md --browser
```

`--browser` does not launch a browser. It reminds you to open the saved file yourself.

The preview is written next to the source as `notes_preview.html`. Only the filename's final extension is replaced, so `.markdown`, `.MD`, extensionless files, and directories whose names contain `.md` stay intact. The source is never overwritten. If that output name already exists, including as a directory or a symlink, a numbered name such as `notes_preview_1.html` is used. Publication uses a hard link so an existing output symlink is not followed. Filesystems without hard-link support report an error instead of writing a partial file.

### Export

```bash
mdedit export notes.md -o output.html --format html
```

| Option | Required | Description |
| --- | --- | --- |
| `-o`, `--output` | yes | New output path. Existing files, directories, and links are never overwritten. |
| `--format` | no | `html` (default) or `pdf`. |

PDF export is not implemented. `--format pdf` exits with an error and does not create or change files. Export HTML and use the browser's Print / Save as PDF instead. The library call `export_to_pdf()` raises `NotImplementedError` and does not write a placeholder.

HTML export writes the complete document to a temporary file beside the destination, then publishes it with a hard link. If the destination appears while the export is running, or the filesystem cannot create a hard link, the command fails and does not replace anything that is already there.

### Search

```bash
mdedit search notes.md "installation"
mdedit search notes.md "TODO" --case-sensitive
```

Search is literal, not a regular expression. Matching is case-insensitive unless `--case-sensitive` is set. Each matching line is reported once, even when the text occurs twice on that line. An empty query is rejected.

### Replace

```bash
mdedit replace notes.md "old text" "new text"
mdedit replace notes.md "TODO" "DONE" --case-sensitive
```

Replacement is literal in both case-sensitive and case-insensitive mode, so backslashes in the new text stay as written. Existing newline characters are preserved. The file is left untouched when nothing changes. An empty search string is rejected instead of being inserted between characters.

## Python API

```python
from markdown_editor import (
    analyze_markdown,
    extract_outline,
    open_file,
    render_to_html,
    save_file,
)

content = open_file("document.md")
stats = analyze_markdown(content)
print(stats["total_words"], stats["reading_time_minutes"])

for heading in extract_outline(content):
    print(heading["line"], heading["level"], heading["text"])

save_file("copy.md", content)
html = render_to_html(content)
```

`save_file()` writes the string it is given, including `\n` or `\r\n`. `extract_outline()` returns dictionaries with `level`, `text`, and `line`.

## Tests and lint

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

GitHub Actions runs Ruff, then pytest on Python 3.8 through 3.13. The 3.8 job uses Ubuntu 22.04; 3.13 is also run on macOS and Windows. The workflow installs the package, checks dependencies, builds a wheel, and runs `mdedit --help`.

## License

MIT License. See [LICENSE](LICENSE).
