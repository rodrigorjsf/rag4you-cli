# MCP Python SDK

**Summary**: The official Python SDK for building MCP servers and clients. Provides FastMCP (high-level, decorator-based API) and a low-level server API. Uses `uv` as the recommended package manager and Pydantic for structured output.
**Sources**: https://github.com/modelcontextprotocol/python-sdk, https://modelcontextprotocol.io/quickstart/server
**Last updated**: 2025-07-22
---

## Installation

```bash
# Recommended: with uv
uv add "mcp[cli]"

# Alternative: with pip
pip install "mcp[cli]"
```

The `[cli]` extra includes MCP development tools (`mcp dev`, `mcp install`, `mcp run`). See [[python-uv]] for the recommended package manager setup.

**Minimum requirements**: Python 3.10+, MCP SDK 1.2.0+

## FastMCP — High-Level API

FastMCP is the recommended way to build MCP servers. It uses Python **type hints and docstrings** to automatically generate tool definitions.

### Server initialization

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My Server")

# With JSON responses (recommended for production)
mcp = FastMCP("My Server", stateless_http=True, json_response=True)
```

### Defining tools

```python
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
async def get_weather(city: str) -> str:
    """Get weather for a city."""
    # Async tools are fully supported
    return f"Weather in {city}: sunny"
```

### Structured output with Pydantic ([[pydantic-v2]])

Tools return structured data automatically when using typed returns:

```python
from pydantic import BaseModel, Field

class WeatherData(BaseModel):
    temperature: float = Field(description="Temperature in Celsius")
    humidity: float = Field(description="Humidity percentage")
    condition: str

@mcp.tool()
def get_weather(city: str) -> WeatherData:
    """Returns structured weather data."""
    return WeatherData(temperature=22.5, humidity=45.0, condition="sunny")
```

Supported structured return types:
- **Pydantic BaseModel** (recommended for rich schemas)
- **TypedDict**
- **Dataclasses** and classes with type hints
- **dict[str, T]** for flexible schemas
- **Primitives** (str, int, float, bool) — wrapped as `{"result": value}`
- **Lists, tuples, Optional** — wrapped as `{"result": value}`

### Defining resources

```python
@mcp.resource("file://documents/{name}")
def read_document(name: str) -> str:
    """Read a document by name."""
    return f"Content of {name}"

@mcp.resource("config://settings")
def get_settings() -> str:
    """Static resource."""
    return '{"theme": "dark"}'
```

### Defining prompts

```python
from mcp.server.fastmcp.prompts import base

@mcp.prompt(title="Code Review")
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"

@mcp.prompt(title="Debug Assistant")
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that."),
    ]
```

### Context object

Injected automatically when a parameter has `Context` type annotation:

```python
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

@mcp.tool()
async def long_task(name: str, ctx: Context[ServerSession, None]) -> str:
    await ctx.info(f"Starting: {name}")
    await ctx.report_progress(progress=0.5, total=1.0, message="Halfway")
    return f"Done: {name}"
```

Context provides:
- `ctx.request_id` — unique request ID
- `ctx.debug()`, `ctx.info()`, `ctx.warning()`, `ctx.error()` — logging
- `ctx.report_progress()` — progress reporting
- `ctx.read_resource(uri)` — read a resource
- `ctx.elicit(message, schema)` — request user input
- `ctx.session` — underlying session for advanced communication
- `ctx.fastmcp` — access to server instance

### Lifespan management

```python
from contextlib import asynccontextmanager
from dataclasses import dataclass

@dataclass
class AppContext:
    db: Database

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    db = await Database.connect()
    try:
        yield AppContext(db=db)
    finally:
        await db.disconnect()

mcp = FastMCP("My App", lifespan=app_lifespan)

@mcp.tool()
def query_db(ctx: Context[ServerSession, AppContext]) -> str:
    db = ctx.request_context.lifespan_context.db
    return db.query()
```

## Running servers

### Development mode (MCP Inspector)

```bash
uv run mcp dev server.py
uv run mcp dev server.py --with pandas --with numpy
```

### Claude Desktop integration

```bash
uv run mcp install server.py
uv run mcp install server.py --name "My Server"
uv run mcp install server.py -v API_KEY=abc123
```

### Direct execution

```python
if __name__ == "__main__":
    mcp.run()                          # stdio (default)
    mcp.run(transport="stdio")         # explicit stdio
    mcp.run(transport="streamable-http")  # HTTP
```

### Streamable HTTP transport (production)

```python
mcp = FastMCP("Server", stateless_http=True, json_response=True)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

### Mounting in Starlette/ASGI

```python
from starlette.applications import Starlette
from starlette.routing import Mount

app = Starlette(
    routes=[
        Mount("/echo", echo_mcp.streamable_http_app()),
        Mount("/math", math_mcp.streamable_http_app()),
    ],
    lifespan=lifespan,
)
# Clients connect to /echo/mcp and /math/mcp
```

## Authentication

MCP SDK implements OAuth 2.1 resource server functionality:

```python
from mcp.server.auth.provider import TokenVerifier
from mcp.server.auth.settings import AuthSettings

mcp = FastMCP(
    "Protected Server",
    token_verifier=MyTokenVerifier(),
    auth=AuthSettings(
        issuer_url="https://auth.example.com",
        resource_server_url="http://localhost:3001",
        required_scopes=["user"],
    ),
)
```

## Critical logging rules

- **stdio servers**: NEVER use `print()` or write to stdout — it corrupts JSON-RPC. Use `print(..., file=sys.stderr)` or `logging`.
- **HTTP servers**: Standard output is fine.

## Relevance to rag4you-cli

SP4 will use FastMCP (see [[mcp-protocol]]) to build the dynamic MCP server:
- One tool per RAG collection, derived from active config
- Pydantic models for structured tool input/output schemas
- Lifespan for database/index initialization
- Context for progress reporting during search operations

## Related pages

- [[mcp-protocol]]
- [[pydantic-v2]]
- [[python-uv]]
