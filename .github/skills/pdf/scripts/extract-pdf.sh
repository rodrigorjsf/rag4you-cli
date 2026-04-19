#!/usr/bin/env bash
# ============================================================================
# extract-pdf.sh — PDF to Markdown extractor for LLM agents
#
# Extracts the full text content of a PDF file into a clean Markdown file
# optimized for LLM consumption. Uses pymupdf4llm for structure-aware
# extraction that preserves headings, tables, bold/italic, and lists.
#
# USAGE:
#   extract-pdf.sh <pdf-path> [options]
#
# PARAMETERS:
#   <pdf-path>              Path to the PDF file (required)
#   --output-dir <dir>      Directory for the output .md file (default: same as PDF)
#   --output-name <name>    Output filename without extension (default: PDF filename)
#   --pages <range>         Page range to extract: "0-5", "0,2,4", "all" (default: all)
#   --include-images        Embed images as base64 data URIs (overrides default file mode)
#   --no-images             Skip all images; text-only extraction
#   --compress-images       Compress large images to JPEG when smaller than PNG (default: off)
#   --page-separators       Add "---" separators between pages (default: off)
#   --help                  Show this help message
#
# IMAGE EXTRACTION MODES (mutually exclusive):
#   default                 Save images as files in assets/ subdirectory (![](assets/name.png))
#   --include-images        Embed images as base64 data URIs in the Markdown
#   --no-images             Omit all images from output
#
# OUTPUT:
#   Prints the absolute path to the generated Markdown file (and nothing else).
#   LLM agents can capture this path and use it to read the extracted content.
#
# DEPENDENCIES:
#   - Python 3.8+
#   - pymupdf4llm (pip install pymupdf4llm)
#   - tesseract (optional, enables OCR for scanned pages)
#
# EXAMPLES:
#   # Extract entire PDF to same directory (images saved to assets/)
#   ./scripts/extract-pdf.sh docs/paper.pdf
#
#   # Extract to specific output directory
#   ./scripts/extract-pdf.sh docs/paper.pdf --output-dir /tmp
#
#   # Extract only pages 0-5 with custom name
#   ./scripts/extract-pdf.sh docs/paper.pdf --pages 0-5 --output-name summary
#
#   # Extract with images saved as files and JPEG compression for large ones
#   ./scripts/extract-pdf.sh docs/paper.pdf --compress-images
#
#   # Text-only extraction (no images)
#   ./scripts/extract-pdf.sh docs/paper.pdf --no-images
#
#   # Embed images as base64 (legacy mode)
#   ./scripts/extract-pdf.sh docs/paper.pdf --include-images
# ============================================================================

set -euo pipefail

# --- Argument parsing ---
PDF_PATH=""
OUTPUT_DIR=""
OUTPUT_NAME=""
PAGES="all"
INCLUDE_IMAGES=false
NO_IMAGES=false
COMPRESS_IMAGES=false
PAGE_SEPARATORS=false

show_help() {
    sed -n '/^# USAGE:/,/^# ====/p' "$0" | sed 's/^# \?//'
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h)
            show_help
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --output-name)
            OUTPUT_NAME="$2"
            shift 2
            ;;
        --pages)
            PAGES="$2"
            shift 2
            ;;
        --include-images)
            INCLUDE_IMAGES=true
            shift
            ;;
        --no-images)
            NO_IMAGES=true
            shift
            ;;
        --compress-images)
            COMPRESS_IMAGES=true
            shift
            ;;
        --page-separators)
            PAGE_SEPARATORS=true
            shift
            ;;
        -*)
            echo "ERROR: Unknown option: $1" >&2
            echo "Run with --help for usage information." >&2
            exit 1
            ;;
        *)
            if [[ -z "$PDF_PATH" ]]; then
                PDF_PATH="$1"
            else
                echo "ERROR: Unexpected argument: $1" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

# --- Validation ---
if [[ -z "$PDF_PATH" ]]; then
    echo "ERROR: No PDF file specified." >&2
    echo "Usage: $0 <pdf-path> [options]" >&2
    echo "Run with --help for full usage." >&2
    exit 1
fi

if [[ "$INCLUDE_IMAGES" == "true" && "$NO_IMAGES" == "true" ]]; then
    echo "ERROR: --include-images and --no-images are mutually exclusive." >&2
    exit 1
fi

if [[ ! -f "$PDF_PATH" ]]; then
    echo "ERROR: File not found: $PDF_PATH" >&2
    exit 1
fi

# Resolve to absolute path
PDF_PATH="$(cd "$(dirname "$PDF_PATH")" && pwd)/$(basename "$PDF_PATH")"

