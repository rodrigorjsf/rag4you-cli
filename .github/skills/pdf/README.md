# PDF to Markdown Extraction Skill

## Purpose

The **pdf skill** provides a robust, structure-aware extraction pipeline for converting PDF documents into clean Markdown files optimized for LLM consumption. This skill bridges the gap between unstructured PDF content and AI-ready text by preserving document structure—headings, tables, bold/italic formatting, and lists—while removing common PDF extraction artifacts.

**Core philosophy:** Extract PDFs to Markdown **files**, never dump raw PDF text directly into context windows. This ensures cleaner, more efficient processing and better token utilization.

---

## Quick Start (4 Steps)

```bash
# 1. Install dependency (one-time)
pip install pymupdf4llm

# 2. Extract PDF
bash ${SKILL_DIR}/scripts/extract-pdf.sh paper.pdf --output-dir /tmp

# 3. Capture path (if needed by agent)
OUTPUT=$(bash ${SKILL_DIR}/scripts/extract-pdf.sh paper.pdf --output-dir /tmp 2>/dev/null)

# 4. Read the generated Markdown
cat "$OUTPUT"
```

---

## Critical Gotchas

| Gotcha                                                          | Impact                                                                                            | Fix                                                  |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| **Pages are 0-indexed**                                         | Page 1 of the PDF is `--pages 0`                                                                  | Count from 0                                         |
| **Output overwrites existing files**                            | If `.md` exists with same name, it's replaced                                                     | Use `--output-name` to rename                        |
| **Default output writes beside the PDF**                        | May fail if that directory isn't writable                                                         | Use `--output-dir /tmp`                              |
| **`--include-images` creates huge files**                       | Image-heavy PDFs can become 100+ MB                                                               | Use only when needed                                 |
| **OCR requires tesseract**                                      | Without tesseract, scanned text is not readable; images are saved as files instead                | Install tesseract or accept visual-only output       |
| **`--no-images` and `--include-images` are mutually exclusive** | Script exits 1 with both flags                                                                    | Use one or neither                                   |
| **`assets/` dir created beside the output `.md`**               | LLM agents reading the `.md` need `assets/` in scope too                                          | Pass both the `.md` file and its `assets/` directory |
| **JPEG compression is content-aware**                           | Only applied to picture boxes ≥200k px where JPEG is ≥15% smaller; formula/table boxes always PNG | Trust the decision; check `stderr` for count         |

---

## Technology Stack

### Core Dependencies

| Component       | Purpose                                    | Version                  |
| --------------- | ------------------------------------------ | ------------------------ |
| **Python**      | Execution runtime                          | 3.8+                     |
| **pymupdf4llm** | Structure-aware PDF extraction library     | Latest                   |
| **pymupdf**     | Underlying PDF parsing engine              | Bundled with pymupdf4llm |
| **Bash**        | Script orchestration and argument handling | 3.0+                     |

### Requirements

Runs on any system with:

- **bash** (3.0+)
- **Python 3** (3.8+)
- **pymupdf4llm** (installed via pip)

Not limited to specific OSes, but requires bash + Python support.

### Why pymupdf4llm?

- **Structure awareness** — detects and preserves headings, lists, and tables (not just raw text)
- **Format preservation** — maintains bold, italic, code formatting
- **LLM-optimized** — output tuned for AI consumption (clean, minimal metadata)
- **Lightweight** — pure Python, minimal dependencies
- **Image handling** — optional base64 embedding for PDFs with mixed text and graphics

---

## Architecture

The skill consists of two core components:

### 1. **SKILL.md** (Metadata & Documentation)

- Declares the skill name, description, and usage guidance
- Contains quick reference tables, common mistakes, and limitations
- Acts as the user-facing documentation

### 2. **scripts/extract-pdf.sh** (Implementation)

A Bash wrapper that:

- Validates input parameters and file existence
- Checks for required Python dependencies
- Orchestrates the Python extraction engine
- Handles stdout/stderr separation (critical for capturing the output path)
- Implements post-processing cleanup

