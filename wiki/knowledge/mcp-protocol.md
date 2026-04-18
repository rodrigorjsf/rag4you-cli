# Model Context Protocol (MCP)

**Summary**: MCP is an open-source standard for connecting AI applications to external systems via a client-server architecture with JSON-RPC 2.0 messaging. It defines three core primitives (tools, resources, prompts) and two transport mechanisms (stdio, Streamable HTTP).
**Sources**: https://modelcontextprotocol.io/introduction, https://modelcontextprotocol.io/docs/concepts/architecture, https://modelcontextprotocol.io/docs/concepts/transports
**Last updated**: 2025-07-22
---

## What is MCP

MCP is an open protocol that standardizes how AI applications connect to external data sources, tools, and workflows. Think of it as a USB-C port for AI: a universal interface that any AI host can use to connect to any MCP server.

### Ecosystem support

MCP is supported by: Claude (Desktop & Code), ChatGPT, VS Code (Copilot), Cursor, and many others. Build once, integrate everywhere.

## Architecture

MCP follows a **client-server** architecture with three participants:

- **MCP Host**: The AI application (e.g., Claude Desktop, VS Code) that manages one or more MCP clients
- **MCP Client**: A component within the host that maintains a connection to a single MCP server
- **MCP Server**: A program that provides context (tools, resources, prompts) to MCP clients

### Two layers

| Layer | Purpose |
|---|---|
| **Data layer** | JSON-RPC 2.0 protocol: lifecycle management, primitives (tools, resources, prompts), notifications |
| **Transport layer** | Communication channels: stdio or Streamable HTTP, connection establishment, message framing |

## Core Primitives

MCP servers expose three types of primitives:

### Tools (model-controlled)

Executable functions the LLM can invoke. Similar to POST endpoints — they perform computation and have side effects.

```json
{
  "name": "get_weather",
  "title": "Weather Information Provider",
  "description": "Get current weather for a location",
  "inputSchema": {
    "type": "object",
    "properties": {
      "location": { "type": "string", "description": "City or zip code" }
    },
    "required": ["location"]
  },
  "outputSchema": { ... }
}
```

Key tool concepts:
- **Discovery**: `tools/list` — clients enumerate available tools
- **Execution**: `tools/call` — clients invoke tools with arguments
- **Structured output**: Tools can define `outputSchema` for typed responses plus `structuredContent` in results
- **Error handling**: Protocol errors (JSON-RPC) vs tool execution errors (`isError: true`)
- **Dynamic updates**: `notifications/tools/list_changed` when tool set changes

Tool results can contain: text, images, audio, resource links, or embedded resources.

### Resources (application-driven)

Data sources providing context. Similar to GET endpoints — no side effects.

```json
{
  "uri": "file:///project/src/main.rs",
  "name": "main.rs",
  "description": "Primary application entry point",
  "mimeType": "text/x-rust"
}
```

Key resource concepts:
- **URI-based**: Each resource identified by a unique URI (file://, https://, git://, custom schemes)
- **Templates**: Parameterized resources using URI templates (`file:///{path}`)
- **Subscriptions**: Clients can subscribe to changes (`resources/subscribe`)
- **Content types**: Text or binary (base64-encoded blob)
- **Annotations**: `audience`, `priority` (0-1), `lastModified`

### Prompts (user-controlled)

Reusable interaction templates, typically exposed as slash commands.

```json
{
  "name": "code_review",
  "title": "Request Code Review",
  "description": "Analyze code quality and suggest improvements",
  "arguments": [
    { "name": "code", "description": "The code to review", "required": true }
  ]
}
```

### Client Primitives

- **Sampling**: Servers request LLM completions from the host
- **Elicitation**: Servers request information or confirmation from users
- **Logging**: Servers send log messages to clients

## Transports

### stdio

- Client launches server as a subprocess
- JSON-RPC messages over stdin/stdout, delimited by newlines
- Server MUST NOT write non-MCP content to stdout (use stderr for logging)
- Optimal for local servers, no network overhead
- **Recommended**: Clients SHOULD support stdio whenever possible

### Streamable HTTP

- Server runs independently, handles multiple clients
- Single HTTP endpoint (e.g., `https://example.com/mcp`)
- Client POSTs JSON-RPC messages; server responds with JSON or SSE stream
- Supports session management via `Mcp-Session-Id` header
- Supports resumability with SSE event IDs
- Security: MUST validate Origin header, bind to localhost when local, implement authentication

## Lifecycle

1. Client sends `initialize` request with its capabilities
2. Server responds with its capabilities and protocol version
3. Client sends `initialized` notification
4. Normal message exchange (requests, responses, notifications)
5. Either side can terminate

## Security Requirements

Servers MUST:
- Validate all tool inputs
- Implement access controls
- Rate limit tool invocations
- Sanitize tool outputs

Clients SHOULD:
- Prompt for user confirmation on sensitive operations
- Show tool inputs to user before calling
- Validate tool results before passing to LLM
- Implement timeouts

## Relevance to rag4you-cli

SP4 plans to build a **dynamic, scope-aware MCP server** using [[mcp-python-sdk]] at `rag4you/mcp/` that:
- Derives tools from the active config (one tool per collection), with schemas via [[pydantic-v2]]
- Supports project-vs-global scope awareness
- Integrates with the SP3 CLI wizard
- Managed via [[python-uv]] toolchain

## Related pages

- [[mcp-python-sdk]]
- [[python-uv]]
- [[pydantic-v2]]
