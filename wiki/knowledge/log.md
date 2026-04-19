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

## 2026-04-19 — SP0 Phase 1 implementation — update planned markers

**Source**: Phase 1 implementation (bench/ package)
**Operation**: Updated `ir-evaluation-benchmarking.md` to reflect Phase 1 deliverables — `bench/metrics.py` and `bench/tests/` are now implemented (48 tests green).
**Pages modified**:

- `ir-evaluation-benchmarking.md` — removed "(planned, not yet implemented)" from `bench/metrics.py` reference in §1.3; updated `bench/tests/` reference in §3.5 to reflect 48 passing tests; bumped Last updated to 2026-04-19
**Purpose**: Keep wiki in sync with implemented Phase 1 artifacts per CLAUDE.md convention.

## 2025-07-23 — TurboQuant and GraphQLite deep research

**Source**: arXiv:2504.19874 (TurboQuant paper), arXiv:2406.03482 (QJL paper), PolarQuant paper, Firmamento-Technologies/TurboQuant (GitHub), yashkc2025/turboquant (GitHub), colliery-io/graphqlite (GitHub v0.4.4), graphqlite docs/tutorials/graphrag.md, graphqlite examples/llm-graphrag/
**Operation**: Deep research on TurboQuant implementations for RAG embedding compression and GraphQLite for hybrid vector+graph RAG. Created raw reference docs and wiki knowledge pages.
**Pages created**:

- `turboquant-vector-quantization.md` — Algorithm overview, theoretical guarantees, RAG benchmarks (95%+ recall at 5.3x compression), three implementation repos (Firmamento for vector search, yashkc2025 general purpose, turboquant-mlx for Apple Silicon), integration patterns with sqlite-vec, configuration guidance for LLM agents
- `graphqlite-hybrid-rag.md` — GraphQLite architecture (Cypher transpiler → SQL), 18 graph algorithms (PageRank, Louvain, Dijkstra, BFS, etc.), complete GraphRAG pipeline (entity extraction, co-occurrence graphs, multi-hop retrieval, community detection), triple-hybrid RAG architecture (vector + keyword + graph on same SQLite DB), integration code patterns
**Raw docs saved**:
- `docs/raw/turboquant/turboquant-implementations.md` — Comprehensive implementation reference with code examples from both repos
- `docs/raw/graphqlite-hybrid-rag.md` — Full GraphQLite documentation, API reference, and GraphRAG example code
**Pages modified**:
- `index.md` — Added entries for both new pages, updated cross-cutting themes
**Purpose**: Establish knowledge base for embedding compression (TurboQuant) and graph-enhanced retrieval (GraphQLite) to guide SP1/SP2 implementation of triple-hybrid RAG stack.

## 2025-07-24 — TurboQuant applicability deep-dive & GraphQLite PDF extraction

**Source**: arXiv:2504.19874 Section 4.4 (NN Search Experiments), GraphQLite-documentation.pdf (261 pages, v0.4.4), web research on TurboQuant implementations (vivekvar-dl, TheTom/turboquant_plus), Diffbot/FalkorDB 2025 GraphRAG benchmarks
**Operation**: Extended TurboQuant and GraphQLite documentation with official applicability examples, additional implementations, performance benchmarks, and comprehensive architecture details from official PDF extraction.
**Raw docs saved**:

- `docs/raw/turboquant/turboquant-applicability-examples.md` — Official paper NN search benchmarks, recall results on OpenAI embeddings, 6 implementation repos with code examples, embedding model compatibility guide, LLM agent decision matrix
- `docs/raw/graphqlite/graphqlite-full-documentation.md` — Full 261-page PDF extraction (13,089 lines), comprehensive API reference
- `docs/raw/graphqlite/graphqlite-extended-reference.md` — Curated reference with architecture pipeline, EAV schema details, performance benchmarks, Python API, GraphRAG tutorial code, scaling characteristics
**Pages modified**:
- `turboquant-vector-quantization.md` — Added 2 new implementations (vivekvar-dl, TheTom/turboquant_plus), official paper applicability section with recall on OpenAI embeddings, embedding model compatibility table, LLM agent decision matrix and implementation steps
- `graphqlite-hybrid-rag.md` — Replaced architecture section with PDF-sourced transpiler pipeline details, added typed EAV schema, CSR memory formula table, performance benchmarks table (from official PDF), scaling characteristics table, GraphRAG vs Vector RAG accuracy comparison, Python API quick reference, bulk insert guidance, installation options
- `index.md` — Updated descriptions for both pages
**Purpose**: Provide comprehensive implementation guidance for LLM agents building the triple-hybrid RAG stack, including official benchmarks, code patterns, and decision matrices.