### 3. **Embedded Python Script** (Extract Engine)

Runs as a heredoc within the Bash script:

- Parses page range specifications (e.g., `0-5`, `0,2,4,10-15`)
- **Image extraction modes:**
  - **File mode (default):** uses `parse_document()` from `pymupdf4llm.helpers.document_layout`, then per-image 3-strategy waterfall: (1) OCR via tesseract if available → (2) visual save to `assets/` → (3) inline error sentinel. Never aborts on a per-image failure.
  - **Embed mode (`--include-images`):** calls `pymupdf4llm.to_markdown()` with base64 embedding
  - **Skip mode (`--no-images`):** calls `pymupdf4llm.to_markdown()` with `ignore_images=True`
- Applies optional intelligent JPEG compression (`--compress-images`): only `picture` boxes above 200k pixels, only when JPEG is ≥15% smaller than PNG
- Applies post-processing regex transformations
- Reports statistics to stderr (pages, chars, lines, image counts)
- Writes the final Markdown to disk

---

## How It Works (For Maintainers)

### Main Execution Flow

1. **Argument parsing** — Bash processes flags and validates PDF path exists
2. **Dependency check** — Verifies `pymupdf4llm` is installed
3. **Page range parsing** — Converts `--pages 0-5` into list `[0,1,2,3,4,5]`; `all` becomes `None`
4. **PDF extraction** — Python calls `pymupdf4llm.to_markdown()` with configured options
5. **Post-processing** — Five cleanup passes remove PDF artifacts (see below)
6. **Write to disk** — Markdown file written to output directory
7. **Report stats** — Statistics printed to stderr (pages, chars, lines)
8. **Output path** — Absolute path to `.md` file printed to stdout (captured by agents)

### Post-Processing Cleanup (5 Passes)

Raw pymupdf4llm output often contains PDF artifacts. The script cleans these:

| Pass | Pattern                                       | Behavior                                                    |
| ---- | --------------------------------------------- | ----------------------------------------------------------- |
| 1    | `\n{4,}` (4+ consecutive newlines)            | Reduces to `\n\n\n` (3 newlines = 2 blank lines)            |
| 2    | `\n\d{1,3}\s*\n` (isolated page numbers)      | Removes completely                                          |
| 3    | `(\w)-\s*\n(\w)` (hyphenation at line breaks) | Joins words: `word-\nnext` → `wordnext` (no space inserted) |
| 4    | `[ \t]+$` (trailing spaces/tabs)              | Removes per line                                            |
| 5    | File ending                                   | Ensures exactly one final newline (POSIX standard)          |

**Example:** PDFs often split words at column boundaries. Pass 3 rejoins them (without inserting spaces—this is intentional for compound words).

---

## How to Use

### Installation

**Option 1: Standard (system Python)**

```bash
pip install pymupdf4llm
```

**Option 2: Externally Managed Python (PEP 668)**

```bash
pip3 install --break-system-packages pymupdf4llm
```

**Check installation:**

```bash
python3 -c "import pymupdf4llm; print('✓ pymupdf4llm ready')"
```

### Basic Usage

#### Extract Full PDF

```bash
bash ${SKILL_DIR}/scripts/extract-pdf.sh research-paper.pdf
```

**Output:** Markdown file in same directory as PDF

```
research-paper.md (same directory)
```

#### Extract to Temporary Directory

```bash
OUTPUT=$(bash ${SKILL_DIR}/scripts/extract-pdf.sh research-paper.pdf --output-dir /tmp 2>/dev/null)
cat "$OUTPUT"
```

**Output:** `/tmp/research-paper.md`

#### Extract Specific Pages Only

```bash
# Pages 0-5 (first 6 pages, 0-indexed)
bash ${SKILL_DIR}/scripts/extract-pdf.sh report.pdf --pages 0-5 --output-dir /tmp

# Specific non-contiguous pages
bash ${SKILL_DIR}/scripts/extract-pdf.sh report.pdf --pages 0,3,7,10-15 --output-dir /tmp
```

#### Custom Output Filename

