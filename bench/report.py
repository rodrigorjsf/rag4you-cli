"""Report renderer — reads progress.jsonl, computes metrics, writes REPORT.md."""

from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from bench.i18n import t
from bench.metrics import mrr, precision_at_k, self_sufficiency_rate
from bench.persistence import read_json, read_jsonl


def _composite(
    coverage: float,
    tok_ratio: float,
    p_at_5: float,
    weights: dict[str, float],
) -> float:
    return (
        weights.get("coverage", 0.5) * coverage
        + weights.get("token_to_coverage_ratio", 0.3) * tok_ratio
        + weights.get("precision_at_5", 0.2) * p_at_5
    )


def _tok_ratio(coverage: float, tokens: float) -> float:
    if coverage <= 0.0 or tokens <= 0.0:
        return 0.0
    return coverage / math.log1p(tokens)


def compute_config_stats(
    progress_path: Path,
    golden_index: dict[str, dict],
    top_k: int,
    weights: dict[str, float],
    ss_threshold: float,
) -> list[dict[str, Any]]:
    """Compute per-config aggregated metrics from progress.jsonl."""
    records = read_jsonl(progress_path)

    # Group: config_id → query_id → top_k → phase → data
    by_config: dict[str, dict] = defaultdict(
        lambda: {"retrieved": defaultdict(dict), "judged": defaultdict(dict)}
    )
    for rec in records:
        cid = rec.get("config_id", "")
        qid = rec.get("query_id", "")
        k = rec.get("top_k", top_k)
        phase = rec.get("phase", "")
        if phase == "retrieved":
            by_config[cid]["retrieved"][(qid, k)] = rec.get("chunks", [])
        elif phase == "judged":
            by_config[cid]["judged"][(qid, k)] = rec.get("score", 0.0)

    stats: list[dict[str, Any]] = []
    for cid, data in sorted(by_config.items()):
        retrieved = data["retrieved"]
        judged = data["judged"]

        # Collect at the target top_k
        queries_results: list[tuple[list[str], set[str]]] = []
        coverages: list[float] = []
        tokens_list: list[float] = []

        for (qid, k), chunks in retrieved.items():
            if k != top_k:
                continue
            golden = golden_index.get(qid, {})
            expected = set(golden.get("expected_files", []))
            retrieved_files = [c.get("file_path", "") for c in chunks]
            queries_results.append((retrieved_files, expected))

            score = judged.get((qid, k), 0.0)
            coverages.append(float(score))

            tokens = sum(c.get("token_count", 0) for c in chunks)
            tokens_list.append(float(tokens))

        if not queries_results:
            continue

        p5 = sum(
            precision_at_k(files, expected, min(top_k, 5))
            for files, expected in queries_results
            if expected
        ) / max(1, sum(1 for _, e in queries_results if e))

        mrr_val = mrr([(f, e) for f, e in queries_results if e])
        hit_rate = sum(
            1 for files, expected in queries_results if expected and any(f in expected for f in files)
        ) / max(1, sum(1 for _, e in queries_results if e))

        avg_cov = sum(coverages) / max(1, len(coverages))
        avg_tok = sum(tokens_list) / max(1, len(tokens_list))
        tok_ratio = _tok_ratio(avg_cov, avg_tok)
        ss = self_sufficiency_rate(coverages, ss_threshold)
        comp = _composite(avg_cov, tok_ratio, p5, weights)

        # Parse config_id: {collection}-c{chunk}-{slug}
        parts = cid.split("-")
        collection = parts[0] if parts else ""
        chunk_size = int(parts[1][1:]) if len(parts) > 1 and parts[1].startswith("c") else 0
        model_slug = "-".join(parts[2:]) if len(parts) > 2 else ""

        stats.append(
            {
                "config_id": cid,
                "collection": collection,
                "chunk_size": chunk_size,
                "model_slug": model_slug,
                "top_k": top_k,
                "n_queries": len(queries_results),
                "precision_at_k": round(p5, 4),
                "mrr": round(mrr_val, 4),
                "hit_rate": round(hit_rate, 4),
                "coverage": round(avg_cov, 4),
                "tokens_per_query": round(avg_tok, 1),
                "token_to_coverage_ratio": round(tok_ratio, 4),
                "self_sufficiency_rate": round(ss, 4),
                "composite": round(comp, 4),
            }
        )

    stats.sort(key=lambda s: s["composite"], reverse=True)
    return stats


