# Spec — SP0: Benchmark of Existing Toolkit RAG (rag4you-cli)

> **Note on scope:** The user's original request describes a much larger initiative (a fully configurable, pluggable, npx-distributable RAG framework with wizard CLI, decision matrices, MCP integration, and global/project scope). That initiative was decomposed into **5 sub-projects (SP0–SP4)** — see `docs/ROADMAP.md`. This document specs **only SP0** — the empirical baseline of the current RAG in `~/Workspace/agent-engineering-toolkit`. Each subsequent SP (SP1 core, SP2 docs, SP3 CLI wizard, SP4 MCP) will get its own brainstorm → spec → plan cycle.

## Context

The user wants to build a generic, configurable, fully-local RAG framework based on the architecture currently used in `~/Workspace/agent-engineering-toolkit`. Before re-architecting, the user explicitly requested a performance audit of the current implementation to verify that its stack and behavior are coherent and performant — bringing complete and solid information without fragmented or misleading results.

**Why this sub-project comes first:**
- Validates whether the current stack (SQLite + sqlite-vec + FTS5 + RRF, fastembed local models) is empirically good enough to be the foundation for SP1.
- Produces concrete numbers (precision@k, MRR, coverage, token economy) that inform SP1 defaults — chunk sizes, model tiers, top_k — instead of guessing.
- Builds a reusable benchmark harness that becomes the regression test suite for SP1+.
- Surfaces failure cases (queries where every config falls short) that need to be addressed in SP1.

**Intended outcome:**
1. A run of `bench run` against the toolkit produces a reproducible markdown report with a TL;DR, per-config ranking, failure analysis, and concrete recommendations for SP1 defaults.
2. A pluggable benchmark harness in `rag4you-cli/bench/` that supports four judging backends (cross-encoder default, Claude API, OpenAI API, Ollama local) and resumes safely after interruption.
3. The first piece of code in `rag4you-cli` — establishing the project's i18n infrastructure and code conventions for everything that follows.

---

## Scope

**In scope (SP0):**
- Custom Python harness in `rag4you-cli/bench/` that drives indexing and search of the existing toolkit RAG via subprocess.
- Hand-curated golden set of 20 queries + 50 LLM-generated synthetic queries.
- Sweep matrix: chunk size × embedding model (per collection) = ~18 reindex configurations; `top_k` swept at query time.
- Pluggable judge interface with four backends: cross-encoder (default, local), Claude API, OpenAI API, Ollama local.
- Checkpoint and resume system that survives interruption (SIGKILL, rate limit, network failure) and reuses cached judge responses.
- Markdown report (`REPORT.md`) with TL;DR, ranking, heatmaps, failure analysis, and SP1 recommendations.
- i18n infrastructure (en default, pt available) that all subsequent sub-projects must reuse.
- Locale parity rule (`.claude/rules/locale-parity.md`) enforcing equal evolution across locale files.
- Tests for the bench itself (metrics correctness, resume semantics, sanity check).

**Out of scope (handled by later SPs):**
- The new RAG core (SP1) — bench treats the toolkit RAG as a black box.
- Global vs project scope storage (SP1).
- npx-distributed wizard CLI (SP3).
- Decision matrix documentation across languages (SP2).
- MCP server with dynamic collections (SP4).
- Concurrency/throughput stress testing (single-user retrieval is the assumption).
- Any modification to `~/Workspace/agent-engineering-toolkit` source.

---

## Architecture & Components

### File layout

```
rag4you-cli/
├── bench/                          # new top-level package (SP0 deliverable)
│   ├── __init__.py
│   ├── __main__.py                 # entrypoint: uv run python -m bench
│   ├── cli.py                      # argparse: bench run | resume | status | report | retry-failed
│   ├── config.py                   # BenchConfig (pydantic): paths, sweep, judge, language
│   ├── target.py                   # RagTarget — wraps subprocess calls to toolkit RAG
│   ├── corpus.py                   # CorpusLoader — enumerates files in target & computes hashes
│   ├── golden/
│   │   ├── __init__.py
│   │   ├── schema.py               # GoldenQuery (pydantic)
│   │   └── dataset.yaml            # 20 hand-curated queries
│   ├── synth.py                    # synthetic query generator (chunk → query via judge LLM)
│   ├── sweep.py                    # SweepRunner — orchestrates configs × queries
│   ├── checkpoint.py               # state machine: manifest, progress, judge-cache, lock
│   ├── persistence.py              # atomic JSONL append (fsync per line) + atomic JSON rename
│   ├── judges/
│   │   ├── __init__.py             # registry: type_str -> Judge factory
│   │   ├── base.py                 # Judge ABC + JudgeScore
│   │   ├── cross_encoder.py        # CrossEncoderJudge — default, fastembed reranker
│   │   ├── claude.py               # ClaudeJudge — anthropic SDK, model param, retry
│   │   ├── openai.py               # OpenAIJudge — openai SDK, model param, retry
│   │   └── ollama.py               # OllamaJudge — HTTP /api/chat, model param, retry
│   ├── metrics.py                  # pure functions: precision@k, MRR, coverage, redundancy, ratios
│   ├── report.py                   # Markdown renderer (Jinja2) — locale-aware narrative sections
│   ├── i18n.py                     # locale loader: t("dotted.key", **vars) -> str
│   ├── locales/
│   │   ├── en.yaml                 # default
│   │   └── pt.yaml                 # initial second locale
│   └── tests/
│       ├── test_metrics.py
│       ├── test_judge_cross_encoder.py
│       ├── test_resume.py
│       ├── test_i18n.py            # parity check: every key in en.yaml exists in pt.yaml
│       └── fixtures/
├── reports/                        # bench outputs (gitignored except example/)
│   └── 2026-04-XX-toolkit-baseline-<hash>/
│       ├── REPORT.md
│       ├── summary.json
│       ├── raw.jsonl
│       ├── chunks-sample.md
│       └── manifest.json
├── .bench-state/                   # checkpoint state (gitignored)
│   └── <run-id>/
│       ├── manifest.json
│       ├── index-state.json
│       ├── progress.jsonl
│       ├── judge-cache.jsonl
│       ├── errors.jsonl
│       └── lock
├── .claude/
│   └── rules/
│       └── locale-parity.md        # NEW — paths: **/locales/*.{yaml,yml}
├── docs/
│   ├── ROADMAP.md                  # multi-SP overview (already exists)
│   └── specs/
│       └── sp0-baseline-bench.md   # this file
├── pyproject.toml                  # deps: pydantic, fastembed, jinja2, pyyaml, tiktoken, pytest
│                                   # extras: [claude]=anthropic, [openai]=openai, [ollama]=httpx,
│                                   #         [all-judges]=anthropic+openai+httpx
└── CLAUDE.md                       # already exists; add bench-specific guidance
```

