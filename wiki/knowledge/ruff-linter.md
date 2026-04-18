# Ruff Linter and Formatter

**Summary**: Ruff is an extremely fast Python linter and formatter written in Rust (by Astral, makers of uv). It replaces Flake8, Black, isort, pyupgrade, and more. The rag4you-cli project uses Ruff for all linting and formatting via `uv run ruff check .` and `uv run ruff format .`.
**Sources**: `docs/references/toolchain/bibliography.md`, https://docs.astral.sh/ruff/, https://docs.astral.sh/ruff/configuration/, https://docs.astral.sh/ruff/rules/
**Last updated**: 2025-07-22
---

## Key features

- **10-100x faster** than Flake8 and Black
- **900+ built-in rules** (re-implementations of Flake8 plugins)
- Drop-in parity with Flake8, isort, and Black
- `pyproject.toml` native configuration
- Auto-fix support (`--fix`)
- Built-in caching
- Python 3.14 compatibility
- Hierarchical configuration (ESLint-like)

## Usage

```bash
# Lint
uv run ruff check .

# Lint with auto-fix
uv run ruff check . --fix

# Format (Black-compatible)
uv run ruff format .

# Check formatting without changes
uv run ruff format . --check

# Combined (project convention)
uv run ruff check . && uv run ruff format .
```

## Configuration in pyproject.toml

### Recommended configuration for rag4you-cli

```toml
[tool.ruff]
target-version = "py310"
line-length = 88

[tool.ruff.lint]
select = [
    "E4", "E7", "E9",  # pycodestyle errors
    "F",                # Pyflakes
    "B",                # flake8-bugbear
    "I",                # isort
    "UP",               # pyupgrade
    "S",                # flake8-bandit (security)
    "ANN",              # flake8-annotations
    "RUF",              # Ruff-specific rules
]
ignore = ["E501"]       # Line length handled by formatter

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]   # Allow assert in tests
"__init__.py" = ["E402"] # Allow late imports in __init__

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
docstring-code-format = true
```

### Default configuration reference

```toml
[tool.ruff]
line-length = 88
indent-width = 4
target-version = "py310"
exclude = [".venv", "build", "dist", "node_modules", ...]

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F"]  # Default: Pyflakes + subset pycodestyle
fixable = ["ALL"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

## Key rule categories

| Code | Source | Purpose |
|---|---|---|
| `F` | Pyflakes | Undefined names, unused imports/variables |
| `E`/`W` | pycodestyle | Style errors and warnings |
| `B` | flake8-bugbear | Common bug patterns |
| `I` | isort | Import sorting |
| `UP` | pyupgrade | Modernize Python syntax |
| `S` | flake8-bandit | Security issues |
| `ANN` | flake8-annotations | Missing type annotations |
| `RUF` | Ruff-specific | Ruff's own rules |
| `D` | pydocstyle | Docstring conventions |
| `ASYNC` | flake8-async | Async best practices |
| `FAST` | FastAPI | FastAPI-specific checks |

## Configuration discovery

Ruff uses hierarchical config (closest `pyproject.toml` with `[tool.ruff]` wins):

1. `.ruff.toml` > `ruff.toml` > `pyproject.toml` (same directory)
2. Walk up directory tree for nearest config
3. Fall back to user-level config or defaults
4. Command-line flags override all

## Integration with uv

Ruff and [[python-uv]] are both by Astral. The standard workflow:

```bash
# Add as dev dependency
uv add --group lint ruff

# Run via uv
uv run ruff check .
uv run ruff format .
```

## Relevance to rag4you-cli

- **Mandated tools**: `uv run ruff check . && uv run ruff format .` for all Python code
- **Config location**: `[tool.ruff]` section in project `pyproject.toml`
- **Rule selection**: Should include `B` (bugbear), `I` (isort), `UP` (pyupgrade) beyond defaults
- **Per-file ignores**: Tests need `S101` (assert) exemption
- **Applies to**: SP0 `bench/` and SP1+ `rag4you/` packages

## Related pages

- [[python-uv]]
- [[pydantic-v2]]
