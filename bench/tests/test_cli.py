from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bench.cli import _build_parser, _make_run_id


# ── _make_run_id ──────────────────────────────────────────────────────────────


def test_make_run_id_format(tmp_path):
    run_id = _make_run_id(tmp_path, "en")
    parts = run_id.split("-")
    # YYYY-MM-DD-toolkit-baseline-{4char_hash}
    assert parts[0].isdigit() and len(parts[0]) == 4  # year
    assert parts[1].isdigit() and len(parts[1]) == 2  # month
    assert parts[2].isdigit() and len(parts[2]) == 2  # day
    assert "baseline" in run_id


def test_make_run_id_deterministic(tmp_path):
    a = _make_run_id(tmp_path, "en")
    b = _make_run_id(tmp_path, "en")
    assert a == b


def test_make_run_id_differs_by_path(tmp_path):
    a = _make_run_id(tmp_path / "a", "en")
    b = _make_run_id(tmp_path / "b", "en")
    assert a != b


# ── Parser structure ──────────────────────────────────────────────────────────


def test_parser_has_run_subcommand():
    parser = _build_parser()
    args = parser.parse_args(["run", "--target", "/tmp/x", "--yes"])
    assert args.command == "run"


def test_parser_has_resume_subcommand():
    parser = _build_parser()
    args = parser.parse_args(["resume", "run-001"])
    assert args.command == "resume"
    assert args.run_id == "run-001"


def test_parser_has_status_subcommand():
    parser = _build_parser()
    args = parser.parse_args(["status"])
    assert args.command == "status"


def test_parser_has_report_subcommand():
    parser = _build_parser()
    args = parser.parse_args(["report", "run-001"])
    assert args.command == "report"
    assert args.run_id == "run-001"


def test_parser_has_retry_failed_subcommand():
    parser = _build_parser()
    args = parser.parse_args(["retry-failed", "run-001"])
    assert args.command == "retry-failed"


def test_parser_lang_flag():
    parser = _build_parser()
    args = parser.parse_args(["--lang", "pt", "status"])
    assert args.lang == "pt"


def test_parser_yes_flag():
    parser = _build_parser()
    args = parser.parse_args(["run", "--target", "/tmp/x", "--yes"])
    assert args.yes is True


def test_parser_judge_type():
    parser = _build_parser()
    args = parser.parse_args(["run", "--target", "/tmp/x", "--judge", "claude", "--yes"])
    assert args.judge_type == "claude"


# ── cmd_status ────────────────────────────────────────────────────────────────


def test_cmd_status_shows_all_runs(tmp_path):
    from bench.cli import cmd_status
    from bench.persistence import append_jsonl, write_json_atomic

    state_dir = tmp_path / ".bench-state"
    run_dir = state_dir / "run-abc"
    run_dir.mkdir(parents=True)
    write_json_atomic(run_dir / "manifest.json", {"run_id": "run-abc", "judge": {"type": "x"}})
    append_jsonl(run_dir / "progress.jsonl", {"phase": "judged", "config_id": "c", "query_id": "q", "top_k": 5})

    ns = argparse.Namespace(run_id=None, state_dir=str(state_dir))
    cmd_status(ns)  # should not raise


def test_cmd_status_specific_run(tmp_path):
    from bench.cli import cmd_status
    from bench.persistence import append_jsonl, write_json_atomic

    state_dir = tmp_path / ".bench-state"
    run_dir = state_dir / "run-xyz"
    run_dir.mkdir(parents=True)
    write_json_atomic(run_dir / "manifest.json", {
        "run_id": "run-xyz",
        "work_units_total": 100,
        "judge": {"type": "cross-encoder"},
    })
    append_jsonl(run_dir / "progress.jsonl", {"phase": "judged", "config_id": "c", "query_id": "q", "top_k": 5})

    ns = argparse.Namespace(run_id="run-xyz", state_dir=str(state_dir))
    cmd_status(ns)  # should not raise


def test_cmd_status_missing_run_exits(tmp_path):
    from bench.cli import cmd_status

    ns = argparse.Namespace(run_id="nonexistent", state_dir=str(tmp_path / ".bench-state"))
    with pytest.raises(SystemExit):
        cmd_status(ns)


# ── cmd_report ────────────────────────────────────────────────────────────────


def test_cmd_report_generates_file(tmp_path):
    from bench.cli import cmd_report
    from bench.persistence import write_json_atomic

    state_dir = tmp_path / ".bench-state"
    run_dir = state_dir / "run-rep"
    run_dir.mkdir(parents=True)
    write_json_atomic(run_dir / "manifest.json", {"run_id": "run-rep", "judge": {}, "corpus": {}})
    (run_dir / "progress.jsonl").touch()

    out_dir = tmp_path / "out"
    ns = argparse.Namespace(
        run_id="run-rep",
        state_dir=str(state_dir),
        output=str(out_dir),
    )
    cmd_report(ns)
    assert (out_dir / "REPORT.md").exists()


# ── cmd_retry_failed ──────────────────────────────────────────────────────────


def test_cmd_retry_failed_none(tmp_path):
    from bench.cli import cmd_retry_failed
    from bench.persistence import write_json_atomic

    state_dir = tmp_path / ".bench-state"
    run_dir = state_dir / "run-no-err"
    run_dir.mkdir(parents=True)
    write_json_atomic(run_dir / "manifest.json", {"run_id": "run-no-err"})
    (run_dir / "errors.jsonl").touch()
    (run_dir / "progress.jsonl").touch()

    ns = argparse.Namespace(run_id="run-no-err", state_dir=str(state_dir))
    cmd_retry_failed(ns)  # should print "none" message without raising