### Component boundaries (each unit has one purpose, testable in isolation)

| Module | Purpose | Depends on | Tested via |
|---|---|---|---|
| `target.py` | Single bridge to toolkit RAG via subprocess. Translates BenchConfig sweep entries into temp `rag.config.yaml` files written to `.bench-state/<run-id>/configs/<config_id>.yaml`; runs `index` and `search` via `uv run --project <toolkit>/rag python -m rag -c <temp_config> ...`; parses stdout. | subprocess, pyyaml, jinja2 | mock toolkit responses |
| `corpus.py` | Enumerates target files, computes SHA-256 hashes for change detection. | hashlib, pathlib | fixture directory |
| `sweep.py` | Orchestrates the `(config × query × top_k) × judge` cartesian. Calls target, judges, persistence. Stateless — checkpoints externalize all state. | target, judges, checkpoint, persistence | mock target + mock judge |
| `judges/base.py` | `Judge` ABC; `JudgeScore` model; `score_relevance(q, chunk)` and `score_coverage(q, expected, chunks)`; `estimate_cost(...)`. | pydantic | contract tests on each impl |
| `judges/cross_encoder.py` | Default. fastembed reranker. Coverage = `mean(rerank[:k]) · length_factor`, marked `~approx`. Cost = 0. | fastembed | sanity: known query/chunk monotonic |
| `judges/claude.py` | Optional extra. anthropic SDK. Models: haiku-4-5 (default), sonnet-4-6, opus-4-7. Retries with exponential backoff on 5xx and rate-limit. | anthropic (extra) | mocked SDK responses |
| `judges/openai.py` | Optional extra. openai SDK. Models: gpt-4o-mini (default), gpt-4o. Retries. | openai (extra) | mocked SDK responses |
| `judges/ollama.py` | Optional extra. HTTP to `localhost:11434/api/chat`. Default `qwen2.5:7b-instruct`. Lower concurrency (2) — local LLMs degrade with parallelism. | httpx (extra) | mocked HTTP |
| `metrics.py` | Pure functions over result lists. No I/O. | numpy | golden expected vs computed |
| `checkpoint.py` | State machine for resume. Reads/writes manifest, progress, judge-cache, index-state. Acquires advisory lock. | fcntl, persistence | kill-9 simulation |
| `persistence.py` | Atomic JSONL append (write + fsync per line); atomic JSON write (tmp + rename). | os, json | crash injection |
| `report.py` | Reads progress + summary, renders REPORT.md. Locale-aware: section titles and narrative via `t()`; data tables in English. | jinja2, i18n | snapshot diff |
| `i18n.py` | `t(key, **vars)` loader. Caches parsed YAML. Precedence: `--lang flag > RAG4YOU_LANG env > config.lang > "en"`. | pyyaml | parity test, missing-key behavior |
| `cli.py` | Subcommands: `run`, `resume`, `status`, `report`, `retry-failed`. All user-facing strings via `t()`. | argparse, sweep, checkpoint, report, i18n | end-to-end smoke against fixture target |

**Why subprocess (not import)** for `target.py`: the toolkit RAG lives in a separate venv; subprocess isolates it and mirrors how a real user (or future SP1 testing the toolkit RAG as a baseline comparison) consumes the system. It also makes the bench naturally extensible to non-Python RAG implementations later.

---

## Golden Set & Sweep Matrix

### Golden set — 20 hand-curated queries

Each query in `bench/golden/dataset.yaml`:

```yaml
- id: docs-001
  collection: docs              # docs | code | all
  query: "what is the difference between skills and plugins?"
  query_kind: conceptual         # conceptual | navigational | factual | procedural | failure
  difficulty: medium             # easy | medium | hard
  length: short                  # short | long
  expected_files:                # files that MUST appear in top-K
    - "docs/skills.md"
    - "docs/plugins.md"
  expected_answer: |             # canonical ground-truth answer
    Skills are reusable capability units...
  must_contain:                  # tokens/phrases that must appear in returned chunks
    - "skill"
    - "plugin"
  tags: [knowledge-lookup, ambiguous-target]
```

