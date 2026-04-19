# rag4you-cli

`rag4you-cli` is a fully-local, configurable RAG framework for codebases, documentation, and reference libraries. SP0 — the baseline benchmark harness — is now in active development.

<img align="center" src="/rag4you-header.png" alt="rag4you-cli header">

### Roadmap and Improvements

The work is organized into five sub-projects:

- [x] **SP0 (in progress)** — Benchmark the current toolkit RAG and publish the first reproducible report (`bench/` package)
- [ ] **SP1** — Build the configurable RAG core
- [ ] **SP2** — Publish the model catalog and decision matrix
- [ ] **SP3** — Build the `npx` wizard CLI
- [ ] **SP4** — Build the dynamic MCP server

Full plan: `docs/ROADMAP.md`. Benchmark spec: `docs/specs/sp0-baseline-bench.md`.

## 💻 Prerequisites

- **Python ≥ 3.11**
- **[uv](https://docs.astral.sh/uv/)** — package manager (install via `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Linux or macOS (WSL2 supported); Windows untested

Optional, for LLM-grade judging:
- `ANTHROPIC_API_KEY` — Claude API (Haiku default, cheapest option)
- `OPENAI_API_KEY` — OpenAI API (gpt-4o-mini default)
- [Ollama](https://ollama.ai/) — fully local LLM judge (pull `qwen2.5:7b-instruct`)

## 🚀 Installing rag4you CLI

```bash
git clone https://github.com/your-org/rag4you-cli
cd rag4you-cli
uv sync                   # installs all deps + bench package in dev mode
uv sync --extra all-judges  # also installs anthropic + openai + httpx
```

## ☕ Using rag4you CLI — bench (SP0)

Run the benchmark against an existing toolkit RAG:

```bash
# default: cross-encoder judge (zero cost, fully local)
uv run python -m bench run --target ~/Workspace/agent-engineering-toolkit

# with Claude Haiku judge (rigorous coverage scores, ~$0.20/run)
export ANTHROPIC_API_KEY=sk-...
uv run python -m bench run --target ~/path/to/rag-toolkit --judge claude

# resume an interrupted run
uv run python -m bench resume <run-id>

# check run progress
uv run python -m bench status

# re-render report from existing data
uv run python -m bench report <run-id>

# Portuguese CLI messages
uv run python -m bench run --target ~/path/to/rag-toolkit --lang pt
```

Report is written to `reports/<date>-<run-id>/REPORT.md`.

## Development setup

```bash
uv sync --group dev          # install dev deps (pytest, ruff)
uv run pytest                # run all tests
uv run ruff check bench/     # lint
uv run ruff format bench/    # format
```

**SP0 package layout:**

```
bench/
├── cli.py           # argparse: run | resume | status | report | retry-failed
├── config.py        # BenchConfig (Pydantic)
├── metrics.py       # pure functions: precision@k, MRR, coverage, token economy
├── i18n.py          # locale loader: t("dotted.key", **vars) → str
├── locales/
│   ├── en.yaml      # default locale
│   └── pt.yaml      # Portuguese
├── golden/
│   ├── schema.py    # GoldenQuery (Pydantic)
│   └── dataset.yaml # 20 hand-curated queries
├── judges/          # cross-encoder (default), claude, openai, ollama
├── checkpoint.py    # resume-safe state machine
├── persistence.py   # atomic JSONL + atomic JSON
├── target.py        # subprocess bridge to toolkit RAG
├── sweep.py         # (config × query × top_k) sweep orchestrator
└── report.py        # Jinja2 Markdown renderer
```

## 📫 Contributing to rag4you CLI

This project accepts contributions through GitHub pull requests. Follow the process in `CONTRIBUTING.md`. In short:

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Push the branch.
5. Open a pull request.

## 😄 Join the contributors

Want to contribute? Read [CONTRIBUTING.md](CONTRIBUTING.md).

## 📝 License

This project is licensed under the [MIT License](LICENSE).
