# Wiki Knowledge Index

**Summary**: Table of contents for the rag4you-cli knowledge base.
**Last updated**: 2025-07-22
---

## RAG foundations and research

| Page | Description |
|---|---|
| [[rag-research-compendium]] | Comprehensive RAG research: foundational papers, retrieval techniques, chunking, reranking, advanced paradigms (Self-RAG, CRAG, GraphRAG), evaluation overview. 18 academic papers + 7 official sources. |
| [[ir-evaluation-benchmarking]] | IR evaluation metrics (Precision@k, MRR, NDCG), RAGAS framework, LLM-as-judge, golden set construction, checkpoint patterns, token economy. 20 authoritative sources. |
| [[embedding-models-research]] | FastEmbed library, BGE embedding models (small/base/large), code embedding models (Jina v2, Nomic, GTE-Qwen2), cross-encoder reranking, chunking strategies. 8 academic papers. |
| [[sqlite-vec-fts5-hybrid-search]] | sqlite-vec vector search, SQLite FTS5 full-text search, BM25 scoring, Reciprocal Rank Fusion (RRF), hybrid search architecture, design decisions. |

## Technology references

| Page | Description |
|---|---|
| [[mcp-protocol]] | MCP open protocol: architecture, primitives (tools/resources/prompts), transports, lifecycle |
| [[mcp-python-sdk]] | Official Python SDK: FastMCP, decorators, structured output, context, running servers |
| [[python-uv]] | uv package manager: project structure, dependency types, commands, MCP integration |
| [[pydantic-v2]] | Pydantic v2: BaseModel, fields, validators, JSON Schema, config pattern |
| [[ruff-linter]] | Ruff linter and formatter: rules, configuration, integration with uv |
| [[tiktoken]] | tiktoken: BPE tokenizer, token counting, encoding selection, chunk validation |

## Cross-cutting themes

- **RAG pipeline**: [[rag-research-compendium]] covers the full pipeline; [[embedding-models-research]] details model selection; [[sqlite-vec-fts5-hybrid-search]] covers the storage layer
- **SP0 benchmark harness**: [[ir-evaluation-benchmarking]] provides academic foundations for `bench/metrics.py`, `bench/judges/`, `bench/golden/`, and `bench/checkpoint.py`
- **MCP + Pydantic**: FastMCP auto-generates tool schemas from Pydantic models and type hints
- **MCP + uv**: SDK installs via `uv add "mcp[cli]"`, dev tools run via `uv run mcp dev`
- **Ruff + uv**: Both by Astral, `uv add --group lint ruff`, `uv run ruff check .`
- **tiktoken + Pydantic**: Token metrics modeled as Pydantic BaseModel for validation and serialization
