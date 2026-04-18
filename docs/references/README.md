# Reference Documents

This directory contains curated reference documents compiled from official and academic sources. These serve as immutable source material for the wiki knowledge base in `wiki/knowledge/`.

## Organization

| Directory | Content |
|---|---|
| `rag-foundations/` | RAG academic papers, surveys, and official documentation |
| `storage-backend/` | sqlite-vec, FTS5, and hybrid search references |
| `embedding-models/` | FastEmbed, BGE, Jina, and code embedding model references |
| `evaluation/` | IR evaluation metrics, RAGAS, benchmarking methodology |
| `toolchain/` | MCP, uv, Pydantic v2, Ruff, tiktoken references |

## Source quality policy

Every document in this directory must:
1. Come from an official or academic source (arxiv, ACL Anthology, official docs, vendor documentation)
2. Include a direct URL or DOI to the original
3. Note the date accessed
4. Never contain speculation or unverified claims

## Relationship to wiki

- `docs/references/` → immutable source material (never modified after creation)
- `wiki/knowledge/` → maintained knowledge pages that synthesize and cross-reference sources
- Changes to understanding should create new wiki pages, not modify source documents