```bash
# Extract to "summary.md" instead of "report.md"
bash ${SKILL_DIR}/scripts/extract-pdf.sh report.pdf --output-name summary --output-dir /tmp
```

#### Include Images (Base64-Embedded)

```bash
# Embeds images directly in Markdown (can create large files)
bash ${SKILL_DIR}/scripts/extract-pdf.sh report.pdf --include-images --output-dir /tmp
```

#### Skip Images (Text-Only)

```bash
# Suppress all images — fast, minimal output
bash ${SKILL_DIR}/scripts/extract-pdf.sh report.pdf --no-images --output-dir /tmp
```

#### Extract with Image Compression

```bash
# Saves images to assets/, compresses large picture boxes to JPEG when beneficial
bash ${SKILL_DIR}/scripts/extract-pdf.sh report.pdf --compress-images --output-dir /tmp
```

#### Add Page Separators

```bash
# Adds "---" horizontal rules between pages (useful for tracking page boundaries)
bash ${SKILL_DIR}/scripts/extract-pdf.sh report.pdf --page-separators --output-dir /tmp
```

#### Combine Options

```bash
bash ${SKILL_DIR}/scripts/extract-pdf.sh research.pdf \
  --pages 0-20 \
  --output-name abstract \
  --output-dir /tmp \
  --page-separators \
  2>/dev/null
```

### Complete Workflow Example

**Scenario:** Extract and analyze the abstract from a 500-page dissertation.

```bash
#!/bin/bash

# Step 1: Extract only the first 10 pages (typically abstract + intro)
PDF="/path/to/dissertation.pdf"
OUTPUT=$(bash ${SKILL_DIR}/scripts/extract-pdf.sh "$PDF" \
  --pages 0-10 \
  --output-dir /tmp \
  --output-name dissertation-intro \
  2>/dev/null)

echo "Extracted to: $OUTPUT"

# Step 2: Read and display file stats
wc -l "$OUTPUT"
head -50 "$OUTPUT"

# Step 3: Use for analysis (pipe to LLM context)
cat "$OUTPUT"
```

---

## Script Parameters Reference

### Positional Arguments

| Argument     | Required | Type   | Description                        |
| ------------ | -------- | ------ | ---------------------------------- |
| `<pdf-path>` | Yes      | String | Path to PDF (relative or absolute) |

### Optional Flags

| Flag                   | Takes Value | Default                       | Description                                                                                          |
| ---------------------- | ----------- | ----------------------------- | ---------------------------------------------------------------------------------------------------- |
| `--output-dir <dir>`   | Yes         | Same directory as PDF         | Directory where `.md` file is written                                                                |
| `--output-name <name>` | Yes         | PDF filename (without `.pdf`) | Output filename stem (without `.md` extension)                                                       |
| `--pages <range>`      | Yes         | `all`                         | Pages to extract: `0-5`, `0,2,4,10-15`, or `all`                                                     |
| `--no-images`          | No          | Off                           | Skip all images; produce text-only output (mutually exclusive with `--include-images`)               |
| `--compress-images`    | No          | Off                           | Apply intelligent JPEG compression to large picture boxes (≥200k px; only when JPEG is ≥15% smaller) |
| `--include-images`     | No          | Off                           | Embed images as base64 inline (embed mode; mutually exclusive with `--no-images`)                    |
| `--page-separators`    | No          | Off                           | Add `---` horizontal rules between pages                                                             |
| `--help`               | No          | —                             | Show help and exit                                                                                   |

### Exit Codes

| Code | Meaning | Typical Cause                                                      |
| ---- | ------- | ------------------------------------------------------------------ |
| 0    | Success | File extracted and written                                         |
| 1    | Failure | Missing file, invalid params, missing dependency, extraction error |

---

## Output Contract

The script uses a **strict output contract** to ensure reliable parsing by agents:

### stdout (Captured by Agent)

```
/absolute/path/to/output.md
```

**Exactly one line:** the absolute path to the generated Markdown file.

### stderr (Not Captured, For Debugging)

