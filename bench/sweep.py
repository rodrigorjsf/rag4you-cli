"""SweepRunner — orchestrates the (config × query × top_k) × judge cartesian."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable

import yaml

from bench.checkpoint import Checkpoint
from bench.config import BenchConfig, SweepEntry
from bench.golden.schema import GoldenQuery
from bench.i18n import t
from bench.judges.base import Judge
from bench.target import RagTarget, SearchChunk


def _chunks_hash(chunks: list[dict]) -> str:
    raw = "|".join(
        f"{c.get('file_path', '')}:{c.get('score', 0.0):.6f}" for c in chunks
    )
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _token_count(text: str) -> int:
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return max(1, len(text.split()))


def _chunk_to_record(chunk: SearchChunk, max_tokens: int) -> dict[str, Any]:
    return {
        "file_path": chunk.file_path,
        "score": chunk.score,
        "source": chunk.source,
        "collection": chunk.collection,
        "token_count": _token_count(chunk.content),
    }


def load_golden_queries(dataset_path: Path | None = None) -> list[GoldenQuery]:
    if dataset_path is None:
        dataset_path = Path(__file__).parent / "golden" / "dataset.yaml"
    with dataset_path.open(encoding="utf-8") as fh:
        rows = yaml.safe_load(fh) or []
    return [GoldenQuery.model_validate(r) for r in rows]


class SweepRunner:
    """Orchestrate (sweep_entry × query × top_k) × judge, checkpointing every unit."""

    def __init__(
        self,
        config: BenchConfig,
        checkpoint: Checkpoint,
        target: RagTarget,
        judge: Judge,
        golden_queries: list[GoldenQuery],
        synth_queries: list[GoldenQuery] | None = None,
        print_fn: Callable[[str], None] = print,
    ) -> None:
        self.config = config
        self.checkpoint = checkpoint
        self.target = target
        self.judge = judge
        self.golden_queries = golden_queries
        self.synth_queries = synth_queries or []
        self.print_fn = print_fn

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _all_queries(self) -> list[GoldenQuery]:
        return self.golden_queries + self.synth_queries

    def _judge_id(self) -> str:
        return type(self.judge).__name__

    def _get_sources_for_collection(self, collection: str) -> list[dict]:
        """Extract source dicts for a collection from the toolkit's rag config."""
        toolkit_cfg = self.config.target.resolved_toolkit_config()
        if toolkit_cfg.exists():
            with toolkit_cfg.open(encoding="utf-8") as fh:
                cfg = yaml.safe_load(fh) or {}
            config_dir = toolkit_cfg.parent
            col_data = (cfg.get("collections") or {}).get(collection, {})
            raw_sources = col_data.get("sources") or []
            resolved = []
            for src in raw_sources:
                raw_path = Path(src.get("path", ""))
                if not raw_path.is_absolute():
                    raw_path = config_dir / raw_path
                resolved.append(
                    {
                        "path": str(raw_path.resolve()),
                        "patterns": src.get("patterns", ["*.md"]),
                        "recursive": src.get("recursive", True),
                        "chunking": src.get("chunking"),
                    }
                )
            if resolved:
                return resolved

        # Fallback: derive from target path
        if collection == "docs":
            return [
                {
                    "path": str(self.config.target.path / "docs"),
                    "patterns": ["*.md"],
                    "recursive": True,
                    "chunking": None,
                }
            ]
        return [
            {
                "path": str(self.config.target.path),
                "patterns": ["*.py", "*.ts", "*.js", "*.sh"],
                "recursive": True,
                "chunking": None,
            }
        ]

    def _build_config_context(self, entry: SweepEntry) -> dict:
        sources = self._get_sources_for_collection(entry.collection)
        target_path = self.config.target.path

        if entry.collection == "docs":
            strategy = "markdown_header"
            max_tokens = entry.chunk_size
            overlap_tokens = entry.chunk_size // 2
            max_chars = None
            split_headers: list[str] | None = ["h1", "h2", "h3"]
            languages = None
            description = "Documentation collection"
        else:
            strategy = "source_code"
            max_tokens = None
            overlap_tokens = None
            max_chars = entry.chunk_size
            split_headers = None
            languages = {".py": "python", ".ts": "typescript", ".js": "javascript", ".sh": "bash"}
            description = "Code collection"

        return {
            "config_id": entry.config_id,
            "project_name": target_path.name,
            "collection_name": entry.collection,
            "collection_description": description,
            "model": entry.model_name,
            "dimensions": entry.dimensions,
            "sources": sources,
            "chunking_strategy": strategy,
            "chunking_max_tokens": max_tokens,
            "chunking_overlap_tokens": overlap_tokens,
            "chunking_max_chars": max_chars,
            "chunking_split_headers": split_headers,
            "chunking_languages": languages,
            "model_cache_dir": str(target_path / ".rag" / "models"),
            "search_default_top_k": max(self.config.sweep.top_k),
            "search_max_top_k": max(self.config.sweep.top_k) * 2,
            "search_rrf_k": 60,
            "search_vector_candidates": 20,
            "search_fts_candidates": 20,
        }

    # ── Index phase ───────────────────────────────────────────────────────────

    def _ensure_indexed(self, entry: SweepEntry, current: int, total: int) -> Path:
        """Generate config and index if not already done. Returns config path."""
        if self.checkpoint.is_indexed(entry.config_id):
            self.print_fn(t("cli.index.cached", config_id=entry.config_id))
            return self.target.config_path(entry.config_id)

        context = self._build_config_context(entry)
        template_path = Path(self.config.target.rag_config_template).resolve()
        cfg_path = self.target.generate_config(entry.config_id, context, template_path)

        self.print_fn(
            t("cli.index.starting", config_id=entry.config_id, current=current, total=total)
        )
        result = self.target.index(cfg_path, collection=entry.collection)

        if result.returncode != 0:
            msg = t("errors.index_failed", config_id=entry.config_id, error=result.stderr.strip())
            self.checkpoint.record_error(entry.config_id, None, "index", result.stderr)
            raise RuntimeError(msg)

        self.checkpoint.mark_indexed(entry.config_id, result.wall_time_s, entry.collection)
        self.print_fn(
            t("cli.index.complete", config_id=entry.config_id, elapsed=f"{result.wall_time_s:.1f}")
        )
        return cfg_path

    # ── Sanity check ──────────────────────────────────────────────────────────

    def _run_sanity_check(self, entry: SweepEntry, cfg_path: Path) -> None:
        """Abort if a trivial search returns no results (RAG broken)."""
        sources = self._get_sources_for_collection(entry.collection)
        sanity_query: str | None = None

        for src in sources:
            src_path = Path(src["path"])
            if not src_path.exists():
                continue
            patterns = src.get("patterns", ["*.md"])
            glob_fn = src_path.rglob if src.get("recursive", True) else src_path.glob
            for pattern in patterns:
                for f in glob_fn(pattern):
                    try:
                        text = f.read_text(encoding="utf-8", errors="ignore").strip()
                        for line in text.splitlines():
                            line = line.strip()
                            if len(line) > 40 and not line.startswith("#") and not line.startswith("```"):
                                sanity_query = line[:100]
                                break
                    except OSError:
                        continue
                    if sanity_query:
                        break
                if sanity_query:
                    break
            if sanity_query:
                break

        if not sanity_query:
            return  # empty corpus — skip check

        try:
            chunks = self.target.search(
                cfg_path, sanity_query, collection=entry.collection, top_k=3
            )
        except RuntimeError:
            chunks = []

        if not chunks:
            self.print_fn(t("cli.sanity.fail"))
            raise SystemExit(1)

        self.print_fn(t("cli.sanity.pass"))

    # ── Retrieval phase ───────────────────────────────────────────────────────

    def _search_collection_for_query(
        self, cfg_path: Path, query: GoldenQuery, entry: SweepEntry, top_k: int
    ) -> list[SearchChunk]:
        collection = str(query.collection)
        if collection == "all":
            collection = entry.collection
        return self.target.search(cfg_path, query.query, collection=collection, top_k=top_k)

    def _run_retrieval(
        self,
        entry: SweepEntry,
        cfg_path: Path,
        queries: list[GoldenQuery],
        top_k_values: list[int],
        in_memory: dict[tuple, list[dict]],
    ) -> None:
        for query in queries:
            for top_k in top_k_values:
                key = (query.id, top_k)
                if self.checkpoint.is_done(entry.config_id, query.id, top_k, "retrieved"):
                    continue
                try:
                    chunks = self._search_collection_for_query(cfg_path, query, entry, top_k)
                    chunk_dicts = [_chunk_to_record(c, top_k) for c in chunks]
                    self.checkpoint.mark_done(
                        entry.config_id,
                        query.id,
                        top_k,
                        "retrieved",
                        chunks=chunk_dicts,
                    )
                    in_memory[key] = chunk_dicts
                except RuntimeError as exc:
                    self.checkpoint.record_error(
                        entry.config_id, query.id, "retrieved", str(exc)
                    )

    # ── Judging phase ─────────────────────────────────────────────────────────

    def _run_judging(
        self,
        entry: SweepEntry,
        queries: list[GoldenQuery],
        top_k_values: list[int],
        retrieved: dict[tuple, list[dict]],
    ) -> None:
        judge_id = self._judge_id()
        for query in queries:
            for top_k in top_k_values:
                if self.checkpoint.is_done(entry.config_id, query.id, top_k, "judged"):
                    continue
                chunks = retrieved.get((query.id, top_k))
                if not chunks:
                    continue

                chunks_hash = _chunks_hash(chunks)
                cached = self.checkpoint.get_cached_judge(judge_id, query.id, chunks_hash)
                if cached is not None:
                    score = float(cached.get("score", 0.0))
                else:
                    texts = [c.get("content", c.get("file_path", "")) for c in chunks]
                    try:
                        judgments = self.judge.score_batch(query.query, texts)
                    except Exception as exc:
                        self.checkpoint.record_error(
                            entry.config_id, query.id, "judged", str(exc)
                        )
                        continue
                    score = (
                        sum(j.score for j in judgments) / len(judgments) if judgments else 0.0
                    )
                    self.checkpoint.record_judge(
                        judge_id,
                        query.id,
                        chunks_hash,
                        {
                            "score": score,
                            "judgments": [
                                {"score": j.score, "reasoning": j.reasoning} for j in judgments
                            ],
                        },
                    )
                self.checkpoint.mark_done(
                    entry.config_id, query.id, top_k, "judged", score=score
                )

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Execute the full sweep: index → retrieve → judge for every matrix entry."""
        sweep_entries = self.config.expand_sweep()
        queries = self._all_queries()
        top_k_values = self.config.sweep.top_k
        n_entries = len(sweep_entries)
        sanity_done = False

        for i, entry in enumerate(sweep_entries, start=1):
            cfg_path = self._ensure_indexed(entry, current=i, total=n_entries)

            if not sanity_done:
                self._run_sanity_check(entry, cfg_path)
                sanity_done = True

            # Keep retrieved chunks in memory for the judging phase within this run.
            # On resume, retrieval is idempotent (toolkit search is deterministic).
            in_memory: dict[tuple, list[dict]] = {}
            self._run_retrieval(entry, cfg_path, queries, top_k_values, in_memory)
            self._run_judging(entry, queries, top_k_values, in_memory)

            done_q = sum(
                1
                for q in queries
                for k in top_k_values
                if self.checkpoint.is_done(entry.config_id, q.id, k, "judged")
            )
            total_q = len(queries) * len(top_k_values)
            self.print_fn(
                t(
                    "cli.judge.progress",
                    done=done_q,
                    total=total_q,
                    pct=int(100 * done_q / total_q) if total_q else 0,
                )
            )
