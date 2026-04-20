from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bench.checkpoint import Checkpoint
from bench.config import BenchConfig, SweepSettings, TargetSettings
from bench.golden.schema import Collection, Difficulty, GoldenQuery, QueryKind, QueryLength
from bench.sweep import SweepRunner, _chunks_hash, _token_count, load_golden_queries


# ── Helper factories ──────────────────────────────────────────────────────────


def _make_query(qid: str = "docs-001", collection: str = "docs") -> GoldenQuery:
    return GoldenQuery(
        id=qid,
        collection=Collection(collection),
        query="What is a skill?",
        query_kind=QueryKind.conceptual,
        difficulty=Difficulty.easy,
        length=QueryLength.short,
        expected_files=["docs/skills.md"],
        expected_answer="Skills extend Claude.",
        must_contain=["skill"],
    )


def _make_config(tmp_path: Path) -> BenchConfig:
    return BenchConfig(
        target=TargetSettings(path=tmp_path),
        sweep=SweepSettings(
            collections=["docs"],
            chunk_sizes={"docs": [512]},
            models={"docs": ["small"]},
            top_k=[5],
        ),
    )


def _make_checkpoint(tmp_path: Path, run_id: str = "run-sw-001") -> Checkpoint:
    state_dir = tmp_path / ".bench-state"
    state_dir.mkdir(exist_ok=True)
    manifest = {
        "run_id": run_id,
        "bench_version": "0.1.0",
        "corpus": {"files": [], "hash": "aabbccdd"},
    }
    return Checkpoint.create(run_id, state_dir, manifest)


def _make_runner(tmp_path: Path, target=None, judge=None, queries=None, cp=None):
    config = _make_config(tmp_path)
    if cp is None:
        cp = _make_checkpoint(tmp_path)
    if target is None:
        target = MagicMock()
    if judge is None:
        judge = MagicMock()
    if queries is None:
        queries = [_make_query()]
    messages = []
    return SweepRunner(
        config=config,
        checkpoint=cp,
        target=target,
        judge=judge,
        golden_queries=queries,
        print_fn=messages.append,
    ), messages


# ── _chunks_hash ──────────────────────────────────────────────────────────────


def test_chunks_hash_deterministic():
    chunks = [{"file_path": "a.md", "score": 0.5}]
    assert _chunks_hash(chunks) == _chunks_hash(chunks)


def test_chunks_hash_differs_on_change():
    c1 = [{"file_path": "a.md", "score": 0.5}]
    c2 = [{"file_path": "b.md", "score": 0.5}]
    assert _chunks_hash(c1) != _chunks_hash(c2)


# ── _token_count ──────────────────────────────────────────────────────────────


def test_token_count_empty():
    assert _token_count("") >= 0


def test_token_count_nonempty():
    assert _token_count("hello world skills") > 0


# ── load_golden_queries ───────────────────────────────────────────────────────


def test_load_golden_queries_returns_list():
    queries = load_golden_queries()
    assert isinstance(queries, list)
    assert len(queries) > 0


def test_load_golden_queries_all_valid():
    for q in load_golden_queries():
        assert isinstance(q, GoldenQuery)
        assert q.id
        assert q.query


# ── SweepRunner — index phase ─────────────────────────────────────────────────


def test_runner_calls_generate_config_and_index(tmp_path):
    target = MagicMock()
    target.config_path.return_value = tmp_path / "cfg.yaml"
    target.generate_config.return_value = tmp_path / "cfg.yaml"
    index_result = MagicMock()
    index_result.returncode = 0
    index_result.wall_time_s = 1.5
    index_result.stderr = ""
    target.index.return_value = index_result

    search_result = MagicMock()
    search_result.file_path = "docs/skills.md"
    search_result.content = "Skills extend Claude."
    search_result.score = 0.9
    search_result.source = "rrf"
    search_result.collection = "docs"
    target.search.return_value = [search_result]

    judge = MagicMock()
    judge.score_batch.return_value = [MagicMock(score=0.8, reasoning=None)]

    runner, _ = _make_runner(tmp_path, target=target, judge=judge)
    runner.run()

    target.generate_config.assert_called_once()
    target.index.assert_called_once()