**Distribution (20 queries):**

| Category | N | Example coverage |
|---|---|---|
| docs — conceptual | 5 | "how does attention budget work?", "what is progressive disclosure?" |
| docs — navigational/factual | 3 | "what is the PostToolUse hook token limit?", "where is RRF documented?" |
| code — find symbol | 4 | "function that computes SHA-256 of a file", "where is sqlite-vec registered?" |
| code — how does X work | 4 | "how does the tree-sitter chunker fall back?", "SQL trigger that syncs FTS" |
| cross-collection (`search_all`) | 2 | queries where docs AND code are relevant |
| failure cases | 2 | irrelevant queries that should return little/nothing with low confidence |

**Note:** Queries are stored in English in the golden set (codebase convention). The bench narrative report renders them in the user's locale by quoting them as-is (queries themselves are not translated).

### Synthetic queries — 50 generated

`synth.py` walks the corpus chunks; for every Nth chunk asks the judge LLM (or a separate generator LLM if cross-encoder is the judge) to produce a natural query that the chunk would answer. Self-validation: the source chunk must appear in the top-10 retrieval; if not, the synthetic query is dropped (likely a noisy chunk or generator hallucination).

**Generator backend:** synthetic-query generation always needs an LLM (cross-encoders cannot generate). Resolution order:
1. If active judge is an LLM (claude/openai/ollama): reuse it for generation.
2. Else if Ollama is reachable on `localhost:11434` AND `qwen2.5:7b-instruct` (or fallback `llama3.1:8b`) is pulled: use it just for generation, keeping cross-encoder as judge.
3. Else: skip synth generation, run only the 20 golden queries, emit a clear warning in `REPORT.md` "Synthetic queries skipped — install Ollama and pull qwen2.5:7b-instruct, or pick an LLM judge, to enable the 50-query synth set."

This keeps the default zero-config flow honest about its limitations.

### Sweep matrix

| Axis | Values | Rationale |
|---|---|---|
| **chunk size (docs)** | 256, **512** (current), 1024 tokens | Test if smaller or larger improves coverage/redundancy. Overlap fixed at 50% of max. |
| **chunk size (code)** | 1000, **1500** (current), 2500 chars | Same logic. |
| **embedding model (docs)** | small **`BAAI/bge-small-en-v1.5`** (384d, current) / medium `BAAI/bge-base-en-v1.5` (768d) / large `BAAI/bge-large-en-v1.5` (1024d) | Same family for fair comparison; covers SP2's planned tiers. |
| **embedding model (code)** | small `nomic-ai/nomic-embed-code` (137M, ~256d) / medium **`jinaai/jina-embeddings-v2-base-code`** (768d, current) / large `Alibaba-NLP/gte-Qwen2-1.5B-instruct` (1536d) | Validate fastembed availability before committing models; mark `skipped` in report if any tier has no local candidate. |

**Total reindex configs:** `3 chunks × 3 models = 9 per collection × 2 collections = 18 reindexations`.

**`top_k` / `rrf_k`** (query-time params, no reindex needed): swept across `top_k ∈ {3, 5, 10}` with `rrf_k=60` fixed; applied to the same retrieved candidate sets (`vector_candidates=20` fixed). Free in compute.

**Estimated cost:**
- Indexing: 18 × ~30s ≈ 10 min
- Retrieval: 70 queries × 18 configs × 3 top_k = 3780 retrievals (~1s each) ≈ 1 hour
- Judging: 3780 × judge call → cross-encoder ~10 min (local CPU); Claude Haiku ~10 min ($~0.20); Sonnet ~30 min ($~1.00); Ollama 7b ~1–2 hours

**Diagnostic captured per query (free):** breakdown of which sub-search (vector / FTS / RRF) contributed each top-K chunk → contributor analysis in the report.

---

## Pipeline, Checkpoint & Resume

### End-to-end pipeline

```
1. Init run    → cli.py:run creates .bench-state/<run-id>/, writes manifest.json
2. Snapshot    → manifest captures: corpus file hashes, sweep matrix expanded,
                  judge config, toolkit RAG git SHA, bench version, planned work units
3. Sweep loop  → for each config (chunk × model × collection):
   3a. Check index-state.json — is this config already materialized in toolkit's .rag/?
   3b. If not: generate temp rag.config.yaml, run `rag index` via subprocess,
        atomically update index-state.json
   3c. For each query (golden + synth):
       - progress.jsonl: is this work unit (config_hash, query_id, top_k) already done?
       - If yes: skip
       - If no: run `rag search`, capture chunks, write `phase=retrieved` row
   3d. For each (config, query) retrieved without judgment:
       - judge-cache.jsonl: has (judge_id, query_id, chunks_hash) been judged?
       - If yes: reuse cached score (no API call)
       - If no: call judge, write to judge-cache, write `phase=judged` to progress
4. Aggregate   → metrics.py reads complete progress.jsonl, computes per-config metrics
5. Report      → report.py renders REPORT.md with locale-aware narrative
```