def find_failure_cases(
    progress_path: Path,
    golden_index: dict[str, dict],
    top_k: int,
    threshold: float = 0.4,
) -> list[dict[str, Any]]:
    """Find queries where every config produced coverage below threshold."""
    records = read_jsonl(progress_path)

    # query_id → config_id → score
    scores: dict[str, dict[str, float]] = defaultdict(dict)
    for rec in records:
        if rec.get("phase") == "judged" and rec.get("top_k") == top_k:
            scores[rec["query_id"]][rec["config_id"]] = float(rec.get("score", 0.0))

    failures = []
    for qid, config_scores in scores.items():
        if not config_scores:
            continue
        max_cov = max(config_scores.values())
        if max_cov < threshold:
            golden = golden_index.get(qid, {})
            failures.append(
                {
                    "query_id": qid,
                    "query": golden.get("query", qid),
                    "max_coverage": round(max_cov, 4),
                    "expected_files": golden.get("expected_files", []),
                }
            )
    failures.sort(key=lambda f: f["max_coverage"])
    return failures


def _load_golden_index(golden_path: Path | None = None) -> dict[str, dict]:
    if golden_path is None:
        golden_path = Path(__file__).parent / "golden" / "dataset.yaml"
    if not golden_path.exists():
        return {}
    with golden_path.open(encoding="utf-8") as fh:
        rows = yaml.safe_load(fh) or []
    return {r["id"]: r for r in rows}