# Defaults
if [[ -z "$OUTPUT_DIR" ]]; then
    OUTPUT_DIR="$(dirname "$PDF_PATH")"
fi

if [[ -z "$OUTPUT_NAME" ]]; then
    OUTPUT_NAME="$(basename "$PDF_PATH" .pdf)"
    OUTPUT_NAME="$(basename "$OUTPUT_NAME" .PDF)"
fi

OUTPUT_FILE="${OUTPUT_DIR}/${OUTPUT_NAME}.md"

# Create output directory if needed
mkdir -p "$OUTPUT_DIR"

# --- Dependency check ---
if ! python3 -c "import pymupdf4llm" 2>/dev/null; then
    echo "ERROR: pymupdf4llm is not installed." >&2
    echo "Install it with: pip install pymupdf4llm" >&2
    echo "Or: pip3 install --break-system-packages pymupdf4llm" >&2
    exit 1
fi

# --- Extraction ---
python3 - "$PDF_PATH" "$OUTPUT_FILE" "$PAGES" "$INCLUDE_IMAGES" "$PAGE_SEPARATORS" "$NO_IMAGES" "$COMPRESS_IMAGES" << 'PYTHON_SCRIPT'
import sys
import os
import re

import pymupdf
import pymupdf4llm
from pymupdf4llm.helpers.document_layout import parse_document

pdf_path = sys.argv[1]
output_file = sys.argv[2]
pages_arg = sys.argv[3]
include_images = sys.argv[4] == "true"
page_separators = sys.argv[5] == "true"
no_images = sys.argv[6] == "true"
compress_images = sys.argv[7] == "true"

# file-based image extraction is the default unless overridden
write_images_mode = not include_images and not no_images

# Compression constants
PIXEL_THRESHOLD = 200_000  # ~450x450px — below this, don't attempt compression
JPEG_QUALITY = 85           # high quality; avoids visible artefacts

pdf_stem = os.path.splitext(os.path.basename(pdf_path))[0]

output_dir = os.path.dirname(os.path.abspath(output_file))
output_file = os.path.abspath(output_file)  # must be absolute before any chdir
assets_dir = os.path.join(output_dir, "assets")

def check_ocr_available():
    try:
        pymupdf.get_tessdata()
        return True
    except RuntimeError:
        return False

ocr_available = check_ocr_available()

# Parse pages argument
pages = None
if pages_arg != "all":
    pages = []
    for part in pages_arg.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            pages.extend(range(int(start), int(end) + 1))
        else:
            pages.append(int(part))

# ── Legacy modes (base64 embed or text-only) ─────────────────────────────────
if not write_images_mode:
    kwargs = {
        "write_images": False,
        "embed_images": include_images,
        "ignore_images": no_images,
        "show_progress": False,
        "page_separators": page_separators,
        "force_text": True,
    }
    if pages is not None:
        kwargs["pages"] = pages

    md_text = pymupdf4llm.to_markdown(pdf_path, **kwargs)
    img_summary = "base64 embedded" if include_images else "skipped (--no-images)"

