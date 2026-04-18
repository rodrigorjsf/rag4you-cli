# Pydantic v2

**Summary**: Pydantic is the most widely used data validation library for Python, powered by type hints. v2 features a Rust core for speed, JSON Schema generation, strict/lax modes, and rich serialization. It is integral to both MCP (tool schemas) and rag4you-cli (config models).
**Sources**: `docs/references/toolchain/bibliography.md`, https://docs.pydantic.dev/latest/, https://docs.pydantic.dev/latest/concepts/models/, https://docs.pydantic.dev/latest/concepts/fields/, https://docs.pydantic.dev/latest/concepts/validators/, https://docs.pydantic.dev/latest/concepts/json_schema/
**Last updated**: 2025-07-22
---

## Core concepts

### BaseModel

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    id: int
    name: str = "John Doe"
    email: str | None = None

user = User(id="123", name="Alice")  # Coerces "123" to int
print(user.model_dump())  # {'id': 123, 'name': 'Alice', 'email': None}
```

### Key model methods

| Method | Purpose |
|---|---|
| `model_validate(data)` | Validate dict/object against model |
| `model_validate_json(json_str)` | Validate JSON string (faster than manual parse) |
| `model_dump()` | Serialize to dict |
| `model_dump_json()` | Serialize to JSON string |
| `model_json_schema()` | Generate JSON Schema |
| `model_copy(update={...})` | Create modified copy |
| `model_construct(**data)` | Create without validation (for trusted data) |

### Field customization

```python
from pydantic import BaseModel, Field

class Config(BaseModel):
    chunk_size: int = Field(default=512, gt=0, le=8192, description="Chunk size in tokens")
    model_name: str = Field(default="all-MiniLM-L6-v2", description="Embedding model name")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Similarity threshold")
```

Field parameters:
- **Constraints**: `gt`, `ge`, `lt`, `le`, `min_length`, `max_length`, `pattern`, `strict`
- **Metadata**: `title`, `description`, `examples`, `json_schema_extra`
- **Aliases**: `alias`, `validation_alias`, `serialization_alias`
- **Defaults**: `default`, `default_factory`

### Annotated pattern (recommended)

```python
from typing import Annotated
from pydantic import BaseModel, Field

PositiveChunkSize = Annotated[int, Field(gt=0, le=8192, description="Chunk size")]

class Config(BaseModel):
    chunk_size: PositiveChunkSize = 512
```

Advantages: reusable types, cleaner field definitions, composable metadata.

## Validators

### Field validators

```python
from pydantic import BaseModel, field_validator

class SearchConfig(BaseModel):
    model_name: str
    top_k: int = 5

    @field_validator("model_name")
    @classmethod
    def validate_model(cls, v: str) -> str:
        allowed = {"all-MiniLM-L6-v2", "bge-small-en-v1.5"}
        if v not in allowed:
            raise ValueError(f"Model must be one of {allowed}")
        return v
```

Types: **After** (post-validation), **Before** (pre-validation), **Wrap** (full control), **Plain** (replaces validation).

### Model validators

```python
from pydantic import BaseModel, model_validator
from typing_extensions import Self

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    threshold: float = 0.7

    @model_validator(mode="after")
    def validate_search_params(self) -> Self:
        if self.top_k > 20 and self.threshold < 0.5:
            raise ValueError("High top_k with low threshold produces noisy results")
        return self
```

## JSON Schema generation

Pydantic generates JSON Schema Draft 2020-12, compatible with OpenAPI 3.1.0:

```python
import json
from pydantic import BaseModel, Field

class ToolInput(BaseModel):
    query: str = Field(description="Search query")
    collection: str = Field(description="Target collection name")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results")

schema = ToolInput.model_json_schema()
print(json.dumps(schema, indent=2))
```

Output:
```json
{
  "properties": {
    "query": { "description": "Search query", "title": "Query", "type": "string" },
    "collection": { "description": "Target collection name", "title": "Collection", "type": "string" },
    "top_k": { "default": 5, "description": "Number of results", "maximum": 100, "minimum": 1, "title": "Top K", "type": "integer" }
  },
  "required": ["query", "collection"],
  "title": "ToolInput",
  "type": "object"
}
```

This is directly used by MCP — FastMCP auto-generates tool `inputSchema` from Pydantic models and type hints.

## Configuration model pattern

Best practice for CLI tools with configurable options:

```python
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field

class RAGConfig(BaseModel):
    model_config = ConfigDict(
        extra="forbid",           # Reject unknown fields
        frozen=False,             # Allow mutation
        validate_default=True,    # Validate defaults too
    )

    collections_dir: Path = Field(default=Path("collections"))
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    chunk_size: int = Field(default=512, gt=0)
    chunk_overlap: int = Field(default=50, ge=0)
    top_k: int = Field(default=5, ge=1)
    scope: str = Field(default="project", pattern="^(project|global)$")
```

### Loading from YAML/JSON

```python
import yaml
from pathlib import Path

def load_config(path: Path) -> RAGConfig:
    with open(path) as f:
        data = yaml.safe_load(f)
    return RAGConfig.model_validate(data)
```

### Nested models

```python
class CollectionConfig(BaseModel):
    name: str
    paths: list[Path]
    chunk_size: int = 512

class ProjectConfig(BaseModel):
    version: str = "1"
    collections: list[CollectionConfig]
    defaults: RAGConfig = RAGConfig()
```

## Serialization

```python
# To dict
config.model_dump()
config.model_dump(exclude_defaults=True)
config.model_dump(by_alias=True)

# To JSON
config.model_dump_json(indent=2)

# From JSON (fast path — skips dict intermediate)
RAGConfig.model_validate_json(json_string)
```

## MCP integration

The [[mcp-python-sdk]] uses Pydantic directly:
- Tool `inputSchema` generated from function type hints and Pydantic models
- Tool `outputSchema` generated from return type annotations
- Structured output validated against Pydantic-generated schemas
- Elicitation schemas defined as Pydantic models
- Auth settings use Pydantic for configuration

## Relevance to rag4you-cli

- **Config models**: All configurable options (chunk size, model name, thresholds) defined as Pydantic BaseModel
- **SP0**: Benchmark configuration and report data models
- **SP1**: Collection schemas, model registry entries, search parameters
- **SP4**: MCP tool schemas derived from Pydantic models via FastMCP
- **Validation**: Ensures user-provided config files are valid before processing (managed via [[python-uv]])

## Related pages

- [[mcp-python-sdk]]
- [[python-uv]]
- [[ruff-linter]]
