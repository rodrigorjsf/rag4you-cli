from __future__ import annotations

import json
from pathlib import Path

import pytest

from bench.persistence import append_jsonl, write_json_atomic


def _make_manifest(run_id: str, corpus_hash: str = "abc123") -> dict:
    return {
        "run_id": run_id,
        "bench_version": "0.1.0",
        "corpus": {
            "files": [{"path": "README.md", "sha256": "deadbeef"}],
            "hash": corpus_hash,
        },
    }


def _setup_run(tmp_path: Path, run_id: str, corpus_hash: str = "abc123") -> Path:
    state_dir = tmp_path / ".bench-state"
    state_dir.mkdir()
    run_dir = state_dir / run_id
    run_dir.mkdir()
    write_json_atomic(run_dir / "manifest.json", _make_manifest(run_id, corpus_hash))
    return state_dir


# ── Persistence primitives ───────────────────────────────────────────────────


def test_append_jsonl_creates_file(tmp_path):
    path = tmp_path / "out.jsonl"
    append_jsonl(path, {"key": "value"})
    assert path.exists()
    lines = path.read_text().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {"key": "value"}


def test_append_jsonl_multiple_records(tmp_path):
    path = tmp_path / "out.jsonl"
    for n in range(3):
        append_jsonl(path, {"n": n})
    lines = [json.loads(line) for line in path.read_text().splitlines()]
    assert [r["n"] for r in lines] == [0, 1, 2]


def test_write_json_atomic_creates_file(tmp_path):
    path = tmp_path / "out.json"
    write_json_atomic(path, {"foo": "bar"})
    assert json.loads(path.read_text()) == {"foo": "bar"}


def test_write_json_atomic_overwrites(tmp_path):
    path = tmp_path / "out.json"
    write_json_atomic(path, {"v": 1})
    write_json_atomic(path, {"v": 2})
    assert json.loads(path.read_text())["v"] == 2


def test_write_json_atomic_no_tmp_leftover(tmp_path):
    path = tmp_path / "out.json"
    write_json_atomic(path, {"x": 1})
    assert not (tmp_path / "out.json.tmp").exists()


# ── Checkpoint.create ────────────────────────────────────────────────────────


def test_checkpoint_create_initialises_files(tmp_path):
    from bench.checkpoint import Checkpoint

    state_dir = tmp_path / ".bench-state"
    state_dir.mkdir()
    cp = Checkpoint.create("run-001", state_dir, _make_manifest("run-001"))

    run_dir = state_dir / "run-001"
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "progress.jsonl").exists()
    assert (run_dir / "judge-cache.jsonl").exists()
    assert (run_dir / "errors.jsonl").exists()
    assert cp.run_id == "run-001"


def test_checkpoint_create_no_done_initially(tmp_path):
    from bench.checkpoint import Checkpoint

    state_dir = tmp_path / ".bench-state"
    state_dir.mkdir()
    cp = Checkpoint.create("run-001b", state_dir, _make_manifest("run-001b"))
    unit = ("cfg", "q", 5, "retrieved")
    assert not cp.is_done(*unit)
    assert cp.pending([unit]) == [unit]


# ── Checkpoint.load ──────────────────────────────────────────────────────────


def test_checkpoint_load_reads_manifest(tmp_path):
    from bench.checkpoint import Checkpoint

    state_dir = _setup_run(tmp_path, "run-002")
    cp = Checkpoint.load("run-002", state_dir)
    assert cp.manifest["run_id"] == "run-002"


def test_checkpoint_load_missing_run_raises(tmp_path):
    from bench.checkpoint import Checkpoint

    state_dir = tmp_path / ".bench-state"
    state_dir.mkdir()
    with pytest.raises(FileNotFoundError):
        Checkpoint.load("nonexistent", state_dir)


# ── Gate: resume skips completed units ──────────────────────────────────────


def test_resume_skips_completed_units(tmp_path):
    """After SIGKILL mid-run, reload sees only pending work units."""
    from bench.checkpoint import Checkpoint

    state_dir = _setup_run(tmp_path, "run-003")
    run_dir = state_dir / "run-003"

    unit1 = ("config-a", "docs-001", 5, "retrieved")
    unit2 = ("config-a", "docs-002", 5, "retrieved")

    append_jsonl(
        run_dir / "progress.jsonl",
        {"config_id": unit1[0], "query_id": unit1[1], "top_k": unit1[2], "phase": unit1[3]},
    )

    cp = Checkpoint.load("run-003", state_dir)

    pending = cp.pending([unit1, unit2])
    assert len(pending) == 1
    assert pending[0] == unit2
    assert cp.is_done(*unit1)
    assert not cp.is_done(*unit2)


def test_resume_mark_done_persists_across_reload(tmp_path):
    from bench.checkpoint import Checkpoint

    state_dir = tmp_path / ".bench-state"
    state_dir.mkdir()
    cp = Checkpoint.create("run-004", state_dir, _make_manifest("run-004"))
    unit = ("cfg-b", "docs-001", 3, "judged")

    cp.mark_done(*unit, score=0.9)

    cp2 = Checkpoint.load("run-004", state_dir)
    assert cp2.is_done(*unit)


def test_pending_empty_when_all_done(tmp_path):
    from bench.checkpoint import Checkpoint

    state_dir = tmp_path / ".bench-state"
    state_dir.mkdir()
    cp = Checkpoint.create("run-004b", state_dir, _make_manifest("run-004b"))
    units = [("c", "q1", 5, "retrieved"), ("c", "q2", 5, "retrieved")]
    for u in units:
        cp.mark_done(*u)
    assert cp.pending(units) == []