# ── File-based image extraction (default) ────────────────────────────────────
else:
    os.chdir(output_dir)

    parsed_doc = parse_document(
        pdf_path,
        filename=pdf_stem,
        write_images=False,
        embed_images=False,
        show_progress=False,
        force_text=True,
        pages=pages,
    )

    img_counts = {"saved": 0, "ocr": 0, "failed": 0, "compressed": 0}
    ocr_texts = {}  # idx -> (text, page_number_1based)

    mupdf_doc = pymupdf.open(pdf_path)

    for page_layout in parsed_doc.pages:
        page_num_1 = page_layout.page_number   # 1-based (from parse_document)
        page_obj = mupdf_doc[page_num_1 - 1]   # pymupdf uses 0-based index
        box_idx = 0

        for box in page_layout.boxes:
            if box.boxclass not in ("picture", "formula", "table-fallback"):
                continue
            box_idx += 1
            clip = pymupdf.Rect(box.x0, box.y0, box.x1, box.y1)

            # ── Strategy 1: OCR text ──────────────────────────────────────────
            ocr_text = None
            if ocr_available:
                try:
                    pix = page_obj.get_pixmap(clip=clip, dpi=300)
                    ocr_bytes = pix.pdfocr_tobytes(compress=False)
                    ocr_doc = pymupdf.open(stream=ocr_bytes, filetype="pdf")
                    ocr_text = ocr_doc.load_page(0).get_text("text").strip()
                    ocr_doc.close()
                    if len(ocr_text) < 4:
                        ocr_text = None
                except Exception:
                    ocr_text = None

            if ocr_text:
                idx = len(ocr_texts)
                ocr_texts[idx] = (ocr_text, page_num_1)
                box.image = f"__OCR_{idx}__"
                img_counts["ocr"] += 1
                continue

            # ── Strategy 2: Visual image save ────────────────────────────────
            try:
                pix = page_obj.get_pixmap(clip=clip, dpi=150)
                if pix.width == 0 or pix.height == 0:
                    raise ValueError("empty image region")

                # Compression decision (only for picture boxes, not formula/table)
                use_jpeg = False
                if compress_images and box.boxclass == "picture" and (pix.width * pix.height) > PIXEL_THRESHOLD:
                    png_bytes = pix.tobytes(output="png")
                    safe_pix = pymupdf.Pixmap(pix, 0) if pix.alpha else pix  # strip alpha for JPEG
                    jpg_bytes = safe_pix.tobytes(output="jpeg", jpg_quality=JPEG_QUALITY)
                    if len(jpg_bytes) < len(png_bytes) * 0.85:  # JPEG ≥15% smaller
                        use_jpeg = True

                ext = "jpg" if use_jpeg else "png"
                img_name = f"{pdf_stem}-{page_num_1:04d}-{box_idx:02d}.{ext}"
                os.makedirs(assets_dir, exist_ok=True)  # lazy: only if an image is actually saved
                img_path = os.path.join(assets_dir, img_name)

                if use_jpeg:
                    save_pix = pymupdf.Pixmap(pix, 0) if pix.alpha else pix
                    save_pix.save(img_path, jpg_quality=JPEG_QUALITY)
                    img_counts["compressed"] += 1
                else:
                    pix.save(img_path)

                box.image = f"assets/{img_name}"
                img_counts["saved"] += 1

            except Exception:
                # ── Strategy 3: Error placeholder ────────────────────────────
                box.image = f"__FAIL_p{page_num_1}_y{int(box.y0)}__"
                img_counts["failed"] += 1

    mupdf_doc.close()

    md_text = parsed_doc.to_markdown(
        write_images=False,
        embed_images=False,
        page_separators=page_separators,
    )

    # Replace OCR sentinels with blockquote text
    for idx, (text, page_n) in ocr_texts.items():
        md_text = md_text.replace(
            f"![](__OCR_{idx}__)",
            f"> *[Image OCR, page {page_n}]*\n> {text}",
        )

    # Replace error sentinels with readable warning
    md_text = re.sub(
        r'!\[\]\(__FAIL_p(\d+)_y(\d+)__\)',
        lambda m: (
            f"> ⚠️ *Image extraction failed — "
            f"page {m.group(1)}, ~{m.group(2)} pts from top*"
        ),
        md_text,
    )

    saved = img_counts["saved"]
    ocr_n = img_counts["ocr"]
    failed = img_counts["failed"]
    compressed = img_counts["compressed"]
    parts = [f"{saved} saved"]
    if ocr_n:
        parts.append(f"{ocr_n} OCR text")
    if compress_images:
        parts.append(f"{compressed} compressed to JPEG")
    if failed:
        parts.append(f"{failed} failed")
    img_summary = ", ".join(parts)

# ── Post-processing (all modes) ───────────────────────────────────────────────
# 1. Remove excessive blank lines (3+ → 2)
md_text = re.sub(r'\n{4,}', '\n\n\n', md_text)

# 2. Remove isolated page numbers on their own line
md_text = re.sub(r'\n\d{1,3}\s*\n', '\n', md_text)

# 3. Fix broken hyphenation at line ends (word- \nword → wordword\n)
md_text = re.sub(r'(\w)-\s*\n(\w)', r'\1\2\n', md_text)

# 4. Strip trailing whitespace on each line
md_text = re.sub(r'[ \t]+$', '', md_text, flags=re.MULTILINE)

# 5. Ensure file ends with single newline
md_text = md_text.rstrip() + '\n'

# Write output
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(md_text)

# Report stats to stderr
doc = pymupdf.open(pdf_path)
total_pages = len(doc)
extracted_pages = len(pages) if pages else total_pages
doc.close()

print(
    f"Extracted {extracted_pages}/{total_pages} pages, "
    f"{len(md_text):,} chars, {md_text.count(chr(10)):,} lines  |  "
    f"images: {img_summary}",
    file=sys.stderr,
)
PYTHON_SCRIPT

# --- Output: only the absolute path ---
echo "$(cd "$(dirname "$OUTPUT_FILE")" && pwd)/$(basename "$OUTPUT_FILE")"
