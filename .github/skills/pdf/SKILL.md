---
name: pdf
description: Use when needing to read, extract, or convert PDF file content to Markdown — structure-aware extraction that preserves headings, tables, and formatting for efficient LLM processing
---

# PDF to Markdown Extraction

Convert PDF documents into clean Markdown files for LLM consumption. Uses `pymupdf4llm` for structure-aware extraction that preserves headings, tables, bold/italic, and lists.

**Core principle:** Extract PDF → Markdown **file** → read the `.md` file. Never dump raw PDF text directly into context.

## When to Use

- User references or tags a `.pdf` file for reading or analysis
- Task requires extracting text content from a PDF document
- Preparing PDF content (papers, reports, specs) for deeper analysis
- Converting documentation from PDF to Markdown format

## When NOT to Use

- File is already in a text-readable format (`.md`, `.txt`, `.html`)
- You only need metadata (title, page count) — use `pymupdf` directly
- PDF is fully scanned with no text layer and tesseract is unavailable — image extraction requires a readable image, OCR requires tesseract

## Core Rules

1. **Always extract to a file** — never pipe PDF text directly into your context window
2. **Capture stdout as the file path** — the script outputs only the absolute path to the generated `.md` file
3. **Read the generated `.md` file** after extraction using normal file-reading tools
4. **Use `--output-dir /tmp`** for temporary extractions that don't need to persist
5. **Install dependency first** if missing: `pip3 install pymupdf4llm`

## Quick Reference

| Goal | Command |
|------|---------|
| Extract full PDF | `bash ${SKILL_DIR}/scripts/extract-pdf.sh paper.pdf` |
| Extract to `/tmp` | `bash ${SKILL_DIR}/scripts/extract-pdf.sh paper.pdf --output-dir /tmp` |
| Extract pages 0-5 | `bash ${SKILL_DIR}/scripts/extract-pdf.sh paper.pdf --pages 0-5` |
| Extract specific pages | `bash ${SKILL_DIR}/scripts/extract-pdf.sh paper.pdf --pages 0,3,7` |
| Custom output name | `bash ${SKILL_DIR}/scripts/extract-pdf.sh paper.pdf --output-name summary` |
| Skip all images | `bash ${SKILL_DIR}/scripts/extract-pdf.sh paper.pdf --no-images` |
| Images with JPEG compression | `bash ${SKILL_DIR}/scripts/extract-pdf.sh paper.pdf --compress-images` |
| With images (base64 embed) | `bash ${SKILL_DIR}/scripts/extract-pdf.sh paper.pdf --include-images` |
| With page separators | `bash ${SKILL_DIR}/scripts/extract-pdf.sh paper.pdf --page-separators` |

`${SKILL_DIR}` resolves to this skill's directory at runtime. Use the appropriate platform convention to reference bundled files.

## Workflow

```
1. Run extraction script
   OUTPUT=$(bash ${SKILL_DIR}/scripts/extract-pdf.sh <pdf-path> --output-dir /tmp 2>/dev/null)

2. Capture the path (stdout = absolute path to .md file)
   echo "$OUTPUT"  →  /tmp/document-name.md

3. Read the generated markdown file
   view or cat "$OUTPUT"

4. Process/analyze the content as needed
```

**Important:** Use `2>/dev/null` to suppress stderr stats when capturing the path. Without it, stats like `Extracted 35/35 pages, 72041 chars` mix into the captured variable.

## Output Contract

| Channel | Content | Example |
|---------|---------|---------|
| **stdout** | Absolute path to generated `.md` file (one line) | `/tmp/paper.md` |
| **stderr** | Extraction stats (pages, chars, lines, images) | `Extracted 35/35 pages, 72,041 chars, 723 lines` / `images: 3 saved, 0 compressed to JPEG` |
| **Exit 0** | Success — file was created | |
| **Exit 1** | Failure — missing file, missing dependency, or extraction error | |

## Script Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `<pdf-path>` | Yes | — | Path to the PDF file |
| `--output-dir <dir>` | No | Same directory as PDF | Where to write the `.md` file |
| `--output-name <name>` | No | PDF filename (without `.pdf`) | Output filename (without `.md` extension) |
| `--pages <range>` | No | `all` | Pages to extract: `0-5`, `0,2,4,10-15`, or `all` |
| `--no-images` | No | Off | Skip all images; text-only output (mutually exclusive with `--include-images`) |
| `--compress-images` | No | Off | Apply intelligent JPEG compression to large picture boxes (≥200k px, ≥15% savings) |
| `--include-images` | No | Off | Embed images as base64 inline (embed mode; mutually exclusive with `--no-images`) |
| `--page-separators` | No | Off | Add `---` horizontal rules between pages |
| `--help` | No | — | Show usage information |

## Post-Processing

The script automatically cleans common PDF extraction artifacts:

- Collapses excessive blank lines (4+ → 2)
- Removes isolated page numbers on their own line
- Fixes broken hyphenation at line ends (`word-\nword` → `word\nword`)
- Strips trailing whitespace per line
- Ensures file ends with a single newline

## Dependency Installation

```bash
# Standard
pip install pymupdf4llm

# If system Python is externally managed (PEP 668)
pip3 install --break-system-packages pymupdf4llm
```

The script checks for `pymupdf4llm` at startup and exits with a clear error message if missing.

## Limitations

- **OCR is optional** — requires tesseract; without it, the script falls back to saving images as files; scanned text will not be readable as text
- **Encrypted PDFs** — password-protected files will fail at extraction
- **Large image PDFs** — using `--include-images` on image-heavy documents can produce very large Markdown files
- **Table accuracy** — complex multi-level tables may not extract perfectly; verify critical data
- **Font-based headings** — heading detection relies on font size/weight; unusual PDF formatting may produce flat text

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Dumping PDF text into context directly | Always extract to file first, then read the `.md` |
| Forgetting `2>/dev/null` when capturing path | `OUTPUT=$(bash script.sh file.pdf 2>/dev/null)` |
| Not installing `pymupdf4llm` | Run `pip install pymupdf4llm` before first use |
| Extracting to PDF's directory when it's read-only | Use `--output-dir /tmp` for writable location |
| Extracting all pages of a 500-page PDF | Use `--pages` to extract only what you need |
| Using `--include-images` and `--no-images` together | Flags are mutually exclusive; exit 1 |
| Forgetting `assets/` when handing `.md` to an LLM | File-mode extraction saves images to `assets/`; agents need both in scope |