# ── Gate: corpus drift ───────────────────────────────────────────────────────


def test_resume_corpus_drift_aborts(tmp_path):
    """Corpus hash change raises CorpusDriftError without allow_drift."""
    from bench.checkpoint import Checkpoint, CorpusDriftError

    state_dir = _setup_run(tmp_path, "run-005", corpus_hash="original-hash")
    with pytest.raises(CorpusDriftError, match="Corpus"):
        Checkpoint.load("run-005", state_dir, current_corpus_hash="changed-hash")


def test_resume_corpus_drift_allow(tmp_path):
    """allow_drift=True proceeds despite hash mismatch."""
    from bench.checkpoint import Checkpoint

    state_dir = _setup_run(tmp_path, "run-006", corpus_hash="original-hash")
    cp = Checkpoint.load("run-006", state_dir, current_corpus_hash="changed-hash", allow_drift=True)
    assert cp.manifest["run_id"] == "run-006"


def test_resume_corpus_no_drift(tmp_path):
    """Same corpus hash → no error."""
    from bench.checkpoint import Checkpoint

    state_dir = _setup_run(tmp_path, "run-007", corpus_hash="stable-hash")
    cp = Checkpoint.load("run-007", state_dir, current_corpus_hash="stable-hash")
    assert cp is not None


def test_resume_no_hash_supplied_skips_check(tmp_path):
    """If no current_corpus_hash provided, drift check is skipped."""
    from bench.checkpoint import Checkpoint

    state_dir = _setup_run(tmp_path, "run-007b", corpus_hash="whatever")
    cp = Checkpoint.load("run-007b", state_dir)
    assert cp is not None


# ── Judge cache ──────────────────────────────────────────────────────────────


def test_judge_cache_miss_returns_none(tmp_path):
    from bench.checkpoint import Checkpoint

    state_dir = _setup_run(tmp_path, "run-008")
    cp = Checkpoint.load("run-008", state_dir)
    assert cp.get_cached_judge("cross-encoder", "docs-001", "hashXYZ") is None


def test_judge_cache_record_and_retrieve(tmp_path):
    from bench.checkpoint import Checkpoint

    state_dir = tmp_path / ".bench-state"
    state_dir.mkdir()
    cp = Checkpoint.create("run-009", state_dir, _make_manifest("run-009"))

    response = {"score": 0.87, "reasoning": "relevant"}
    cp.record_judge("cross-encoder", "docs-001", "hashABC", response)

    assert cp.get_cached_judge("cross-encoder", "docs-001", "hashABC") == response


def test_judge_cache_persists_across_reload(tmp_path):
    """judge-cache.jsonl survives reload — simulates resume after SIGKILL."""
    from bench.checkpoint import Checkpoint

    state_dir = tmp_path / ".bench-state"
    state_dir.mkdir()
    cp = Checkpoint.create("run-010", state_dir, _make_manifest("run-010"))
    cp.record_judge("claude", "docs-002", "hashDEF", {"score": 0.5})

    cp2 = Checkpoint.load("run-010", state_dir)
    assert cp2.get_cached_judge("claude", "docs-002", "hashDEF") == {"score": 0.5}


def test_judge_cache_key_distinct(tmp_path):
    from bench.checkpoint import Checkpoint

    state_dir = tmp_path / ".bench-state"
    state_dir.mkdir()
    cp = Checkpoint.create("run-011", state_dir, _make_manifest("run-011"))

    cp.record_judge("claude", "q1", "h1", {"score": 0.9})
    cp.record_judge("openai", "q1", "h1", {"score": 0.7})
    cp.record_judge("claude", "q1", "h2", {"score": 0.3})

    assert cp.get_cached_judge("claude", "q1", "h1") == {"score": 0.9}
    assert cp.get_cached_judge("openai", "q1", "h1") == {"score": 0.7}
    assert cp.get_cached_judge("claude", "q1", "h2") == {"score": 0.3}
    assert cp.get_cached_judge("ollama", "q1", "h1") is None


# ── Lock ─────────────────────────────────────────────────────────────────────


def test_lock_context_manager_creates_lock_file(tmp_path):
    from bench.checkpoint import Checkpoint

    state_dir = tmp_path / ".bench-state"
    state_dir.mkdir()
    cp = Checkpoint.create("run-012", state_dir, _make_manifest("run-012"))

    with cp:
        assert (state_dir / "run-012" / "lock").exists()


def test_lock_release_after_context_exit(tmp_path):
    """After __exit__, a second acquire must succeed (lock was released)."""
    from bench.checkpoint import Checkpoint

    state_dir = tmp_path / ".bench-state"
    state_dir.mkdir()
    cp = Checkpoint.create("run-013a", state_dir, _make_manifest("run-013a"))
    cp2 = Checkpoint.load("run-013a", state_dir)

    with cp:
        pass

    cp2.acquire_lock()
    cp2.release_lock()


def test_lock_concurrent_raises(tmp_path):
    """Second Checkpoint on same run raises LockError."""
    from bench.checkpoint import Checkpoint, LockError

    state_dir = tmp_path / ".bench-state"
    state_dir.mkdir()
    cp1 = Checkpoint.create("run-013", state_dir, _make_manifest("run-013"))
    cp2 = Checkpoint.load("run-013", state_dir)

    cp1.acquire_lock()
    try:
        with pytest.raises(LockError, match="run-013"):
            cp2.acquire_lock()
    finally:
        cp1.release_lock()