def test_runner_skips_already_indexed(tmp_path):
    cp = _make_checkpoint(tmp_path)
    # Pre-mark config as indexed
    cp.mark_indexed("docs-c512-bge-small", wall_time_s=5.0, collection="docs")

    target = MagicMock()
    target.config_path.return_value = tmp_path / "cfg.yaml"
    search_result = MagicMock()
    search_result.file_path = "docs/skills.md"
    search_result.content = "Skills."
    search_result.score = 0.7
    search_result.source = "rrf"
    search_result.collection = "docs"
    target.search.return_value = [search_result]

    judge = MagicMock()
    judge.score_batch.return_value = [MagicMock(score=0.8, reasoning=None)]

    runner, _ = _make_runner(tmp_path, target=target, judge=judge, cp=cp)
    runner.run()

    target.generate_config.assert_not_called()
    target.index.assert_not_called()


def test_runner_raises_on_index_failure(tmp_path):
    target = MagicMock()
    target.config_path.return_value = tmp_path / "cfg.yaml"
    target.generate_config.return_value = tmp_path / "cfg.yaml"
    index_result = MagicMock()
    index_result.returncode = 1
    index_result.wall_time_s = 0.1
    index_result.stderr = "some error"
    target.index.return_value = index_result

    runner, _ = _make_runner(tmp_path, target=target)
    with pytest.raises(RuntimeError, match="docs-c512-bge-small"):
        runner.run()


# ── SweepRunner — retrieval phase ─────────────────────────────────────────────


def test_runner_marks_retrieved_done(tmp_path):
    cp = _make_checkpoint(tmp_path)
    cp.mark_indexed("docs-c512-bge-small", 1.0, "docs")

    target = MagicMock()
    target.config_path.return_value = tmp_path / "cfg.yaml"
    sr = MagicMock()
    sr.file_path = "docs/skills.md"
    sr.content = "Skills."
    sr.score = 0.9
    sr.source = "rrf"
    sr.collection = "docs"
    target.search.return_value = [sr]

    judge = MagicMock()
    judge.score_batch.return_value = [MagicMock(score=0.7, reasoning=None)]

    runner, _ = _make_runner(tmp_path, target=target, judge=judge, cp=cp)
    runner.run()

    assert cp.is_done("docs-c512-bge-small", "docs-001", 5, "retrieved")


def test_runner_skips_already_retrieved(tmp_path):
    cp = _make_checkpoint(tmp_path)
    cp.mark_indexed("docs-c512-bge-small", 1.0, "docs")
    cp.mark_done("docs-c512-bge-small", "docs-001", 5, "retrieved", chunks=[])

    target = MagicMock()
    target.config_path.return_value = tmp_path / "cfg.yaml"

    judge = MagicMock()
    runner, _ = _make_runner(tmp_path, target=target, judge=judge, cp=cp)
    runner.run()

    # search should NOT be called (already done)
    target.search.assert_not_called()


def test_runner_records_error_on_search_failure(tmp_path):
    cp = _make_checkpoint(tmp_path)
    cp.mark_indexed("docs-c512-bge-small", 1.0, "docs")

    target = MagicMock()
    target.config_path.return_value = tmp_path / "cfg.yaml"
    target.search.side_effect = RuntimeError("search broke")

    judge = MagicMock()
    runner, _ = _make_runner(tmp_path, target=target, judge=judge, cp=cp)
    runner.run()  # should not raise

    from bench.persistence import read_jsonl

    errors = read_jsonl(cp._run_dir / "errors.jsonl")
    assert any("search broke" in str(e.get("error")) for e in errors)


# ── SweepRunner — judging phase ───────────────────────────────────────────────


