"""CLI entry point — subcommands: run, resume, status, report, retry-failed."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path


def _make_run_id(target_path: Path, lang: str) -> str:
    date = datetime.date.today().isoformat()
    slug = "toolkit-baseline"
    seed = json.dumps({"target": str(target_path), "lang": lang}, sort_keys=True).encode()
    suffix = hashlib.sha1(seed).hexdigest()[:4]
    return f"{date}-{slug}-{suffix}"


def _build_judge(config: object) -> object:
    from bench.config import BenchConfig

    cfg = config  # type: BenchConfig  # type: ignore[assignment]
    jtype = cfg.judge.type

    if jtype == "cross-encoder":
        from bench.judges.cross_encoder import CrossEncoderJudge

        return CrossEncoderJudge(model=cfg.judge.cross_encoder.model)

    if jtype == "claude":
        import os

        from bench.judges.claude import ClaudeJudge

        api_key = os.environ.get(cfg.judge.claude.api_key_env)
        if not api_key:
            from bench.i18n import t

            print(
                t(
                    "errors.missing_api_key",
                    env_var=cfg.judge.claude.api_key_env,
                    judge_type="claude",
                ),
                file=sys.stderr,
            )
            sys.exit(1)
        return ClaudeJudge(model=cfg.judge.claude.model, api_key=api_key)

    if jtype == "openai":
        import os

        from bench.judges.openai import OpenAIJudge

        api_key = os.environ.get(cfg.judge.openai.api_key_env)
        if not api_key:
            from bench.i18n import t

            print(
                t(
                    "errors.missing_api_key",
                    env_var=cfg.judge.openai.api_key_env,
                    judge_type="openai",
                ),
                file=sys.stderr,
            )
            sys.exit(1)
        return OpenAIJudge(model=cfg.judge.openai.model, api_key=api_key)

    if jtype == "ollama":
        from bench.judges.ollama import OllamaJudge

        return OllamaJudge(
            model=cfg.judge.ollama.model,
            base_url=cfg.judge.ollama.base_url,
        )

    print(f"Unknown judge type: {jtype!r}", file=sys.stderr)
    sys.exit(1)


# ── Commands ──────────────────────────────────────────────────────────────────


def cmd_run(args: argparse.Namespace) -> None:
    from bench.checkpoint import Checkpoint
    from bench.config import BenchConfig
    from bench.i18n import set_locale, t
    from bench.sweep import SweepRunner, load_golden_queries
    from bench.target import RagTarget

    if args.lang:
        set_locale(args.lang)

    if args.config:
        config = BenchConfig.from_yaml(Path(args.config))
    else:
        overrides: dict = {}
        if args.lang:
            overrides["lang"] = args.lang
        if args.judge_type:
            from bench.config import JudgeSettings
            overrides["judge"] = JudgeSettings(type=args.judge_type)
        config = BenchConfig.from_target(args.target, **overrides)

    run_id = args.run_id or _make_run_id(config.target.path, config.lang)
    state_dir = Path(args.state_dir) if args.state_dir else config.state_dir

    # Show run plan
    entries = config.expand_sweep()
    golden = load_golden_queries()
    top_k_values = config.sweep.top_k
    n_units = len(entries) * len(golden) * len(top_k_values)

    print(t("cli.run.plan",
        n_configs=len(entries),
        n_queries=len(golden),
        n_top_k=len(top_k_values),
        n_units=n_units,
    ))
    print(t("cli.run.judge_info",
        judge_type=config.judge.type,
        judge_model=getattr(getattr(config.judge, config.judge.type.replace("-", "_"), None), "model", ""),
    ))

    if not args.yes:
        confirm = input(t("cli.run.cost_confirm") + " ")
        if confirm.strip().lower() in ("n", "no"):
            print(t("cli.run.aborted"))
            return

    corpus_snap = _build_corpus_snapshot(config)
    manifest = {
        "run_id": run_id,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "bench_version": "0.1.0",
        "rag_target": {
            "path": str(config.target.path),
            "git_sha": _get_git_sha(config.target.path),
        },
        "corpus": corpus_snap,
        "judge": {
            "type": config.judge.type,
            "model": getattr(
                getattr(config.judge, config.judge.type.replace("-", "_"), None), "model", ""
            ),
        },
        "sweep": [
            {"config_id": e.config_id, "collection": e.collection,
             "chunk": e.chunk_size, "model": e.model_name}
            for e in entries
        ],
        "lang": config.lang,
    }

    print(t("cli.run.starting", run_id=run_id))
    cp = Checkpoint.create(run_id, state_dir, manifest)
    target = RagTarget(
        toolkit_path=config.target.path,
        state_dir=state_dir / run_id,
    )
    judge = _build_judge(config)

    try:
        with cp:
            runner = SweepRunner(config, cp, target, judge, golden)
            runner.run()
    finally:
        if hasattr(judge, "close"):
            judge.close()

    report_path = _write_report(run_id, state_dir, config)
    print(t("cli.run.complete", run_id=run_id, report_path=str(report_path)))


def cmd_resume(args: argparse.Namespace) -> None:
    from bench.checkpoint import Checkpoint, CorpusDriftError
    from bench.config import BenchConfig
    from bench.i18n import set_locale, t
    from bench.sweep import SweepRunner, load_golden_queries
    from bench.target import RagTarget

    state_dir = Path(args.state_dir) if args.state_dir else Path(".bench-state")
    run_dir = state_dir / args.run_id
    if not run_dir.exists():
        print(t("cli.resume.no_run", run_id=args.run_id), file=sys.stderr)
        sys.exit(1)

    try:
        cp = Checkpoint.load(args.run_id, state_dir, allow_drift=args.allow_corpus_drift)
    except CorpusDriftError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    manifest = cp.manifest
    if manifest.get("lang"):
        set_locale(manifest["lang"])

    config = BenchConfig.from_target(
        manifest["rag_target"]["path"],
        lang=manifest.get("lang", "en"),
    )

    # Count progress
    from bench.persistence import read_jsonl

    done = sum(
        1
        for r in read_jsonl(run_dir / "progress.jsonl")
        if r.get("phase") == "judged"
    )
    sweep = manifest.get("sweep", [])
    golden = load_golden_queries()
    total = len(sweep) * len(golden) * len(config.sweep.top_k)

    print(t("cli.resume.resuming", done=done, total=total, pct=int(100 * done / max(1, total))))
    print(t("cli.resume.found_units", run_id=args.run_id, done=done, total=total))

    target = RagTarget(
        toolkit_path=config.target.path,
        state_dir=state_dir / args.run_id,
    )
    judge = _build_judge(config)

    try:
        with cp:
            runner = SweepRunner(config, cp, target, judge, golden)
            runner.run()
    finally:
        if hasattr(judge, "close"):
            judge.close()

    report_path = _write_report(args.run_id, state_dir, config)
    print(t("cli.run.complete", run_id=args.run_id, report_path=str(report_path)))


def cmd_status(args: argparse.Namespace) -> None:
    from bench.i18n import t
    from bench.persistence import read_jsonl

    state_dir = Path(args.state_dir) if args.state_dir else Path(".bench-state")

    if args.run_id:
        run_dir = state_dir / args.run_id
        if not run_dir.exists():
            print(t("cli.status.not_found", run_id=args.run_id), file=sys.stderr)
            sys.exit(1)
        progress = read_jsonl(run_dir / "progress.jsonl")
        done = sum(1 for r in progress if r.get("phase") == "judged")
        from bench.persistence import read_json

        manifest = {}
        if (run_dir / "manifest.json").exists():
            manifest = read_json(run_dir / "manifest.json")
        total = manifest.get("work_units_total", "?")
        judge = manifest.get("judge", {}).get("type", "?")
        pct = int(100 * done / int(total)) if str(total).isdigit() else 0
        print(t("cli.status.running", run_id=args.run_id, done=done, total=total, pct=pct, judge=judge))
    else:
        if not state_dir.exists():
            print(t("cli.status.no_runs", state_dir=str(state_dir)))
            return
        runs = [d for d in state_dir.iterdir() if d.is_dir()]
        if not runs:
            print(t("cli.status.no_runs", state_dir=str(state_dir)))
            return
        for run_dir in sorted(runs):
            progress = read_jsonl(run_dir / "progress.jsonl")
            done = sum(1 for r in progress if r.get("phase") == "judged")
            print(f"  {run_dir.name}: {done} judged")


def cmd_report(args: argparse.Namespace) -> None:
    from bench.i18n import t
    from bench.report import render

    state_dir = Path(args.state_dir) if args.state_dir else Path(".bench-state")
    run_dir = state_dir / args.run_id
    if not run_dir.exists():
        print(t("cli.status.not_found", run_id=args.run_id), file=sys.stderr)
        sys.exit(1)

    reports_dir = Path(args.output) if args.output else Path("reports") / args.run_id
    output_path = reports_dir / "REPORT.md"

    print(t("cli.report.generating", run_id=args.run_id))
    render(run_dir, output_path)
    print(t("cli.report.saved", path=str(output_path)))


def cmd_retry_failed(args: argparse.Namespace) -> None:
    from bench.i18n import t
    from bench.persistence import read_jsonl

    state_dir = Path(args.state_dir) if args.state_dir else Path(".bench-state")
    run_dir = state_dir / args.run_id
    if not run_dir.exists():
        print(t("cli.status.not_found", run_id=args.run_id), file=sys.stderr)
        sys.exit(1)

    errors = read_jsonl(run_dir / "errors.jsonl")
    if not errors:
        print(t("cli.retry_failed.none", run_id=args.run_id))
        return
    print(t("cli.retry_failed.found", n=len(errors), run_id=args.run_id))
    # Resuming from checkpoint handles retry automatically (skips done, re-runs errors)
    args_resume = argparse.Namespace(
        run_id=args.run_id,
        state_dir=args.state_dir,
        allow_corpus_drift=False,
    )
    cmd_resume(args_resume)


# ── Utilities ─────────────────────────────────────────────────────────────────


def _build_corpus_snapshot(config: object) -> dict:
    from bench.config import BenchConfig
    from bench.corpus import CorpusLoader

    cfg = config  # type: BenchConfig  # type: ignore[assignment]
    toolkit_cfg = cfg.target.resolved_toolkit_config()
    loader = CorpusLoader(cfg.target.path)
    if toolkit_cfg.exists():
        return loader.snapshot(toolkit_cfg)
    return {"files": [], "hash": "", "total_files": 0}


def _get_git_sha(path: Path) -> str:
    try:
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(path),
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def _write_report(run_id: str, state_dir: Path, config: object) -> Path:
    from bench.config import BenchConfig
    from bench.report import render

    cfg = config  # type: BenchConfig  # type: ignore[assignment]
    run_dir = state_dir / run_id
    reports_dir = cfg.reports_dir / run_id
    output_path = reports_dir / "REPORT.md"
    render(run_dir, output_path)
    return output_path


# ── Argument parser ───────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bench",
        description="Benchmark harness for toolkit RAG evaluation.",
    )
    parser.add_argument(
        "--lang",
        default=None,
        help="Output language (en, pt). Overrides config and RAG4YOU_LANG env.",
    )

    subs = parser.add_subparsers(dest="command")

    # run
    p_run = subs.add_parser("run", help="Start a new benchmark run.")
    p_run.add_argument("--target", required=False, help="Path to the toolkit target directory.")
    p_run.add_argument("--config", default=None, help="Path to bench config YAML.")
    p_run.add_argument("--judge", dest="judge_type", default=None,
                       choices=["cross-encoder", "claude", "openai", "ollama"])
    p_run.add_argument("--run-id", dest="run_id", default=None)
    p_run.add_argument("--state-dir", dest="state_dir", default=None)
    p_run.add_argument("--yes", "-y", action="store_true", help="Skip cost confirmation.")
    p_run.set_defaults(func=cmd_run)

    # resume
    p_resume = subs.add_parser("resume", help="Resume an interrupted run.")
    p_resume.add_argument("run_id")
    p_resume.add_argument("--state-dir", dest="state_dir", default=None)
    p_resume.add_argument("--allow-corpus-drift", dest="allow_corpus_drift",
                          action="store_true")
    p_resume.set_defaults(func=cmd_resume)

    # status
    p_status = subs.add_parser("status", help="Show run progress.")
    p_status.add_argument("run_id", nargs="?", default=None)
    p_status.add_argument("--state-dir", dest="state_dir", default=None)
    p_status.set_defaults(func=cmd_status)

    # report
    p_report = subs.add_parser("report", help="(Re-)generate REPORT.md from a run.")
    p_report.add_argument("run_id")
    p_report.add_argument("--state-dir", dest="state_dir", default=None)
    p_report.add_argument("--output", default=None, help="Output directory for the report.")
    p_report.set_defaults(func=cmd_report)

    # retry-failed
    p_retry = subs.add_parser("retry-failed", help="Retry failed work units in a run.")
    p_retry.add_argument("run_id")
    p_retry.add_argument("--state-dir", dest="state_dir", default=None)
    p_retry.set_defaults(func=cmd_retry_failed)

    return parser


def main() -> None:
    parser = _build_parser()
    args, _ = parser.parse_known_args()

    if args.lang:
        from bench.i18n import set_locale

        set_locale(args.lang)

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