### `.bench-state/<run-id>/` layout

```
.bench-state/2026-04-18-toolkit-baseline-a3f9/
├── manifest.json              # run config + work plan (immutable after init)
├── index-state.json           # which rag.config is materialized in toolkit/rag/.rag/
├── progress.jsonl             # append-only: 1 line per work unit completed
├── judge-cache.jsonl          # append-only: raw judge responses (reusable across resumes)
├── errors.jsonl               # append-only: failures with retry context
└── lock                       # advisory file lock (prevents concurrent runs)
```

### Schemas

**`manifest.json`** (full context needed to resume):
```json
{
  "run_id": "2026-04-18-toolkit-baseline-a3f9",
  "created_at": "2026-04-18T18:00:00Z",
  "bench_version": "0.1.0",
  "rag_target": {
    "path": "/home/rodrigo/Workspace/agent-engineering-toolkit",
    "git_sha": "df448f0...",
    "uv_lock_hash": "..."
  },
  "corpus": {
    "files": [{"path": "docs/skills.md", "sha256": "..."}, ...],
    "total_files": 247
  },
  "judge": {"type": "cross-encoder", "model": "BAAI/bge-reranker-v2-m3"},
  "sweep": [
    {"config_id": "docs-c512-bge-small", "collection": "docs", "chunk": 512,
     "model": "BAAI/bge-small-en-v1.5"},
    ...
  ],
  "golden_set_path": "bench/golden/dataset.yaml",
  "synth_seed": 42,
  "work_units_total": 3780,
  "work_units_breakdown": {"retrievals": 1260, "judgments": 3780},
  "lang": "en"
}
```

**`progress.jsonl`** (append-only, one line per phase completion):
```json
{"ts":"...", "config_id":"docs-c512-bge-small", "query_id":"docs-001",
 "top_k":5, "phase":"retrieved", "chunks":[{"file":"...", "score":..., "source":"vector|fts|rrf"}]}
{"ts":"...", "config_id":"docs-c512-bge-small", "query_id":"docs-001",
 "top_k":5, "phase":"judged", "score":0.82, "judge_call_id":"jc-..."}
```

**`judge-cache.jsonl`** (reuses across resumes — never re-pays API):
```json
{"judge_call_id":"jc-...", "judge":"claude:claude-haiku-4-5",
 "query_id":"docs-001", "chunks_hash":"sha256:...",
 "request":{...}, "response":{...}, "score":0.82, "rationale":"..."}
```

### Resume semantics

`bench resume <run-id>` (or `bench run --resume`):
1. Reads `manifest.json`; validates `bench_version` compat and corpus hash. If corpus drift, aborts unless `--allow-corpus-drift`.
2. Reads `progress.jsonl` → builds set of completed `(config_id, query_id, top_k, phase)` tuples.
3. Reads `judge-cache.jsonl` → builds reusable score cache.
4. Reads `index-state.json` → knows which config is currently materialized.
5. Continues the pipeline from step 3 normally.

### Atomicity & guarantees

- **Append-only JSONL with `os.fsync` per line** — POSIX guarantee that the byte hit disk before the next work unit starts. No corruption on SIGKILL.
- **`index-state.json` written via `tmp + rename`** — never partial.
- **`lock` file via `fcntl.flock(LOCK_EX | LOCK_NB)`** — second concurrent invocation fails fast with a clear message.
- **Work unit idempotency:** rerunning a completed work unit yields the same result (judge `temperature=0.0`, deterministic embeddings, deterministic top_k).

### Failure handling

- **API 5xx or rate limit:** exponential retry (3 attempts: 1s, 4s, 16s). After exhaustion: write to `errors.jsonl` with context, mark work unit `failed`, continue with other units.
- **Toolkit RAG crash during indexing:** `index-state.json` not updated → next resume reindexes that config. Cleans `.rag/` of toolkit before retry.
- **Corpus changed between sessions:** `manifest.json` rejects resume; user decides.
- **Judge cache miss after corpus change:** affected entries invalidated automatically.

### CLI commands

```bash
bench run --target ~/Workspace/agent-engineering-toolkit
                # default: --judge cross-encoder (zero setup, zero cost, all-local)
bench run --judge claude --judge.model claude-haiku-4-5  # opt into LLM-grade judge
bench run --judge openai --judge.model gpt-4o-mini
bench run --judge ollama --judge.model qwen2.5:7b-instruct
bench run --lang pt                                       # CLI messages in Portuguese
bench run --yes                                           # CI mode: skip cost confirmation prompt
bench resume 2026-04-18-toolkit-baseline-a3f9
bench status [run-id]
bench report [run-id]                                     # re-render REPORT.md from progress
bench retry-failed [run-id]
```

---

## Judge — Interface, Plugins & Tradeoffs

### Interface (ABC)

