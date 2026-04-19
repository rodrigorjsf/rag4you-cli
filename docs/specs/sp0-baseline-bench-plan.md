# SP0 Implementation Plan — Baseline Benchmark Harness

Spec: `docs/specs/sp0-baseline-bench.md` — approved, implementation started 2026-04-19.

## Pre-implementation findings

| Check | Result |
|---|---|
| fastembed version | 0.8.0 |
| `BAAI/bge-small-en-v1.5` | ✓ available |
| `BAAI/bge-base-en-v1.5` | ✓ available |
| `BAAI/bge-large-en-v1.5` | ✓ available |
| `jinaai/jina-embeddings-v2-base-code` | ✓ available (code medium) |
| `nomic-ai/nomic-embed-code` | ✗ NOT in fastembed ONNX — **code small tier skipped** |
| `Alibaba-NLP/gte-Qwen2-1.5B-instruct` | ✗ NOT in fastembed ONNX — **code large tier skipped** |

Code sweep will execute only 1 embedding model tier (jina-base 768d). Report will note that small/large code tiers were skipped and document the reason. See `embedding-models-research` wiki for details on fastembed ONNX model availability.

## Phased implementation

### Phase 1 — Foundation ✅ (current)

`pyproject.toml`, `bench/__init__.py`, `bench/i18n.py`, `bench/locales/{en,pt}.yaml`,
`bench/metrics.py`, `bench/golden/schema.py`, `bench/golden/__init__.py` (loader),
`bench/golden/dataset.yaml` (stub — 5 queries), `bench/tests/test_i18n.py`,
`bench/tests/test_metrics.py`

Gate: `uv run pytest bench/tests/test_i18n.py bench/tests/test_metrics.py` all green.

### Phase 2 — Golden dataset (20 queries)

Read actual `agent-engineering-toolkit` file structure, write all 20 golden queries with
verified `expected_files`. Replace the Phase 1 stub in `bench/golden/dataset.yaml`.

Gate: Each query has verified `expected_files`; spot-run 3 queries against toolkit to
confirm at least 1 config achieves p@5 > 0.

### Phase 3 — Judge plugins

`bench/judges/base.py`, `bench/judges/cross_encoder.py`, `bench/judges/claude.py`,
`bench/judges/openai.py`, `bench/judges/ollama.py`, `bench/judges/__init__.py`,
`bench/tests/test_judge_cross_encoder.py`

Gate: Cross-encoder judge produces monotonically higher score for literal query/chunk match
than random chunk.

### Phase 4 — Persistence + checkpoint

`bench/persistence.py`, `bench/checkpoint.py`, `bench/tests/test_resume.py`

Gate: `test_resume_skips_completed_units` passes (SIGKILL simulation); corpus-drift test
rejects without `--allow-corpus-drift`.

### Phase 5 — Target + corpus

`bench/target.py`, `bench/corpus.py`, `bench/templates/toolkit-rag.config.yaml.j2`

Gate: Subprocess call to toolkit `rag search` returns parseable JSON with at least 1 chunk
from a known query.

### Phase 6 — Config + sweep + synth + CLI

`bench/config.py`, `bench/sweep.py`, `bench/synth.py`, `bench/cli.py`, `bench/__main__.py`

Gate: `uv run python -m bench --help` shows all subcommands; `bench run --help` shows all
flags; smoke test against fixture completes in <60s.

### Phase 7 — Report renderer

`bench/report.py`, `bench/templates/report.md.j2`

Gate: `bench report <run-id>` generates `REPORT.md` with all required sections (TL;DR,
ranking, failure analysis, reproducibility); `--lang pt` renders section headings in
Portuguese.

### Phase 8 — First real run

Execute `bench run --target ~/Workspace/agent-engineering-toolkit` end-to-end.
Validate `reports/<date>-<hash>/REPORT.md` against REPORT.md acceptance criteria from spec.

## Critical file paths

| Phase | Files |
|---|---|
| 1 | `pyproject.toml`, `bench/{__init__,i18n,metrics}.py`, `bench/locales/*.yaml`, `bench/golden/{schema,__init__}.py`, `bench/tests/test_{i18n,metrics}.py` |
| 2 | `bench/golden/dataset.yaml` |
| 3 | `bench/judges/*.py`, `bench/tests/test_judge_cross_encoder.py` |
| 4 | `bench/{persistence,checkpoint}.py`, `bench/tests/test_resume.py` |
| 5 | `bench/{target,corpus}.py`, `bench/templates/toolkit-rag.config.yaml.j2` |
| 6 | `bench/{config,sweep,synth,cli}.py`, `bench/__main__.py` |
| 7 | `bench/report.py`, `bench/templates/report.md.j2` |
| 8 | First `reports/*/REPORT.md` |

## Patterns reused from agent-engineering-toolkit

- `rag/embedder.py` — fastembed wrapper pattern → `bench/judges/cross_encoder.py`
- `rag/cli.py:118-134` — argparse naming conventions → `bench/cli.py`
- `rag/config.py` — pyyaml + pydantic loading → `bench/config.py`