def test_runner_calls_judge_once_per_unit(tmp_path):
    cp = _make_checkpoint(tmp_path)
    cp.mark_indexed("docs-c512-bge-small", 1.0, "docs")

    target = MagicMock()
    target.config_path.return_value = tmp_path / "cfg.yaml"
    sr = MagicMock()
    sr.file_path = "docs/skills.md"
    sr.content = "content"
    sr.score = 0.9
    sr.source = "rrf"
    sr.collection = "docs"
    target.search.return_value = [sr]

    judge = MagicMock()
    j_result = MagicMock()
    j_result.score = 0.75
    j_result.reasoning = None
    judge.score_batch.return_value = [j_result]

    runner, _ = _make_runner(tmp_path, target=target, judge=judge, cp=cp)
    runner.run()

    judge.score_batch.assert_called()
    assert cp.is_done("docs-c512-bge-small", "docs-001", 5, "judged")


def test_runner_uses_judge_cache(tmp_path):
    cp = _make_checkpoint(tmp_path)
    cp.mark_indexed("docs-c512-bge-small", 1.0, "docs")

    target = MagicMock()
    target.config_path.return_value = tmp_path / "cfg.yaml"
    sr = MagicMock()
    sr.file_path = "docs/skills.md"
    sr.content = "cached content"
    sr.score = 0.9
    sr.source = "rrf"
    sr.collection = "docs"
    target.search.return_value = [sr]

    # Pre-populate judge cache
    chunk = {"file_path": "docs/skills.md", "score": 0.9, "source": "rrf", "collection": "docs", "token_count": 3}
    from bench.sweep import _chunks_hash
    h = _chunks_hash([chunk])
    cp.record_judge("MagicMock", "docs-001", h, {"score": 0.99})

    judge = MagicMock()
    runner, _ = _make_runner(tmp_path, target=target, judge=judge, cp=cp)
    runner.run()

    # Judge should not be called because cache hit
    judge.score_batch.assert_not_called()


# ── Sanity check ──────────────────────────────────────────────────────────────


def test_sanity_check_passes_with_results(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "readme.md").write_text(
        "This is a test document about skills and agents in Claude Code.", encoding="utf-8"
    )

    config = BenchConfig(
        target=TargetSettings(path=tmp_path, toolkit_rag_config=tmp_path / "nonexistent.yaml"),
        sweep=SweepSettings(
            collections=["docs"],
            chunk_sizes={"docs": [512]},
            models={"docs": ["small"]},
            top_k=[5],
        ),
    )
    cp = _make_checkpoint(tmp_path)
    cp.mark_indexed("docs-c512-bge-small", 1.0, "docs")

    target = MagicMock()
    sr = MagicMock()
    sr.file_path = "docs/readme.md"
    sr.content = "content"
    sr.score = 0.9
    sr.source = "rrf"
    sr.collection = "docs"
    target.search.return_value = [sr]
    target.config_path.return_value = tmp_path / "cfg.yaml"
    judge = MagicMock()
    judge.score_batch.return_value = [MagicMock(score=0.8, reasoning=None)]

    runner = SweepRunner(config, cp, target, judge, [_make_query()], print_fn=lambda _: None)
    # Should not raise
    runner._run_sanity_check(
        config.expand_sweep()[0], tmp_path / "cfg.yaml"
    )


def test_sanity_check_aborts_on_empty_results(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "readme.md").write_text(
        "This is a test document about skills and agents in Claude Code.", encoding="utf-8"
    )
    config = BenchConfig(
        target=TargetSettings(path=tmp_path, toolkit_rag_config=tmp_path / "nonexistent.yaml"),
        sweep=SweepSettings(
            collections=["docs"],
            chunk_sizes={"docs": [512]},
            models={"docs": ["small"]},
            top_k=[5],
        ),
    )
    cp = _make_checkpoint(tmp_path)

    target = MagicMock()
    target.search.return_value = []  # empty — sanity fails
    judge = MagicMock()
    runner = SweepRunner(config, cp, target, judge, [_make_query()], print_fn=lambda _: None)

    with pytest.raises(SystemExit):
        runner._run_sanity_check(config.expand_sweep()[0], tmp_path / "cfg.yaml")