```python
# bench/judges/base.py
class JudgeScore(BaseModel):
    score: float                      # normalized 0–1
    rationale: str | None             # text (LLMs fill; cross-encoder = None)
    raw: dict                         # raw backend response (cached)
    approx: bool                      # True for cross-encoder coverage fallback

class Judge(ABC):
    name: str                         # e.g. "cross-encoder:bge-reranker-v2-m3"
    backend: str                      # "cross-encoder" | "claude" | "openai" | "ollama"

    @abstractmethod
    def score_relevance(self, query: str, chunk: str) -> JudgeScore: ...
    """Per-chunk relevance. Always available. Backbone for precision@k / MRR."""

    @abstractmethod
    def score_coverage(self, query: str, expected_answer: str,
                       chunks: list[str]) -> JudgeScore: ...
    """Does the top-K set cover the expected answer? LLMs evaluate the set holistically;
    cross-encoder uses fallback (mean of weighted relevances) and sets approx=True."""

    def estimate_cost(self, n_relevance_calls: int, n_coverage_calls: int) -> float:
        """For pre-run warning. Cross-encoder = 0.0."""
```

### Plugin matrix

| Judge | Backend | Coverage score | Cost | Setup | When to use |
|---|---|---|---|---|---|
| **`cross-encoder` (default)** | `BAAI/bge-reranker-v2-m3` (568M) via fastembed | **Approximate** (weighted mean of per-chunk relevance) | $0 | Zero — model auto-downloads on first use (~1.5GB cache) | Default. Honors "100% local" project principle. Sufficient for baseline and ongoing regression tests (SP1+). |
| **`claude`** (extra) | Anthropic API; default `claude-haiku-4-5` | **Rigorous** (evaluates set holistically) | ~$0.10–0.50 per full run (Haiku); ~$1–3 (Sonnet) | `ANTHROPIC_API_KEY` env var | Pro/Max plan users wanting LLM-grade rigor without GPU. Recommended for final validation before SP1 commitment. **Default Claude model is Haiku-4-5 to respect Pro plan rate limits.** |
| **`openai`** (extra) | OpenAI API; default `gpt-4o-mini` | **Rigorous** | ~$0.15 (4o-mini); ~$2 (gpt-4o) | `OPENAI_API_KEY` env var | Users with OpenAI credits or for cross-vendor sanity check (Claude vs GPT). |
| **`ollama`** (extra) | HTTP to `http://localhost:11434/api/chat`; default `qwen2.5:7b-instruct` | **Rigorous** | $0 | Ollama installed + `ollama pull qwen2.5:7b-instruct` | Users wanting LLM-grade rigor 100% offline. Tradeoff: GPU/RAM (~8GB for 7b, ~20GB for 14b) and 5–20× slower than API. **`max_concurrent: 2`** by default — local LLMs degrade with high parallelism. |

### Cross-encoder coverage fallback (transparency)

```
coverage_approx = mean(rerank_scores[top-K]) * length_factor
```
where `length_factor` softly penalizes very-short and very-long chunk sets. Reports mark these scores with badge `~approx` and include a **"Limitations of this run"** section explaining that exact coverage requires an LLM judge.

**Recommended workflow:** first SP0 run with cross-encoder (fast, local, zero setup). If results are ambiguous or counter-intuitive, second run with Claude Haiku for tie-breaking. Resume reuses indexing and per-chunk relevance cache; only `score_coverage` calls the new judge.

### Pre-run cost/time estimate (CLI)

```
$ bench run --judge claude --judge.model claude-haiku-4-5
[bench] Run plan: 18 configs × 70 queries × 3 top_k = 3780 retrievals
[bench] Judge: claude (claude-haiku-4-5)
[bench] Estimated cost: ~$0.18 (4500 calls × ~150 tokens avg)
[bench] Estimated time: ~12 min (5 concurrent)
[bench] Continue? [Y/n]
```

For cross-encoder: prompt skipped ($0). `--yes` flag bypasses prompt for CI.

### Config schema

```yaml
# bench/config.yaml (generated by `bench init`)
lang: en                           # en | pt | (future)

judge:
  type: cross-encoder              # cross-encoder | claude | openai | ollama
  cross-encoder:
    model: BAAI/bge-reranker-v2-m3
    device: cpu                    # cpu | cuda | auto
  claude:
    model: claude-haiku-4-5        # claude-haiku-4-5 | claude-sonnet-4-6 | claude-opus-4-7
    api_key_env: ANTHROPIC_API_KEY
    max_concurrent: 5
  openai:
    model: gpt-4o-mini
    api_key_env: OPENAI_API_KEY
    max_concurrent: 5
  ollama:
    base_url: http://localhost:11434
    model: qwen2.5:7b-instruct
    max_concurrent: 2

target:
  path: ~/Workspace/agent-engineering-toolkit
  rag_config_template: bench/templates/toolkit-rag.config.yaml.j2

sweep:
  collections: [docs, code]
  chunk_sizes:
    docs: [256, 512, 1024]
    code: [1000, 1500, 2500]
  models:
    docs: [small, medium, large]   # resolved via models.yaml
    code: [small, medium, large]
  top_k: [3, 5, 10]

scoring:
  composite_weights:               # configurable; rerank without rerunning
    coverage: 0.5
    token_to_coverage_ratio: 0.3
    precision_at_5: 0.2
  self_sufficiency_threshold: 0.8  # coverage threshold for self-sufficiency rate
```

---

## Metrics, Scoring & Output

### Metric definitions

**Retrieval (judge-independent):**

| Metric | Formula | Notes |
|---|---|---|
| **Precision@k** | `\|relevant ∩ retrieved[:k]\| / k` | "relevant" = file is in golden's `expected_files`; for synthetics: source-chunk file. |
| **Recall@k** | `\|relevant ∩ retrieved[:k]\| / \|relevant\|` | |
| **MRR** | `mean(1 / rank_first_relevant)` | `0` if no relevant in top-K. |
| **Hit rate@k** | `% of queries with ≥1 relevant in top-K` | Sanity gate: <50% indicates collapse. |

