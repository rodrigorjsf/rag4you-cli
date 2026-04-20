from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bench.target import RagTarget, SearchChunk, _parse_result_block


# ── _parse_result_block unit tests ───────────────────────────────────────────


def _block(*lines: str) -> str:
    return "\n".join(lines)


def test_parse_block_basic():
    block = _block(
        "### Result 1 — `docs/skills.md` [score: 0.0123]",
        "",
        "```",
        "Skills are reusable units.",
        "```",
    )
    chunk = _parse_result_block(block, "docs")
    assert chunk is not None
    assert chunk.file_path == "docs/skills.md"
    assert pytest.approx(chunk.score) == 0.0123
    assert chunk.start_line is None
    assert chunk.content == "Skills are reusable units."
    assert chunk.collection == "docs"
    assert chunk.section_header is None


def test_parse_block_with_lines_and_section():
    block = _block(
        "### Result 1 — `docs/guide.md` (lines 10-20) [score: 0.0500]",
        "**Section**: Introduction",
        "",
        "```",
        "Welcome to the guide.",
        "```",
    )
    chunk = _parse_result_block(block, "docs")
    assert chunk is not None
    assert chunk.start_line == 10
    assert chunk.end_line == 20
    assert chunk.section_header == "Introduction"
    assert chunk.content == "Welcome to the guide."


def test_parse_block_code_language_symbol():
    block = _block(
        "### Result 1 — `rag/search.py` (lines 45-60) [score: 0.0200]",
        "**Language: python | Symbol: SearchEngine.search**",
        "",
        "```",
        "def search(self, query): ...",
        "```",
    )
    chunk = _parse_result_block(block, "code")
    assert chunk is not None
    assert chunk.language == "python"
    assert chunk.symbol_name == "SearchEngine.search"


def test_parse_block_collection_override():
    block = _block(
        "### Result 1 — `docs/readme.md` [score: 0.0300]",
        "**Collection**: docs",
        "",
        "```",
        "Some content.",
        "```",
    )
    chunk = _parse_result_block(block, "all")
    assert chunk is not None
    assert chunk.collection == "docs"


def test_parse_block_nested_code_block():
    """Embedded ``` blocks inside content must be preserved."""
    block = _block(
        "### Result 1 — `docs/guide.md` [score: 0.0100]",
        "",
        "```",
        "# Title",
        "",
        "```python",
        "def foo(): pass",
        "```",
        "",
        "More text.",
        "```",
    )
    chunk = _parse_result_block(block, "docs")
    assert chunk is not None
    assert "```python" in chunk.content
    assert "def foo(): pass" in chunk.content
    assert "More text." in chunk.content


def test_parse_block_malformed_no_fence_returns_none():
    block = _block(
        "### Result 1 — `docs/x.md` [score: 0.0100]",
        "No fence here at all",
    )
    chunk = _parse_result_block(block, "docs")
    assert chunk is None


def test_parse_block_bad_header_returns_none():
    block = _block(
        "## Not a result header",
        "```",
        "content",
        "```",
    )
    chunk = _parse_result_block(block, "docs")
    assert chunk is None


# ── RagTarget.parse_search_output ────────────────────────────────────────────


def test_parse_output_empty_string():
    assert RagTarget.parse_search_output("", "docs") == []


def test_parse_output_no_results_message():
    out = "No results found in docs."
    assert RagTarget.parse_search_output(out, "docs") == []


def test_parse_output_single_result():
    out = textwrap.dedent("""\
        ## Search Results (docs)

        ### Result 1 — `docs/readme.md` [score: 0.0150]
        **Section**: Overview

        ```
        This is the overview.
        ```
    """)
    chunks = RagTarget.parse_search_output(out, "docs")
    assert len(chunks) == 1
    assert chunks[0].file_path == "docs/readme.md"
    assert "overview" in chunks[0].content.lower()


def test_parse_output_multiple_results():
    out = textwrap.dedent("""\
        ## Search Results (docs)

        ### Result 1 — `docs/a.md` [score: 0.0200]

        ```
        Content A.
        ```

        ### Result 2 — `docs/b.md` [score: 0.0100]

        ```
        Content B.
        ```
    """)
    chunks = RagTarget.parse_search_output(out, "docs")
    assert len(chunks) == 2
    assert chunks[0].file_path == "docs/a.md"
    assert chunks[1].file_path == "docs/b.md"


