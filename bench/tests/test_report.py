from __future__ import annotations

import json
from pathlib import Path

import pytest

from bench.persistence import append_jsonl, write_json_atomic
from bench.report import compute_config_stats, find_failure_cases, render


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _setup_run(tmp_path: Path) -> tuple[Path, Path]:
    """Create a minimal .bench-state run directory with progress records."""
    run_dir = tmp_path / ".bench-state" / "run-r001"
    run_dir.mkdir(parents=True)

    manifest = {
        "run_id": "run-r001",
        "bench_version": "0.1.0",
        "created_at": "2026-04-19T10:00:00Z",
        "rag_target": {"path": "/tmp/toolkit", "git_sha": "abc1234"},
        "judge": {"type": "cross-encoder", "model": "bge-reranker-base"},
        "corpus": {"total_files": 10},
        "lang": "en",
    }
    write_json_atomic(run_dir / "manifest.json", manifest)

    progress_path = run_dir / "progress.jsonl"
    # retrieved records
    retrieved_chunks = [
        {"file_path": "docs/skills.md", "score": 0.9, "source": "rrf", "collection": "docs", "token_count": 150},
    ]
    append_jsonl(progress_path, {
        "config_id": "docs-c512-bge-small",
        "query_id": "docs-001",
        "top_k": 5,
        "phase": "retrieved",
        "chunks": retrieved_chunks,
    })
    # judged records
    append_jsonl(progress_path, {
        "config_id": "docs-c512-bge-small",
        "query_id": "docs-001",
        "top_k": 5,
        "phase": "judged",
        "score": 0.85,
    })
    return run_dir, progress_path


GOLDEN_INDEX = {
    "docs-001": {
        "id": "docs-001",
        "query": "What are skills?",
        "expected_files": ["docs/skills.md"],
    }
}


# ── compute_config_stats ──────────────────────────────────────────────────────


def test_compute_config_stats_returns_list(tmp_path):
    _, progress_path = _setup_run(tmp_path)
    stats = compute_config_stats(
        progress_path, GOLDEN_INDEX, top_k=5,
        weights={"coverage": 0.5, "token_to_coverage_ratio": 0.3, "precision_at_5": 0.2},
        ss_threshold=0.8,
    )
    assert isinstance(stats, list)


def test_compute_config_stats_has_correct_fields(tmp_path):
    _, progress_path = _setup_run(tmp_path)
    stats = compute_config_stats(
        progress_path, GOLDEN_INDEX, top_k=5,
        weights={"coverage": 0.5, "token_to_coverage_ratio": 0.3, "precision_at_5": 0.2},
        ss_threshold=0.8,
    )
    assert len(stats) == 1
    s = stats[0]
    assert "config_id" in s
    assert "coverage" in s
    assert "composite" in s
    assert "precision_at_k" in s
    assert "mrr" in s


def test_compute_config_stats_coverage_matches_score(tmp_path):
    _, progress_path = _setup_run(tmp_path)
    stats = compute_config_stats(
        progress_path, GOLDEN_INDEX, top_k=5,
        weights={"coverage": 0.5, "token_to_coverage_ratio": 0.3, "precision_at_5": 0.2},
        ss_threshold=0.8,
    )
    assert pytest.approx(stats[0]["coverage"], abs=0.01) == 0.85


def test_compute_config_stats_sorted_by_composite(tmp_path):
    run_dir, progress_path = _setup_run(tmp_path)
    # Add a second config with lower score
    append_jsonl(progress_path, {
        "config_id": "docs-c256-bge-small",
        "query_id": "docs-001",
        "top_k": 5,
        "phase": "retrieved",
        "chunks": [{"file_path": "docs/other.md", "score": 0.3, "source": "rrf", "collection": "docs", "token_count": 50}],
    })
    append_jsonl(progress_path, {
        "config_id": "docs-c256-bge-small",
        "query_id": "docs-001",
        "top_k": 5,
        "phase": "judged",
        "score": 0.20,
    })
    stats = compute_config_stats(
        progress_path, GOLDEN_INDEX, top_k=5,
        weights={"coverage": 0.5, "token_to_coverage_ratio": 0.3, "precision_at_5": 0.2},
        ss_threshold=0.8,
    )
    assert stats[0]["composite"] >= stats[-1]["composite"]


def test_compute_config_stats_empty_progress(tmp_path):
    empty = tmp_path / "empty.jsonl"
    empty.touch()
    stats = compute_config_stats(
        empty, GOLDEN_INDEX, top_k=5,
        weights={"coverage": 0.5, "token_to_coverage_ratio": 0.3, "precision_at_5": 0.2},
        ss_threshold=0.8,
    )
    assert stats == []


# ── find_failure_cases ────────────────────────────────────────────────────────


def test_find_failure_cases_empty_on_high_scores(tmp_path):
    _, progress_path = _setup_run(tmp_path)  # score 0.85 > 0.4 threshold
    failures = find_failure_cases(progress_path, GOLDEN_INDEX, top_k=5, threshold=0.4)
    assert failures == []


def test_find_failure_cases_detects_low_coverage(tmp_path):
    run_dir = tmp_path / ".bench-state" / "run-fail"
    run_dir.mkdir(parents=True)
    p = run_dir / "progress.jsonl"
    append_jsonl(p, {"config_id": "docs-c512-bge-small", "query_id": "docs-001",
                     "top_k": 5, "phase": "judged", "score": 0.1})
    failures = find_failure_cases(p, GOLDEN_INDEX, top_k=5, threshold=0.4)
    assert len(failures) == 1
    assert failures[0]["query_id"] == "docs-001"


# ── render ────────────────────────────────────────────────────────────────────


def test_render_creates_report_file(tmp_path):
    run_dir, _ = _setup_run(tmp_path)
    out = tmp_path / "REPORT.md"
    render(run_dir, out)
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "RAG Baseline Report" in content


def test_render_contains_tldr_heading(tmp_path):
    run_dir, _ = _setup_run(tmp_path)
    out = tmp_path / "REPORT.md"
    render(run_dir, out)
    assert "TL;DR" in out.read_text(encoding="utf-8")


def test_render_contains_ranking_table(tmp_path):
    run_dir, _ = _setup_run(tmp_path)
    out = tmp_path / "REPORT.md"
    render(run_dir, out)
    content = out.read_text(encoding="utf-8")
    assert "docs-c512-bge-small" in content


def test_render_contains_reproducibility(tmp_path):
    run_dir, _ = _setup_run(tmp_path)
    out = tmp_path / "REPORT.md"
    render(run_dir, out)
    content = out.read_text(encoding="utf-8")
    assert "run-r001" in content


def test_render_missing_progress_still_works(tmp_path):
    run_dir = tmp_path / ".bench-state" / "run-empty"
    run_dir.mkdir(parents=True)
    (run_dir / "manifest.json").write_text("{}", encoding="utf-8")
    (run_dir / "progress.jsonl").touch()
    out = tmp_path / "REPORT.md"
    render(run_dir, out)
    assert out.exists()
