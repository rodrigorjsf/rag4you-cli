# Toolchain — Source Bibliography

**Compiled**: 2025-07-22
**Purpose**: Bibliographic reference for MCP, uv, Pydantic, Ruff, and tiktoken sources used in wiki/knowledge/ pages

---

## Model Context Protocol (MCP)

### Official specification
- **URL**: https://modelcontextprotocol.io/
- **GitHub**: https://github.com/modelcontextprotocol
- **Key pages**:
  - Introduction: https://modelcontextprotocol.io/introduction
  - Architecture: https://modelcontextprotocol.io/docs/concepts/architecture
  - Transports: https://modelcontextprotocol.io/docs/concepts/transports
  - Tools: https://modelcontextprotocol.io/docs/concepts/tools
  - Resources: https://modelcontextprotocol.io/docs/concepts/resources
  - Prompts: https://modelcontextprotocol.io/docs/concepts/prompts

### Python SDK
- **GitHub**: https://github.com/modelcontextprotocol/python-sdk
- **Quickstart**: https://modelcontextprotocol.io/quickstart/server
- **Key API**: FastMCP with decorator-based tool definitions, Pydantic integration, stdio/HTTP transports

## Python uv

### Official documentation
- **URL**: https://docs.astral.sh/uv/
- **GitHub**: https://github.com/astral-sh/uv
- **Key pages**:
  - Overview: https://docs.astral.sh/uv/
  - Projects: https://docs.astral.sh/uv/guides/projects/
  - Dependencies: https://docs.astral.sh/uv/concepts/projects/dependencies/
- **Key facts**: Rust-based, 10-100x faster than pip, replaces pip+pip-tools+poetry+pyenv+virtualenv. Uses `pyproject.toml` + `uv.lock`.

## Pydantic v2

### Official documentation
- **URL**: https://docs.pydantic.dev/latest/
- **Key pages**:
  - Models: https://docs.pydantic.dev/latest/concepts/models/
  - Fields: https://docs.pydantic.dev/latest/concepts/fields/
  - Validators: https://docs.pydantic.dev/latest/concepts/validators/
  - JSON Schema: https://docs.pydantic.dev/latest/concepts/json_schema/
- **Key facts**: Rust core (pydantic-core), 5-50x faster than v1, JSON Schema generation, strict/lax modes. Required by MCP Python SDK.

## Ruff

### Official documentation
- **URL**: https://docs.astral.sh/ruff/
- **GitHub**: https://github.com/astral-sh/ruff
- **Key pages**:
  - Configuration: https://docs.astral.sh/ruff/configuration/
  - Rules: https://docs.astral.sh/ruff/rules/
- **Key facts**: Rust-based, 900+ rules, replaces Flake8+Black+isort+pyupgrade. Native `pyproject.toml` configuration.

## tiktoken

### Official repository
- **GitHub**: https://github.com/openai/tiktoken
- **PyPI**: https://pypi.org/project/tiktoken/
- **Cookbook**: https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken
- **Key facts**: Rust-based BPE tokenizer. `cl100k_base` encoding used by SP0 for model-agnostic token counting. 3-6x faster than equivalent Python implementations.