def test_parse_output_cross_collection():
    out = textwrap.dedent("""\
        ## Search Results (all)

        ### Result 1 — `docs/a.md` [score: 0.9000]
        **Collection**: docs

        ```
        Doc content.
        ```

        ### Result 2 — `src/b.py` (lines 5-15) [score: 0.8000]
        **Language: python | Symbol: foo**
        **Collection**: code

        ```
        def foo(): pass
        ```
    """)
    chunks = RagTarget.parse_search_output(out, "all")
    assert len(chunks) == 2
    assert chunks[0].collection == "docs"
    assert chunks[1].collection == "code"
    assert chunks[1].language == "python"
    assert chunks[1].symbol_name == "foo"
    assert chunks[1].start_line == 5


# ── RagTarget.generate_config ─────────────────────────────────────────────────


def test_generate_config_writes_yaml(tmp_path):
    toolkit = tmp_path / "toolkit"
    (toolkit / "rag").mkdir(parents=True)
    state_dir = tmp_path / ".bench-state" / "run-001"
    state_dir.mkdir(parents=True)

    template_path = (
        Path(__file__).parent.parent / "templates" / "toolkit-rag.config.yaml.j2"
    )
    assert template_path.exists(), "Template file missing"

    target = RagTarget(toolkit_path=toolkit, state_dir=state_dir)

    context = {
        "config_id": "docs-c512-bge-small",
        "project_name": "test-project",
        "collection_name": "docs",
        "collection_description": "Docs",
        "model": "BAAI/bge-small-en-v1.5",
        "dimensions": 384,
        "sources": [
            {
                "path": str(tmp_path / "corpus" / "docs"),
                "patterns": ["*.md"],
                "recursive": True,
                "chunking": None,
            }
        ],
        "chunking_strategy": "markdown_header",
        "chunking_max_tokens": 512,
        "chunking_overlap_tokens": 256,
        "chunking_max_chars": None,
        "chunking_split_headers": ["h1", "h2", "h3"],
        "chunking_languages": None,
        "model_cache_dir": str(tmp_path / "model-cache"),
        "search_default_top_k": 5,
        "search_max_top_k": 10,
        "search_rrf_k": 60,
        "search_vector_candidates": 20,
        "search_fts_candidates": 20,
    }

    cfg_path = target.generate_config("docs-c512-bge-small", context, template_path)
    assert cfg_path.exists()

    import yaml

    rendered = yaml.safe_load(cfg_path.read_text())
    assert rendered["project"]["name"] == "test-project"
    col = rendered["collections"]["docs"]
    assert col["embedding"]["model"] == "BAAI/bge-small-en-v1.5"
    assert col["chunking"]["max_tokens"] == 512
    assert rendered["database"]["path"] == ".rag/knowledge.db"


# ── RagTarget.search (mocked subprocess) ─────────────────────────────────────


def _make_target(tmp_path: Path) -> tuple[RagTarget, Path]:
    toolkit = tmp_path / "toolkit"
    (toolkit / "rag").mkdir(parents=True)
    state_dir = tmp_path / ".bench-state" / "run-mock"
    state_dir.mkdir(parents=True)
    target = RagTarget(toolkit_path=toolkit, state_dir=state_dir)
    cfg = state_dir / "configs" / "cfg-001" / "rag.config.yaml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("# placeholder\n")
    return target, cfg


def test_search_returns_parsed_chunks(tmp_path):
    target, cfg = _make_target(tmp_path)

    mock_stdout = textwrap.dedent("""\
        ## Search Results (docs)

        ### Result 1 — `docs/readme.md` [score: 0.0500]

        ```
        Hello world.
        ```
    """)

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = mock_stdout
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        chunks = target.search(cfg, "hello", collection="docs", top_k=5)

    assert len(chunks) == 1
    assert chunks[0].file_path == "docs/readme.md"
    assert "Hello world" in chunks[0].content


def test_search_raises_on_nonzero_returncode(tmp_path):
    target, cfg = _make_target(tmp_path)

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "Error: config not found"

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="rag search failed"):
            target.search(cfg, "query")


def test_index_returns_index_result(tmp_path):
    from bench.target import IndexResult

    target, cfg = _make_target(tmp_path)

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        result = target.index(cfg, collection="docs")

    assert isinstance(result, IndexResult)
    assert result.returncode == 0
    assert result.collection == "docs"
    assert result.wall_time_s >= 0.0


def test_search_chunk_to_dict():
    chunk = SearchChunk(
        file_path="docs/a.md",
        content="hello",
        score=0.5,
        collection="docs",
    )
    d = chunk.to_dict()
    assert d["file_path"] == "docs/a.md"
    assert d["score"] == 0.5
    assert d["source"] == "rrf"
