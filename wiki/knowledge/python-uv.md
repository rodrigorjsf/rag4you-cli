# Python uv Package Manager

**Summary**: uv is an extremely fast Python package and project manager written in Rust (by Astral, makers of [[ruff-linter]]). It replaces pip, pip-tools, pipx, poetry, pyenv, virtualenv, and more. The rag4you-cli project mandates `uv add` and `uv run` for all Python work.
**Sources**: `docs/references/toolchain/bibliography.md`, <https://docs.astral.sh/uv/>, <https://docs.astral.sh/uv/guides/projects/>, <https://docs.astral.sh/uv/concepts/projects/dependencies/>
**Last updated**: 2025-07-22
---

## Key features

- **10-100x faster** than pip
- Single tool replacing pip, pip-tools, pipx, poetry, pyenv, virtualenv
- Universal lockfile (`uv.lock`)
- `pyproject.toml`-based configuration
- Built-in Python version management
- Cargo-style workspaces
- Global dependency cache

## Project structure

```
project/
├── .python-version     # Default Python version
├── .venv/              # Virtual environment (auto-managed)
├── pyproject.toml      # Project metadata + dependencies
├── uv.lock             # Cross-platform lockfile (commit to VCS)
└── src/                # Source code
```

## Core commands

### Project initialization

```bash
uv init my-project          # Create new project
uv init                     # Initialize in current directory
```

### Dependency management

```bash
uv add requests             # Add dependency
uv add 'requests>=2.31.0'   # With version constraint
uv add "mcp[cli]"           # With extras
uv remove requests          # Remove dependency
uv lock                     # Update lockfile
uv lock --upgrade-package X # Upgrade specific package
uv sync                     # Sync environment with lockfile
```

### Running commands

```bash
uv run pytest               # Run in project environment
uv run python script.py     # Run script
uv run -- flask run -p 3000 # Run with arguments
```

`uv run` automatically verifies lockfile and environment are in sync before every invocation.

### Python version management

```bash
uv python install 3.12      # Install Python version
uv python pin 3.12          # Pin version for directory
```

## pyproject.toml structure

```toml
[project]
name = "rag4you"
version = "0.1.0"
description = "RAG framework"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.0",
    "mcp[cli]>=1.2.0",
    "tiktoken>=0.7.0",
]

[project.optional-dependencies]
bench = ["pandas>=2.0"]
mcp = ["mcp[cli]>=1.2.0", "httpx>=0.27"]

[dependency-groups]
dev = ["pytest>=8.0", "ruff>=0.5"]
lint = ["ruff>=0.5"]

[project.scripts]
rag4you = "rag4you.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
default-groups = ["dev"]
```

## Dependency types

### project.dependencies

Published dependencies. Included when package is installed by others.

### project.optional-dependencies (extras)

Optional dependency groups. Installed with `package[extra]` syntax.

```bash
uv add tiktoken --optional bench
# Result: [project.optional-dependencies] bench = ["tiktoken>=0.7.0"]
```

### dependency-groups (PEP 735)

Local development dependencies. NOT included when published.

```bash
uv add --dev pytest          # Goes to [dependency-groups] dev = [...]
uv add --group lint ruff     # Goes to [dependency-groups] lint = [...]
```

Groups can nest:

```toml
[dependency-groups]
dev = [
    {include-group = "lint"},
    {include-group = "test"},
]
```

### tool.uv.sources

Alternative sources for development (Git, path, workspace):

```toml
[tool.uv.sources]
my-lib = { path = "../my-lib", editable = true }
```

## Script entry points

```toml
[project.scripts]
rag4you = "rag4you.cli:main"
# After `uv sync`, run with: rag4you or uv run rag4you
```

## MCP SDK integration

The [[mcp-python-sdk]] recommends uv as its package manager:

```bash
uv init mcp-server-demo
cd mcp-server-demo
uv add "mcp[cli]"
uv run mcp dev server.py   # Development mode
uv run mcp install server.py  # Claude Desktop install
```

## Relevance to rag4you-cli

- **Mandated toolchain**: All Python work uses `uv add` and `uv run` (never bare `pip install`)
- **Commands**: `uv run pytest`, `uv run ruff check . && uv run ruff format .`
- **SP0** (bench/): Python package managed by uv
- **SP1** (rag4you/): Core package with optional dependencies for different features (validation via [[pydantic-v2]])
- **SP4** (rag4you/mcp/): MCP server installed via `uv add "mcp[cli]"`

## Related pages

- [[ruff-linter]]
- [[mcp-python-sdk]]
- [[pydantic-v2]]
