from __future__ import annotations

from pathlib import Path

import yaml
import pytest

from bench.corpus import CorpusFile, CorpusLoader


def _write_config(config_path: Path, sources: list[dict]) -> None:
    config = {
        "project": {"name": "test"},
        "collections": {
            "docs": {
                "embedding": {"model": "BAAI/bge-small-en-v1.5", "dimensions": 384},
                "sources": sources,
                "chunking": {"strategy": "markdown_header", "max_tokens": 512},
            }
        },
        "shared": {"cache_dir": ".rag/models"},
        "database": {"path": ".rag/knowledge.db"},
        "search": {
            "default_top_k": 5,
            "max_top_k": 10,
            "rrf_k": 60,
            "vector_candidates": 20,
            "fts_candidates": 20,
        },
    }
    config_path.write_text(yaml.dump(config), encoding="utf-8")


# ── enumerate_from_config ─────────────────────────────────────────────────────


def test_enumerate_from_config_finds_markdown_files(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "a.md").write_text("# A\nHello.", encoding="utf-8")
    (corpus / "b.md").write_text("# B\nWorld.", encoding="utf-8")
    (corpus / "ignore.txt").write_text("not indexed")

    config_path = tmp_path / "rag.config.yaml"
    _write_config(
        config_path,
        [{"path": str(corpus), "patterns": ["*.md"], "recursive": False}],
    )

    loader = CorpusLoader(tmp_path)
    files = loader.enumerate_from_config(config_path)

    assert len(files) == 2
    assert all(isinstance(f, CorpusFile) for f in files)
    paths = {f.path for f in files}
    assert any("a.md" in p for p in paths)
    assert any("b.md" in p for p in paths)


def test_enumerate_recursive(tmp_path):
    corpus = tmp_path / "docs"
    sub = corpus / "sub"
    sub.mkdir(parents=True)
    (corpus / "top.md").write_text("top")
    (sub / "nested.md").write_text("nested")

    config_path = tmp_path / "rag.config.yaml"
    _write_config(
        config_path,
        [{"path": str(corpus), "patterns": ["*.md"], "recursive": True}],
    )

    loader = CorpusLoader(tmp_path)
    files = loader.enumerate_from_config(config_path)

    assert len(files) == 2


def test_enumerate_non_recursive(tmp_path):
    corpus = tmp_path / "docs"
    sub = corpus / "sub"
    sub.mkdir(parents=True)
    (corpus / "top.md").write_text("top")
    (sub / "nested.md").write_text("nested")

    config_path = tmp_path / "rag.config.yaml"
    _write_config(
        config_path,
        [{"path": str(corpus), "patterns": ["*.md"], "recursive": False}],
    )

    loader = CorpusLoader(tmp_path)
    files = loader.enumerate_from_config(config_path)

    assert len(files) == 1
    assert "top.md" in files[0].path


def test_enumerate_missing_source_dir_skipped(tmp_path):
    config_path = tmp_path / "rag.config.yaml"
    _write_config(
        config_path,
        [{"path": str(tmp_path / "nonexistent"), "patterns": ["*.md"], "recursive": True}],
    )

    loader = CorpusLoader(tmp_path)
    files = loader.enumerate_from_config(config_path)

    assert files == []


def test_enumerate_deduplicates_files(tmp_path):
    """Same file matched by two sources → appears once."""
    corpus = tmp_path / "docs"
    corpus.mkdir()
    (corpus / "file.md").write_text("content")

    config_path = tmp_path / "rag.config.yaml"
    config = {
        "project": {"name": "test"},
        "collections": {
            "docs": {
                "embedding": {"model": "BAAI/bge-small-en-v1.5", "dimensions": 384},
                "sources": [
                    {"path": str(corpus), "patterns": ["*.md"], "recursive": False},
                    {"path": str(corpus), "patterns": ["*.md"], "recursive": False},
                ],
                "chunking": {"strategy": "markdown_header", "max_tokens": 512},
            }
        },
        "shared": {"cache_dir": ".rag/models"},
        "database": {"path": ".rag/knowledge.db"},
        "search": {
            "default_top_k": 5,
            "max_top_k": 10,
            "rrf_k": 60,
            "vector_candidates": 20,
            "fts_candidates": 20,
        },
    }
    config_path.write_text(yaml.dump(config), encoding="utf-8")

    loader = CorpusLoader(tmp_path)
    files = loader.enumerate_from_config(config_path)

    assert len(files) == 1


def test_sha256_changes_when_file_modified(tmp_path):
    corpus = tmp_path / "docs"
    corpus.mkdir()
    f = corpus / "file.md"
    f.write_text("original content", encoding="utf-8")

    config_path = tmp_path / "rag.config.yaml"
    _write_config(
        config_path,
        [{"path": str(corpus), "patterns": ["*.md"], "recursive": False}],
    )

    loader = CorpusLoader(tmp_path)
    before = loader.enumerate_from_config(config_path)[0].sha256

    f.write_text("modified content", encoding="utf-8")
    after = loader.enumerate_from_config(config_path)[0].sha256

    assert before != after


# ── snapshot ──────────────────────────────────────────────────────────────────


def test_snapshot_structure(tmp_path):
    corpus = tmp_path / "docs"
    corpus.mkdir()
    (corpus / "a.md").write_text("# A")

    config_path = tmp_path / "rag.config.yaml"
    _write_config(
        config_path,
        [{"path": str(corpus), "patterns": ["*.md"], "recursive": False}],
    )

    loader = CorpusLoader(tmp_path)
    snap = loader.snapshot(config_path)

    assert "files" in snap
    assert "hash" in snap
    assert "total_files" in snap
    assert snap["total_files"] == 1
    assert len(snap["hash"]) == 16


def test_snapshot_hash_changes_when_corpus_changes(tmp_path):
    corpus = tmp_path / "docs"
    corpus.mkdir()
    f = corpus / "a.md"
    f.write_text("original")

    config_path = tmp_path / "rag.config.yaml"
    _write_config(
        config_path,
        [{"path": str(corpus), "patterns": ["*.md"], "recursive": False}],
    )

    loader = CorpusLoader(tmp_path)
    h1 = loader.snapshot(config_path)["hash"]

    f.write_text("modified")
    h2 = loader.snapshot(config_path)["hash"]

    assert h1 != h2


def test_snapshot_hash_stable_when_corpus_unchanged(tmp_path):
    corpus = tmp_path / "docs"
    corpus.mkdir()
    (corpus / "a.md").write_text("stable content")

    config_path = tmp_path / "rag.config.yaml"
    _write_config(
        config_path,
        [{"path": str(corpus), "patterns": ["*.md"], "recursive": False}],
    )

    loader = CorpusLoader(tmp_path)
    assert loader.snapshot(config_path)["hash"] == loader.snapshot(config_path)["hash"]


def test_corpus_file_path_relative_to_target(tmp_path):
    corpus = tmp_path / "docs"
    corpus.mkdir()
    (corpus / "file.md").write_text("# File")

    config_path = tmp_path / "rag.config.yaml"
    _write_config(
        config_path,
        [{"path": str(corpus), "patterns": ["*.md"], "recursive": False}],
    )

    loader = CorpusLoader(tmp_path)
    files = loader.enumerate_from_config(config_path)

    assert len(files) == 1
    assert not Path(files[0].path).is_absolute()
    assert files[0].path == "docs/file.md"
