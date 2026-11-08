# Markdown Editor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Terminal Editor](https://img.shields.io/badge/terminal-editor-green.svg)]()

A full-featured terminal Markdown editor CLI with preview, export, and statistics. Professional-grade tool for writers and developers worldwide.

## 🌟 Features

- 📝 **Create & Edit** - Create and edit markdown files from the terminal
- 👁️ **Live Preview** - Render markdown to beautiful HTML
- 📊 **Statistics** - Word count, reading time, heading analysis
- 🔍 **Search & Replace** - Find and replace text in files
- 📤 **Export** - Export to HTML (PDF support planned)
- 🎨 **Rich Output** - Beautiful terminal UI with colors and tables
- 🐍 **Python API** - Use as a library in your code

## 📦 Installation

```bash
git clone https://github.com/Master-626/markdown-editor.git
cd markdown-editor
pip install .
```

## 🚀 Usage

### Create New File
```bash
mdedit new notes.md
```

### Open File
```bash
mdedit open notes.md
```

### View Statistics
```bash
mdedit stats README.md
```

### Preview as HTML
```bash
mdedit preview README.md
```

The preview is saved beside the source as `README_preview.html`. Only the
filename's final extension is replaced, so `.markdown`, `.MD`, extensionless
files, and directories containing `.md` are handled safely. The source is
never overwritten. If the output name already exists, a numbered name such as
`README_preview_1.html` is used instead; existing files and links are left alone.
Preview publication uses a hard link to avoid following existing output links
on any platform. Filesystems without hard-link support report an error rather
than risk overwriting or redirecting the output.

### Export to HTML
```bash
mdedit export README.md -o output.html --format html
```

### Search in File
```bash
mdedit search README.md "installation"
```

### Replace Text
```bash
mdedit replace README.md "old text" "new text"
```

## 🐍 Python API

```python
from markdown_editor import open_file, save_file, analyze_markdown, render_to_html

# Read and analyze
content = open_file("document.md")
stats = analyze_markdown(content)
print(f"Words: {stats['total_words']}, Reading time: {stats['reading_time_minutes']} min")

# Render to HTML
html = render_to_html(content)
```

## 🧪 Testing

```bash
pip install -e ".[dev]"
pytest
```

## 📄 License

MIT License