```
Extracted 35/35 pages, 72,041 chars, 723 lines
  images: 3 saved, 0 compressed to JPEG
```

**Statistics about the extraction:** useful for debugging but not part of the output contract.

### Generated Markdown Structure

```markdown
# Document Title (or inferred)

## Section 1
Content with **bold**, *italic*, and `code`.

### Subsection 1.1
Lists are preserved:
- Item 1
- Item 2
  - Nested item

### Subsection 1.2
Tables render as Markdown:

| Header 1 | Header 2 |
| -------- | -------- |
| Cell 1   | Cell 2   |

## Section 2
...continued...
```

---

## Error Handling & Recovery

| Error                                                     | Cause                                                | Recovery                                                         |
| --------------------------------------------------------- | ---------------------------------------------------- | ---------------------------------------------------------------- |
| `ERROR: pymupdf4llm is not installed`                     | Dependency missing                                   | Run `pip install pymupdf4llm` and retry                          |
| `ERROR: File not found: /path/to/file.pdf`                | PDF path doesn't exist                               | Verify path and permissions                                      |
| `mkdir: cannot create directory`                          | Output dir not writable                              | Use `--output-dir /tmp` instead                                  |
| Malformed `--pages` (e.g., `abc`, `5-2`)                  | Invalid page range                                   | Use valid syntax: `0-5`, `0,2,4`, or `all`                       |
| `--include-images and --no-images are mutually exclusive` | Both flags passed together                           | Remove one flag                                                  |
| Minimal text output on scanned PDF                        | No tesseract installed and PDF is scanned            | Install tesseract for OCR support, or accept visual image output |
| `⚠️ Image extraction failed` in output                     | Per-image extraction error (region empty or corrupt) | Expected resilient behavior; rest of file is processed normally  |
| `pymupdf.FileError: cannot authenticate`                  | Encrypted PDF                                        | This skill doesn't support password-protected files              |

---

---

## Limitations & Constraints

### Hard Limits (by design)

| Limitation                                | Details                                                                                                                                                                                           | Workaround                                                      |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| **OCR requires tesseract**                | OCR (Strategy 1) is attempted per image when tesseract is installed; without it, images are saved as files (Strategy 2). Scanned text-only PDFs without images produce minimal output either way. | Install tesseract for OCR; otherwise accept visual image output |
| **No encryption**                         | Password-protected PDFs will fail                                                                                                                                                                 | Remove password protection first                                |
| **No layout/styling**                     | Colors, positioning, fonts are lost (text only)                                                                                                                                                   | For visual documents, review PDF directly                       |
| **`--compress-images` JPEG savings vary** | JPEG is only chosen when it is ≥15% smaller than PNG; solid-color or diagrammatic images often save as PNG anyway                                                                                 | Check stderr for `compressed to JPEG` count                     |
| **Large image files (embed mode)**        | Using `--include-images` on image-heavy PDFs can create 100+ MB Markdown                                                                                                                          | Use default file-mode or `--no-images`                          |
| **Table extraction**                      | Complex multi-level tables may not extract perfectly                                                                                                                                              | Always verify critical table data                               |
| **Font-based headings**                   | Heading detection relies on font size; unusual PDF formatting produces flat text                                                                                                                  | Manually restructure output if needed                           |

### Design Choices

| Constraint                      | Reason                                                                    |
| ------------------------------- | ------------------------------------------------------------------------- |
| **Always extract to file**      | Prevents dumping hundreds of KB into context windows; cleaner token usage |
| **Structure-aware, not visual** | Focuses on semantic content (headings, lists, tables) not layout          |
| **UTF-8 output only**           | Simplifies handling; covers 99.9% of real-world PDFs                      |

---

## Common Patterns & Examples

### Pattern 1: Research Paper Analysis

Extract a paper, analyze methodology, and summarize findings.

```bash
# Extract first 10 pages (abstract + methodology)
OUTPUT=$(bash ${SKILL_DIR}/scripts/extract-pdf.sh paper.pdf --pages 0-10 --output-dir /tmp 2>/dev/null)

# Read and analyze
cat "$OUTPUT" | head -100  # Preview

# Full analysis with context
cat "$OUTPUT"  # Pass to LLM for detailed analysis
```