def render(
    run_dir: Path,
    output_path: Path,
    top_k: int = 5,
    weights: dict[str, float] | None = None,
    ss_threshold: float = 0.8,
    golden_path: Path | None = None,
) -> Path:
    """Render REPORT.md from checkpoint state files.

    Returns the path to the written report.
    """
    if weights is None:
        weights = {"coverage": 0.5, "token_to_coverage_ratio": 0.3, "precision_at_5": 0.2}

    run_dir = Path(run_dir)
    progress_path = run_dir / "progress.jsonl"
    manifest_path = run_dir / "manifest.json"

    manifest: dict = {}
    if manifest_path.exists():
        manifest = read_json(manifest_path)

    golden_index = _load_golden_index(golden_path)
    stats = compute_config_stats(progress_path, golden_index, top_k, weights, ss_threshold)
    failures = find_failure_cases(progress_path, golden_index, top_k)

    run_id = manifest.get("run_id", run_dir.name)
    judge_info = manifest.get("judge", {})
    judge_type = judge_info.get("type", "unknown")
    judge_model = judge_info.get("model", "")
    bench_version = manifest.get("bench_version", "0.1.0")
    target_info = manifest.get("rag_target", {})
    target_path = target_info.get("path", "")
    git_sha = target_info.get("git_sha", "")
    created_at = manifest.get("created_at", "")
    total_files = manifest.get("corpus", {}).get("total_files", 0)
    lang = manifest.get("lang", "en")
    is_approx = judge_type == "cross-encoder"

    # Per-collection winners
    docs_winner = next((s for s in stats if s["collection"] == "docs"), None)
    code_winner = next((s for s in stats if s["collection"] == "code"), None)
    avg_ss = sum(s["self_sufficiency_rate"] for s in stats) / max(1, len(stats))
    fail_pct = int(100 * len(failures) / max(1, len(golden_index)))

    lines: list[str] = []

    def h(key: str, level: int = 2, **kw: object) -> None:
        prefix = "#" * level
        lines.append(f"{prefix} {t(key, **kw)}")

    lines.append(f"# RAG Baseline Report — {run_id}")
    lines.append(f"_Generated {created_at}_")
    lines.append("")

    # TL;DR
    h("report.tldr_heading", 2)
    lines.append("")
    if docs_winner:
        lines.append(
            f"- Composite winner (docs): chunk={docs_winner['chunk_size']}, "
            f"model={docs_winner['model_slug']}"
        )
    if code_winner:
        lines.append(
            f"- Composite winner (code): chunk={code_winner['chunk_size']}, "
            f"model={code_winner['model_slug']}"
        )
    lines.append(t("report.self_sufficiency", pct=int(avg_ss * 100), k=top_k))
    if fail_pct > 0:
        lines.append(t("report.no_relevant_alert", pct=fail_pct, k=top_k))
    lines.append("")

    # Recommendations
    h("report.recommendations_heading", 2)
    lines.append("")
    if docs_winner:
        lines.append(f"- Default chunk for docs: {docs_winner['chunk_size']}")
        lines.append(f"- Recommended docs model tier: {docs_winner['model_slug']}")
    if code_winner:
        lines.append(f"- Default chunk for code: {code_winner['chunk_size']}")
        lines.append(f"- Recommended code model tier: {code_winner['model_slug']}")
    lines.append("")

    # Configs ranking
    h("report.configs_ranking_heading", 2)
    lines.append("")
    header = "| Rank | Collection | Chunk | Model | Coverage | Tokens/q | Ratio | P@k | Hit Rate | Composite |"
    lines.append(header)
    lines.append("|------|------------|-------|-------|----------|----------|-------|-----|----------|-----------|")
    for rank, s in enumerate(stats, start=1):
        lines.append(
            f"| {rank} | {s['collection']} | {s['chunk_size']} | {s['model_slug']} "
            f"| {s['coverage']:.3f} | {s['tokens_per_query']:.0f} "
            f"| {s['token_to_coverage_ratio']:.3f} | {s['precision_at_k']:.3f} "
            f"| {s['hit_rate']:.3f} | {s['composite']:.3f} |"
        )
    lines.append("")

    # Failure analysis
    h("report.failure_analysis_heading", 2)
    lines.append("")
    if failures:
        for f in failures[:10]:
            lines.append(f"- `{f['query_id']}`: \"{f['query'][:80]}\" — max coverage: {f['max_coverage']:.3f}")
            if f.get("expected_files"):
                lines.append(f"  - Expected: {', '.join(f['expected_files'][:3])}")
    else:
        lines.append("_No queries failed across all configs (coverage ≥ threshold)._")
    lines.append("")

    # Per-collection details
    h("report.per_collection_heading", 2)
    lines.append("")
    for col in ("docs", "code"):
        col_stats = [s for s in stats if s["collection"] == col]
        if not col_stats:
            continue
        lines.append(f"### {col.capitalize()}")
        lines.append("")
        lines.append(f"| Config | Coverage | MRR | Composite |")
        lines.append("|--------|----------|-----|-----------|")
        for s in col_stats:
            lines.append(
                f"| {s['config_id']} | {s['coverage']:.3f} | {s['mrr']:.3f} | {s['composite']:.3f} |"
            )
        lines.append("")

    # Limitations
    h("report.limitations_heading", 2)
    lines.append("")
    if is_approx:
        lines.append(t("report.judge_approx_note", judge_model=judge_model or judge_type))
    lines.append(
        f"- Corpus: {target_path} ({total_files} files). Does not test scale."
    )
    lines.append("- Not measured: concurrency, cold-start, FTS-only vs vector-only ablation.")
    lines.append("")

    # Reproducibility
    h("report.reproducibility_heading", 2)
    lines.append("")
    lines.append(f"- Bench version: {bench_version}")
    if git_sha:
        lines.append(f"- Toolkit git SHA: {git_sha}")
    lines.append(f"- Resume: `bench resume {run_id}`")
    lines.append("")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