**Token economy:**

| Metric | Formula |
|---|---|
| **Raw tokens per query** | `sum(token_count(chunk) for chunk in retrieved[:k])` — uses `tiktoken` (cl100k) as a single reference, independent of the embedding model. |
| **Coverage score** | LLM judge: 0–1 normalized of "do top-K cover `expected_answer`?". Cross-encoder: `mean(rerank[:k]) · length_factor`, marked `approx=True`. |
| **Redundancy** | `mean(cosine(chunk_i, chunk_j))` over all pairs in top-K. Embeddings computed once with `bge-small` (independent of the config's model for comparability). |
| **Token-to-coverage ratio** | `coverage / log(1 + tokens)` — log to avoid over-penalizing larger configs. |
| **Self-sufficiency rate** | `% of queries with coverage ≥ threshold at top_k=5` (threshold per judge type, default 0.8). |

**Operational:**

| Metric | How measured |
|---|---|
| Indexing time (full) | Wall clock between `rag index` start/end. |
| Query latency p50/p95 | Wall clock per `rag search`, aggregated per config. |
| Peak RSS | `resource.getrusage` during subprocess (Linux/macOS). |
| DB size | `os.path.getsize(.rag/knowledge.db)` post-indexing. |
| Model cache size | `du -s .rag/models/<model>`. |

### Aggregation

```
work unit (config, query, top_k)
  → per-config bucket (mean / median / p25 / p75 of each metric across queries)
  → global ranking (composite: 0.5·coverage + 0.3·token_to_coverage_ratio + 0.2·precision@5)
  → per-collection sub-rankings (docs and code have different natures)
```

**Composite weights are configurable** — the user can rerank without rerunning the sweep (re-aggregation reads `progress.jsonl`).

### Run outputs

```
reports/2026-04-XX-<run-id>/
├── REPORT.md           # human-readable, locale-aware narrative
├── summary.json        # structured aggregates (consumed by SP1 specs)
├── raw.jsonl           # all work units (without full chunk text — too large)
├── chunks-sample.md    # curated examples: top-3 and bottom-3 results per config
└── manifest.json       # copy of .bench-state/<run-id>/manifest.json
```

### `REPORT.md` structure (en locale shown; pt locale renders equivalent text)

```markdown
# RAG Baseline Report — toolkit (run 2026-04-18-a3f9)

## TL;DR
- Composite winner (docs): chunk=512, model=bge-base ✓ matches current, with caveat
- Composite winner (code): chunk=1500, model=jina-base ✓ matches current
- Self-sufficiency rate: 64% (queries where top-5 already suffices)
- ⚠️ 23% of queries: no relevant chunk in top-5 → investigate

## Recommendations for SP1 defaults
- Default chunk for docs: 512 (✓ keep)
- Default chunk for code: 1500 (✓ keep)
- Tier "small" docs: bge-small (current) — best cost/coverage ratio
- Tier "medium" docs: bge-base (+5pp coverage, 2× model weight, 1.4× latency)
- Tier "large" docs: bge-large (+2pp coverage, 4× weight) — overkill for small corpora
- ...

## Configs ranking (composite)
| Rank | Collection | Chunk | Model | Coverage | Tokens/q | Ratio | P@5 | Latency p50 |
|------|------------|-------|-------|----------|----------|-------|-----|-------------|
| 1    | docs       | 512   | bge-base | 0.78  | 1840     | 1.04  | 0.71| 142ms       |
| ...  |            |       |       |          |          |       |     |             |

## Heatmaps (chunk × model) — coverage score
[ASCII grid in Markdown; optional PNG link if matplotlib extra installed]

## Failure analysis
Queries where every config failed (coverage < 0.4):
- `docs-008`: "how does the reindex lock work?" — relevant chunk exists in
  `.claude/hooks/check-rag-reindex.sh:45` but the hook is not indexed by current toolkit config.
  → Recommendation: include `.claude/hooks/` in toolkit's docs collection.

## Per-collection details
### docs
[detailed tables]
### code
[detailed tables]

## Limitations of this run
- Judge: cross-encoder (`bge-reranker-v2-m3`). Coverage scores marked `~approx`.
- Corpus: agent-engineering-toolkit (247 files, ~2.3MB). Does not test scale.
- Not measured: concurrency, cold-start, FTS-only vs vector-only ablation.

## Reproducibility
- Bench version: 0.1.0
- Toolkit git SHA: df448f0
- Run command: `bench run --target ~/Workspace/agent-engineering-toolkit --judge cross-encoder`
- Resume: `bench resume 2026-04-18-a3f9`
```

### Reproducibility

- **Seeds:** `synth.py` uses `random.seed(manifest.synth_seed)`. Deterministic.
- **LLM temperature:** `0.0` always (Haiku/Sonnet/GPT/Ollama). Cross-encoder is natively deterministic.
- **Pinned models:** exact versions in `manifest.json`; `pyproject.toml` uses `~=` not `>=`.
- **Single tokenizer:** `tiktoken` cl100k for token counting — independent of any embedding model's tokenizer; enables fair cross-config comparison.
- **Run identity:** `run_id = "<YYYY-MM-DD>-<slug>-<sha1(manifest)[:4]>"`. Same config + same corpus + same bench version → same hash suffix → refuses overwrite unless `--force-new` (which appends `-r2`, `-r3` to the slug).

### Bench self-validation (tests)

```python
# bench/tests/test_metrics.py
def test_precision_at_k_perfect():
    """Golden has 1 expected_file at retrieved[0] → P@1 = 1.0."""

def test_mrr_no_relevant():
    """No relevant in top-K → MRR = 0.0."""

def test_redundancy_identical_chunks():
    """3 identical chunks → redundancy = 1.0."""

# bench/tests/test_judge_cross_encoder.py
def test_relevance_monotonic():
    """A chunk containing the literal query scores higher than a random chunk."""

# bench/tests/test_resume.py
def test_resume_skips_completed_units():
    """After SIGKILL mid-run, resume processes only pending units."""

def test_resume_corpus_drift_aborts():
    """If corpus changed, resume rejects without --allow-corpus-drift."""

# bench/tests/test_i18n.py
def test_locale_parity():
    """Every key in en.yaml exists in pt.yaml (and vice versa). Fails CI on drift."""

def test_missing_key_fallback():
    """t('missing.key') returns the key string + warning, never raises."""
```

**Mandatory pre-run sanity check:** the bench injects 1 trivial query whose relevant chunk is obviously identifiable (e.g., query = first literal paragraph of a README). If no config returns that chunk in top-3 → bench aborts with: "RAG or bench broken, we are not measuring anything useful."

---

## i18n Infrastructure (Cross-Cutting)

### Required convention (project-wide, applies to SP0–SP4)

- **All code, comments, identifiers, docstrings, design docs, commit messages, schemas, config keys: English only.**
- **Only CLI user-facing strings get i18n via external locale files** (`bench/locales/<lang>.yaml`).
- Default language: `en`. Initial languages shipped: `en` + `pt`.
- Selection precedence: `--lang <code>` flag > `RAG4YOU_LANG` env var > `config.lang` > `"en"`.

### Locale file shape (example, en.yaml)

```yaml
cli:
  run:
    starting: "Starting bench run {run_id}..."
    cost_estimate: "Estimated cost: ~${cost} ({n_calls} calls × ~{avg_tokens} tokens avg)"
    cost_confirm: "Continue? [Y/n]"
    aborted: "Run aborted by user."
  resume:
    found_units: "Resuming run {run_id}: {done}/{total} work units already complete."
    corpus_drift: "Corpus has changed since the run was created. Use --allow-corpus-drift to override."
  status:
    running: "Run {run_id}: {done}/{total} ({pct}%) — judge={judge}"
errors:
  judge_api_failed: "Judge call failed after {attempts} attempts: {error}"
  index_failed: "Indexing config {config_id} failed: {error}"
report:
  tldr_heading: "TL;DR"
  recommendations_heading: "Recommendations for SP1 defaults"
  failure_analysis_heading: "Failure analysis"
  limitations_heading: "Limitations of this run"
```

### Loader (`bench/i18n.py`)

```python
# Pseudocode signature
def t(key: str, **vars) -> str:
    """Resolve a dotted key against the active locale; interpolate vars."""

def set_locale(code: str) -> None: ...
def get_active_locale() -> str: ...
```

Behavior:
- Cache parsed YAML in memory.
- Missing key → return the key string verbatim + emit a warning (never raise).
- Active locale resolved once at CLI startup from precedence chain.

### Locale parity rule (project artifact, must be created)

`.claude/rules/locale-parity.md`:
```markdown
---
description: Enforce equal evolution across all locale files. When any locale file changes, all sibling locales in the same directory must be updated with the equivalent change in their language.
paths:
  - "**/locales/*.yaml"
  - "**/locales/*.yml"
  - "**/locales/*.json"
---

When you modify a locale file (add/remove/rename a key, or change a string's meaning):

1. **Identify all sibling locale files** in the same `locales/` directory.
2. **Apply the equivalent change in each sibling** — the same key path, semantically equivalent translation in that locale's language.
3. **Same commit, same change set** — never leave the project in a state where one locale has a key that another does not.
4. **For pure typo fixes** in a single locale that don't change meaning: still consider whether other locales have the same typo pattern.
5. **For new features that introduce many strings:** add all keys to the default `en.yaml` first, then mirror to every existing locale before merging.

The bench has a `test_locale_parity` test that fails CI if any key exists in one locale but not another. Run it after every locale change.
```

---

## Critical Files & Reused Patterns

### Files to create (SP0)

All under `~/Workspace/rag4you-cli/`:
- `bench/__init__.py`, `bench/__main__.py`, `bench/cli.py`, `bench/config.py`, `bench/target.py`, `bench/corpus.py`, `bench/synth.py`, `bench/sweep.py`, `bench/checkpoint.py`, `bench/persistence.py`, `bench/metrics.py`, `bench/report.py`, `bench/i18n.py`
- `bench/golden/__init__.py`, `bench/golden/schema.py`, `bench/golden/dataset.yaml`
- `bench/judges/__init__.py`, `bench/judges/base.py`, `bench/judges/cross_encoder.py`, `bench/judges/claude.py`, `bench/judges/openai.py`, `bench/judges/ollama.py`
- `bench/locales/en.yaml`, `bench/locales/pt.yaml`
- `bench/tests/test_metrics.py`, `bench/tests/test_judge_cross_encoder.py`, `bench/tests/test_resume.py`, `bench/tests/test_i18n.py`
- `bench/templates/toolkit-rag.config.yaml.j2` (Jinja2 template for sweep configs)
- `pyproject.toml`: deps `pydantic`, `pyyaml`, `fastembed`, `tiktoken`, `jinja2`, `numpy` (explicit even though transitive), `pytest`; extras `[claude]=anthropic`, `[openai]=openai`, `[ollama]=httpx`, `[all-judges]=anthropic+openai+httpx`. Registers script `bench = "bench.cli:main"` so users can run `bench ...` after `uv sync` (alternatively `uv run python -m bench ...`).
- `.claude/rules/locale-parity.md`
- `.gitignore` updates: `.bench-state/`, `reports/` except `reports/example/`

### Files to read for patterns (informational, not modified)

- `~/Workspace/agent-engineering-toolkit/rag/cli.py:118-134` — current CLI argparse pattern (we mirror naming conventions).
- `~/Workspace/agent-engineering-toolkit/rag/config.py` — current YAML config loading (we follow the same pyyaml + dataclasses approach for our `BenchConfig`, though using pydantic for validation).
- `~/Workspace/agent-engineering-toolkit/rag/index.py:79` — reading-order loader (informs how we handle template-driven config generation).
- `~/Workspace/agent-engineering-toolkit/rag/embedder.py` — fastembed wrapper pattern (useful for `cross_encoder.py` judge).
- `~/Workspace/agent-engineering-toolkit/.mcp.json` — MCP server invocation format (relevant for SP4, informational here).

### External libs / patterns reused

- `fastembed` — already used by toolkit; reuse for both cross-encoder reranker and the bge-small embedding helper used in redundancy calculation.
- `tiktoken` — chosen over toolkit's naive `text.split()` token estimate to provide a stable, model-agnostic counter.
- `pydantic` v2 — for `BenchConfig`, `GoldenQuery`, `JudgeScore` schemas.
- `jinja2` — for both report templating and `rag.config.yaml` template generation per sweep entry.
- `pytest` — testing. (`pytest-asyncio` only added if implementation chooses async over thread-pool concurrency for API judges.)
- Anthropic / OpenAI / httpx SDKs — installed only via extras; absent extras means absent judges in the registry, with a clear error if user selects an unavailable judge.

---

## Verification

How to confirm the SP0 deliverable end-to-end:

1. **Install and smoke test:**
   ```bash
   cd ~/Workspace/rag4you-cli
   uv sync
   uv run pytest bench/                                       # all green
   uv run python -m bench --help                              # shows commands in en
   uv run python -m bench --lang pt --help                    # shows commands in pt
   ```

2. **Locale parity check (CI-like):**
   ```bash
   uv run pytest bench/tests/test_i18n.py -v                  # parity test passes
   ```

3. **Default run (cross-encoder, zero-config):**
   ```bash
   uv run python -m bench run --target ~/Workspace/agent-engineering-toolkit
   # expected: ~30 min total; reports/<date>-<hash>/REPORT.md generated
   ```

4. **Resume after interrupt:**
   ```bash
   uv run python -m bench run --target ~/Workspace/agent-engineering-toolkit &
   sleep 60 && kill -9 %1
   uv run python -m bench resume <run-id>
   # expected: continues from last completed work unit, no duplicate API calls
   ```

5. **LLM judge run (Claude Haiku):**
   ```bash
   export ANTHROPIC_API_KEY=...
   uv add --optional claude
   uv run python -m bench run --judge claude --judge.model claude-haiku-4-5 \
                              --target ~/Workspace/agent-engineering-toolkit
   # expected: cost confirmation prompt; ~12 min runtime; new REPORT.md with rigorous coverage scores
   ```

6. **Sanity check fires when broken:**
   ```bash
   # Manually point bench at an empty corpus to verify the trivial-query sanity check aborts
   uv run python -m bench run --target /tmp/empty-target
   # expected: aborts with "RAG or bench broken, we are not measuring anything useful."
   ```

7. **REPORT.md acceptance criteria:**
   - TL;DR has 4 bullet points (winner per collection, self-sufficiency rate, alert on failure rate)
   - Configs ranking table is sorted by composite score
   - "Recommendations for SP1 defaults" section has at minimum: chunk size per collection, model per tier per collection
   - Failure analysis lists at least the configs/queries with coverage < 0.4
   - Reproducibility section has a runnable command

8. **Hand-off to SP1:** `summary.json` is the contract — SP1's brainstorming spec should consume this file to ground its model-tier defaults and chunk-size choices.

---

## Out of Scope Explicit (Reaffirmation)

- Modifying any code in `~/Workspace/agent-engineering-toolkit`.
- Building the new RAG core (SP1).
- Building the npx CLI wizard (SP3).
- MCP server changes (SP4).
- Decision matrix documentation polish across many languages (SP2).
- Concurrency/throughput stress tests.
- Comparison against external RAG products (LangChain, LlamaIndex retrievers, Vertex AI Search).
- GPU-accelerated indexing or quantized model variants.
