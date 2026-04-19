from __future__ import annotations

import fcntl
import os
from pathlib import Path
from typing import Any

from bench.persistence import append_jsonl, read_json, read_jsonl, write_json_atomic


class CorpusDriftError(Exception):
    """Corpus changed since the run was created."""


class LockError(Exception):
    """Another bench process holds the run lock."""


def _unit_key(config_id: str, query_id: str, top_k: int, phase: str) -> tuple:
    return (config_id, query_id, int(top_k), phase)


def _judge_key(judge_id: str, query_id: str, chunks_hash: str) -> tuple:
    return (judge_id, query_id, chunks_hash)


class Checkpoint:
    """State machine for bench run resume.

    Progress and judge-cache are backed by append-only JSONL files so a
    SIGKILL mid-write never produces a corrupt state directory.
    """

    def __init__(
        self,
        run_id: str,
        run_dir: Path,
        manifest: dict,
        done: set[tuple],
        judge_cache: dict[tuple, dict],
    ) -> None:
        self.run_id = run_id
        self._run_dir = run_dir
        self.manifest = manifest
        self._done = done
        self._judge_cache = judge_cache
        self._lock_fd: int | None = None

    # ── Factory methods ──────────────────────────────────────────────────────

    @classmethod
    def create(cls, run_id: str, state_dir: Path, manifest: dict) -> Checkpoint:
        """Initialise a new run directory with empty state files."""
        run_dir = Path(state_dir) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        write_json_atomic(run_dir / "manifest.json", manifest)
        write_json_atomic(run_dir / "index-state.json", {})

        for fname in ("progress.jsonl", "judge-cache.jsonl", "errors.jsonl"):
            p = run_dir / fname
            if not p.exists():
                p.touch()

        return cls(run_id, run_dir, manifest, set(), {})

    @classmethod
    def load(
        cls,
        run_id: str,
        state_dir: Path,
        current_corpus_hash: str | None = None,
        allow_drift: bool = False,
    ) -> Checkpoint:
        """Load an existing run directory.

        Raises FileNotFoundError if the run does not exist.
        Raises CorpusDriftError if current_corpus_hash differs from manifest
        and allow_drift is False.
        """
        run_dir = Path(state_dir) / run_id
        manifest_path = run_dir / "manifest.json"

        if not manifest_path.exists():
            raise FileNotFoundError(f"No run found: {run_id} in {state_dir}")

        manifest = read_json(manifest_path)

        if current_corpus_hash is not None:
            stored = manifest.get("corpus", {}).get("hash", "")
            if current_corpus_hash != stored and not allow_drift:
                raise CorpusDriftError(
                    f"Corpus has changed since run {run_id} was created. "
                    "Pass allow_drift=True to override."
                )

        done: set[tuple] = set()
        for rec in read_jsonl(run_dir / "progress.jsonl"):
            done.add(_unit_key(rec["config_id"], rec["query_id"], rec["top_k"], rec["phase"]))

        judge_cache: dict[tuple, dict] = {}
        for rec in read_jsonl(run_dir / "judge-cache.jsonl"):
            key = _judge_key(rec["judge_id"], rec["query_id"], rec["chunks_hash"])
            judge_cache[key] = rec["response"]

        return cls(run_id, run_dir, manifest, done, judge_cache)

    # ── Progress tracking ────────────────────────────────────────────────────

    def mark_done(
        self, config_id: str, query_id: str, top_k: int, phase: str, **extra: Any
    ) -> None:
        """Record a completed work unit; appends to progress.jsonl."""
        key = _unit_key(config_id, query_id, top_k, phase)
        record: dict[str, Any] = {
            "config_id": config_id,
            "query_id": query_id,
            "top_k": int(top_k),
            "phase": phase,
            **extra,
        }
        append_jsonl(self._run_dir / "progress.jsonl", record)
        self._done.add(key)

    def is_done(self, config_id: str, query_id: str, top_k: int, phase: str) -> bool:
        return _unit_key(config_id, query_id, top_k, phase) in self._done

    def pending(self, all_units: list[tuple]) -> list[tuple]:
        """Return the subset of all_units not yet completed."""
        return [u for u in all_units if _unit_key(*u) not in self._done]

    # ── Judge cache ──────────────────────────────────────────────────────────

    def record_judge(self, judge_id: str, query_id: str, chunks_hash: str, response: dict) -> None:
        """Persist a judge response and cache it in memory."""
        rec = {
            "judge_id": judge_id,
            "query_id": query_id,
            "chunks_hash": chunks_hash,
            "response": response,
        }
        append_jsonl(self._run_dir / "judge-cache.jsonl", rec)
        self._judge_cache[_judge_key(judge_id, query_id, chunks_hash)] = response

    def get_cached_judge(self, judge_id: str, query_id: str, chunks_hash: str) -> dict | None:
        """Return cached judge response, or None on cache miss."""
        return self._judge_cache.get(_judge_key(judge_id, query_id, chunks_hash))

    # ── Advisory lock ────────────────────────────────────────────────────────

    def acquire_lock(self) -> None:
        """Acquire exclusive advisory lock on the run directory."""
        lock_path = self._run_dir / "lock"
        fd = os.open(str(lock_path), os.O_WRONLY | os.O_CREAT, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            os.close(fd)
            raise LockError(
                f"Another bench process is running for run {self.run_id}. "
                f"Remove the lock file to force: {lock_path}"
            ) from exc
        self._lock_fd = fd

    def release_lock(self) -> None:
        """Release the advisory lock if held."""
        if self._lock_fd is not None:
            fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
            os.close(self._lock_fd)
            self._lock_fd = None

    def __enter__(self) -> Checkpoint:
        self.acquire_lock()
        return self

    def __exit__(self, *_: Any) -> None:
        self.release_lock()