### Pattern 2: Selective Multi-File Extraction

Extract key sections from multiple PDFs and combine.

```bash
for pdf in report1.pdf report2.pdf report3.pdf; do
  OUTPUT=$(bash ${SKILL_DIR}/scripts/extract-pdf.sh "$pdf" --output-dir /tmp 2>/dev/null)
  echo "## Source: $(basename $pdf)" >> combined.md
  cat "$OUTPUT" >> combined.md
  echo -e "\n---\n" >> combined.md
done

cat combined.md  # Pass combined content to LLM
```

### Pattern 3: Large Document with Page Boundaries

Extract sections separately, track page sources.

```bash
# Pages 1-50: Executive summary
bash ${SKILL_DIR}/scripts/extract-pdf.sh large.pdf --pages 0-50 \
  --output-name exec-summary --output-dir /tmp --page-separators 2>/dev/null

# Pages 51-100: Technical details
bash ${SKILL_DIR}/scripts/extract-pdf.sh large.pdf --pages 51-100 \
  --output-name technical-details --output-dir /tmp --page-separators 2>/dev/null

# Both files available for targeted analysis
```

---

## Maintenance & Troubleshooting

### Verify Installation

```bash
# Check Python availability
python3 --version  # Should be 3.8+

# Check pymupdf4llm
python3 -c "import pymupdf4llm; print('✓ Ready')"

# Test extraction
bash ${SKILL_DIR}/scripts/extract-pdf.sh test.pdf --output-dir /tmp
```

### Debugging Failed Extraction

```bash
# Run WITHOUT stderr redirection to see stats and errors
bash ${SKILL_DIR}/scripts/extract-pdf.sh problem.pdf

# Expected stderr output:
# Extracted 20/20 pages, 45,123 chars, 876 lines

# If no output, check:
# 1. Python version: python3 --version
# 2. Dependencies: python3 -c "import pymupdf4llm"
# 3. File permissions: ls -l problem.pdf
```

### Performance Tuning

| Scenario                       | Optimization                                  |
| ------------------------------ | --------------------------------------------- |
| Very large PDF (500+ pages)    | Use `--pages` to extract only needed sections |
| Memory-constrained environment | Avoid `--include-images` on large files       |
| Need fast preview              | Extract pages 0-10 only                       |
| Batch processing               | Loop with different `--output-dir` paths      |

---

## Integration with Other Tools

### Piping to grep

```bash
OUTPUT=$(bash ${SKILL_DIR}/scripts/extract-pdf.sh paper.pdf --output-dir /tmp 2>/dev/null)
grep -n "section\|chapter" "$OUTPUT"
```

### Word Count Analysis

```bash
OUTPUT=$(bash ${SKILL_DIR}/scripts/extract-pdf.sh report.pdf --output-dir /tmp 2>/dev/null)
wc -w "$OUTPUT"  # Word count
wc -l "$OUTPUT"  # Line count
```

### Combining with Other Skills

```bash
# Extract PDF, then pass Markdown to RAG system
OUTPUT=$(bash ${SKILL_DIR}/scripts/extract-pdf.sh doc.pdf --output-dir /tmp 2>/dev/null)
# Now use $OUTPUT with RAG indexing, similarity search, etc.
```

---

## License & Attribution

**pymupdf4llm** is part of the PyMuPDF ecosystem, licensed under AGPL 3.0 (with commercial licensing available).

For production use cases, verify licensing compliance:

- Open source projects: AGPL 3.0 compatible
- Commercial projects: Contact PyMuPDF for licensing

---

## See Also

- **pymupdf4llm GitHub:** <https://github.com/pymupdf/pymupdf4llm>
- **PyMuPDF Docs:** <https://pymupdf.readthedocs.io/>
- **SKILL.md** (in this directory): User-facing skill documentation with quick reference
- **extract-pdf.sh**: Implementation source code with inline comments
