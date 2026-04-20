from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from bench.config import (
    COLLECTION_MODELS,
    BenchConfig,
    SweepEntry,
    SweepSettings,
    TargetSettings,
)


# ── BenchConfig.from_target ───────────────────────────────────────────────────


def test_from_target_sets_path(tmp_path):
    cfg = BenchConfig.from_target(tmp_path)
    assert cfg.target.path == tmp_path


def test_from_target_expands_tilde(tmp_path):
    cfg = BenchConfig.from_target("~")
    assert cfg.target.path == Path.home()


def test_from_target_defaults_lang_en(tmp_path):
    cfg = BenchConfig.from_target(tmp_path)
    assert cfg.lang == "en"


def test_from_target_accepts_overrides(tmp_path):
    cfg = BenchConfig.from_target(tmp_path, lang="pt")
    assert cfg.lang == "pt"


# ── BenchConfig.from_yaml ─────────────────────────────────────────────────────


def test_from_yaml_reads_target(tmp_path):
    config_file = tmp_path / "bench.yaml"
    data = {
        "lang": "pt",
        "target": {"path": str(tmp_path)},
    }
    config_file.write_text(yaml.dump(data), encoding="utf-8")
    cfg = BenchConfig.from_yaml(config_file)
    assert cfg.lang == "pt"
    assert cfg.target.path == tmp_path


def test_from_yaml_uses_defaults_for_sweep(tmp_path):
    config_file = tmp_path / "bench.yaml"
    data = {"target": {"path": str(tmp_path)}}
    config_file.write_text(yaml.dump(data), encoding="utf-8")
    cfg = BenchConfig.from_yaml(config_file)
    assert cfg.sweep.collections == ["docs", "code"]
    assert 512 in cfg.sweep.chunk_sizes["docs"]


# ── expand_sweep ──────────────────────────────────────────────────────────────


def test_expand_sweep_count_default():
    """Default matrix: 2 collections × 3 chunks × 3 models = 18 entries."""
    cfg = BenchConfig.from_target("/tmp/fake")
    entries = cfg.expand_sweep()
    assert len(entries) == 18


def test_expand_sweep_all_are_sweep_entries():
    cfg = BenchConfig.from_target("/tmp/fake")
    for e in cfg.expand_sweep():
        assert isinstance(e, SweepEntry)


def test_expand_sweep_config_id_format():
    """Config IDs follow {collection}-c{chunk}-{slug} format."""
    cfg = BenchConfig.from_target("/tmp/fake")
    for e in cfg.expand_sweep():
        assert e.config_id.startswith(e.collection)
        assert f"-c{e.chunk_size}-" in e.config_id


def test_expand_sweep_docs_models():
    cfg = BenchConfig.from_target("/tmp/fake")
    docs_entries = [e for e in cfg.expand_sweep() if e.collection == "docs"]
    model_names = {e.model_name for e in docs_entries}
    expected = {m for m, _ in COLLECTION_MODELS["docs"].values()}
    assert model_names == expected


def test_expand_sweep_code_models():
    cfg = BenchConfig.from_target("/tmp/fake")
    code_entries = [e for e in cfg.expand_sweep() if e.collection == "code"]
    model_names = {e.model_name for e in code_entries}
    expected = {m for m, _ in COLLECTION_MODELS["code"].values()}
    assert model_names == expected


def test_expand_sweep_small_matrix():
    """Single collection, one chunk, one model → 1 entry."""
    cfg = BenchConfig(
        target=TargetSettings(path=Path("/tmp/fake")),
        sweep=SweepSettings(
            collections=["docs"],
            chunk_sizes={"docs": [512]},
            models={"docs": ["small"]},
            top_k=[5],
        ),
    )
    entries = cfg.expand_sweep()
    assert len(entries) == 1
    assert entries[0].collection == "docs"
    assert entries[0].chunk_size == 512
    assert entries[0].model_tier == "small"


def test_expand_sweep_unknown_tier_skipped():
    """Unknown model tier silently skipped."""
    cfg = BenchConfig(
        target=TargetSettings(path=Path("/tmp/fake")),
        sweep=SweepSettings(
            collections=["docs"],
            chunk_sizes={"docs": [512]},
            models={"docs": ["nonexistent"]},
            top_k=[5],
        ),
    )
    assert cfg.expand_sweep() == []


def test_expand_sweep_no_duplicate_config_ids():
    cfg = BenchConfig.from_target("/tmp/fake")
    ids = [e.config_id for e in cfg.expand_sweep()]
    assert len(ids) == len(set(ids))


# ── TargetSettings.resolved_toolkit_config ───────────────────────────────────


def test_resolved_toolkit_config_default(tmp_path):
    s = TargetSettings(path=tmp_path)
    expected = tmp_path / "rag" / "rag.config.yaml"
    assert s.resolved_toolkit_config() == expected.resolve()


def test_resolved_toolkit_config_override(tmp_path):
    custom = tmp_path / "custom.yaml"
    s = TargetSettings(path=tmp_path, toolkit_rag_config=custom)
    assert s.resolved_toolkit_config() == custom.resolve()


# ── ScoringSettings defaults ──────────────────────────────────────────────────


def test_scoring_weights_sum_to_one():
    cfg = BenchConfig.from_target("/tmp/fake")
    w = cfg.scoring.composite_weights
    total = w.coverage + w.token_to_coverage_ratio + w.precision_at_5
    assert abs(total - 1.0) < 1e-9
