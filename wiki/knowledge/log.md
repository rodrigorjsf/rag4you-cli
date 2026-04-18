# Wiki Knowledge Log

Append-only record of all wiki operations.

---

## 2025-07-22 — Initial technology knowledge base

**Source**: Official documentation from modelcontextprotocol.io, GitHub repos, docs.astral.sh, docs.pydantic.dev
**Operation**: Created 6 knowledge pages from research across 20+ official documentation sources.
**Pages created**:
- `mcp-protocol.md` — MCP architecture, primitives, transports, lifecycle, security
- `mcp-python-sdk.md` — FastMCP API, decorators, structured output, server transports, auth
- `python-uv.md` — Project structure, commands, dependency types, script entry points
- `pydantic-v2.md` — BaseModel, fields, validators, JSON Schema, config patterns
- `ruff-linter.md` — Rules, configuration, per-file ignores, integration
- `tiktoken.md` — Encodings, token counting, chunk validation, token economy metrics
- `index.md` — Table of contents and cross-cutting themes
**Purpose**: Establish technology knowledge base for SP0-SP4 implementation.

## 2025-07-22 — RAG foundations and research knowledge base

**Source**: 18 academic papers (arxiv, NeurIPS, EMNLP, IEEE-MIPR, ICLR) + 7 official documentation sources (Anthropic, LlamaIndex, LangChain)
**Operation**: Created `rag-research-compendium.md` from comprehensive research across RAG academic literature.
**Pages created**:
- `rag-research-compendium.md` — Lewis et al. (2020) foundational paper, Gao et al. (2024) survey, retrieval techniques (DPR, ColBERT, hybrid/RRF), chunking strategies, reranking, query decomposition, advanced paradigms (Self-RAG, CRAG, GraphRAG), evaluation metrics, token economy, local/offline RAG
**Purpose**: Provide academic foundations for all RAG implementation decisions across SP0-SP4.

## 2025-07-22 — Storage backend research

**Source**: sqlite-vec official docs (alexgarcia.xyz/sqlite-vec), SQLite FTS5 official docs (sqlite.org/fts5.html), Cormack et al. (2009) RRF paper
**Operation**: Created `sqlite-vec-fts5-hybrid-search.md` from official documentation research.
**Pages created**:
- `sqlite-vec-fts5-hybrid-search.md` — sqlite-vec API, vec0 virtual table, KNN queries, FTS5 BM25, tokenizers, RRF algorithm, hybrid search architecture, scale considerations, design decisions
**Purpose**: Provide authoritative storage backend reference for SP0 benchmark target and SP1 core implementation.

## 2025-07-22 — Embedding models and FastEmbed research

**Source**: HuggingFace model cards, arXiv papers (8 papers), Qdrant/FastEmbed official docs, MTEB benchmark
**Operation**: Created `embedding-models-research.md` from official sources and academic papers.
**Pages created**:
- `embedding-models-research.md` — FastEmbed library, BGE models (3 tiers), code embedding models (Jina v2, Nomic, GTE-Qwen2), cross-encoder reranking (BGE Reranker v2 M3), chunking strategies for code vs docs, model selection matrix
**Purpose**: Guide embedding model selection and configuration for SP0 sweep matrix and SP1/SP2 model tiers.

## 2025-07-22 — IR evaluation and benchmarking research

**Source**: Manning/Raghavan/Schütze textbook, TREC methodology, RAGAS docs, 20 authoritative academic sources (NeurIPS, NAACL, ACL, SIGIR)
**Operation**: Created `ir-evaluation-benchmarking.md` from academic and official documentation research.
**Pages created**:
- `ir-evaluation-benchmarking.md` — Classical IR metrics (Precision@k, MRR, NDCG), RAGAS framework, ARES, LLM-as-judge (Zheng et al.), golden set construction, synthetic query generation, reproducibility, checkpoint/resume patterns, token economy
**Purpose**: Provide academic foundations for SP0 benchmark harness (metrics.py, judges/, golden/, checkpoint.py).

## 2025-07-22 — Wiki format compliance and quality pass

**Source**: Quality review against `wiki/CLAUDE.md` conventions
**Operation**: Normalized all 10 content pages to comply with wiki page format. Fixed headers (Summary/Sources/Last updated), added `[[knowledge-links]]` throughout body text, added `## Related pages` footers, added inline `(source: filename)` citations, fixed 384-dim vs 768-dim contradiction in sqlite-vec page, deduplicated evaluation content in rag-research-compendium (defers to `[[ir-evaluation-benchmarking]]`), labeled planned code paths as "(planned — not yet implemented)".
**Pages modified**:
- `rag-research-compendium.md` — header, knowledge-links, citations, evaluation dedup, Related pages
- `embedding-models-research.md` — header, knowledge-links, citations, Related pages
- `sqlite-vec-fts5-hybrid-search.md` — header, knowledge-links, citations, dimension fix, Related pages
- `ir-evaluation-benchmarking.md` — header, knowledge-links, citations, planned-code labels, Related pages
- `mcp-protocol.md` — knowledge-links
- `mcp-python-sdk.md` — knowledge-links
- `python-uv.md` — Sources field, knowledge-links
- `pydantic-v2.md` — Sources field, knowledge-links
- `ruff-linter.md` — Sources field, knowledge-links
- `tiktoken.md` — Sources field, knowledge-links
**Purpose**: Ensure all wiki pages pass the lint checklist in `wiki/CLAUDE.md` and provide a navigable knowledge graph via `[[knowledge-links]]`.
