# Copilot instructions for rag4you-cli

## Current repository state

- This repository is still spec-first. `README.md` and `docs/ROADMAP.md` are the source of truth for status, and only SP0 has a drafted spec in `docs/specs/sp0-baseline-bench.md`.
- Treat package names such as `bench/`, `rag4you/`, and `rag4you/mcp/` as planned surfaces until implementation lands. Do not assume runtime code or tooling already exists.
- This repository keeps two instruction surfaces in sync: Claude Code uses `CLAUDE.md` and `.claude/rules/`, and GitHub Copilot uses `.github/copilot-instructions.md` and `.github/instructions/`.

## Build, test, and lint

- No runnable build, test, or lint configuration exists in the current repository state.
- `CLAUDE.md` defines the intended Python toolchain once implementation starts:
  - `uv run pytest`
  - `uv run pytest path/to/test.py::test_name`
  - `uv run ruff check . && uv run ruff format .`
- Use `uv add` and `uv run` for Python work. Do not use bare `pip install`.

## High-level architecture

- The project is delivered in five sub-projects. `docs/ROADMAP.md` defines the sequence: SP0 benchmark harness, SP1 configurable `rag4you/` core, SP2 model guidance docs, SP3 `npx` CLI wrapper, and SP4 dynamic MCP server.
- SP0 is the first executable surface. Its spec defines a `bench/` Python package that benchmarks the existing toolkit RAG via subprocess, produces a markdown `REPORT.md`, writes checkpoint state under `.bench-state/`, writes run outputs under `reports/`, and establishes the i18n and code conventions reused by later SPs.
- The docs workflow is part of the architecture. Each sub-project gets its own spec at `docs/specs/<sp-id>-<topic>.md`, and any implementation plan lives next to that spec as `-plan.md`.

## Key conventions

- Update `docs/ROADMAP.md` when a sub-project's status, scope, or delivered artifacts change.
- If you update `CLAUDE.md`, `.claude/rules/`, `.github/copilot-instructions.md`, or `.github/instructions/`, mirror the equivalent change across the other instruction surface in the same task.
- Use the `wiki` to guide you throught documentations and project specifications.
- Before implementing a feature, consult `wiki/knowledge/index.md` for relevant research pages. When implementation changes invalidate wiki content, update the affected knowledge pages in the same task.
- Keep code, comments, docstrings, schemas, config keys, documentation, and commit messages in English. Only CLI user-facing strings belong in locale files.
- Keep sibling locale files in lockstep. A locale change must update the same keys, placeholders, and pluralization structure across all sibling locale files in the same change set.
- When Python code lands, follow the repo's Python rule set: keep runtime knobs configurable, keep CLI strings in locale files, target at least 90% coverage for edited Python areas, and use atomic writes or append-only updates for checkpoint and persistence flows.
- Verify hardcoded paths before relying on them. This repository already records wrong paths as a recurring failure mode.
- Before creating a new project artifact, check whether an existing one can be extended instead.
- Keep spec and plan files inside the repository. Do not move project plans to out-of-tree locations such as `~/.claude/plans/`.
- When updating `README.md`, follow `docs/templates/readme-template.md`.
- Mirror repository-wide guidance in `.github/copilot-instructions.md` and mirror path-specific guidance in `.github/instructions/*.instructions.md`.
- If you add assistant artifacts, create new skills through `superpowers:writing-skills` and create other artifacts through the agent-customizer workflows already used by this repo.
