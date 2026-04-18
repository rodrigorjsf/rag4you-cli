# Storage Backend — Source Bibliography

**Compiled**: 2025-07-22
**Purpose**: Bibliographic reference for sqlite-vec, FTS5, and hybrid search sources used in wiki/knowledge/sqlite-vec-fts5-hybrid-search.md

---

## sqlite-vec

### Official documentation
- **URL**: https://alexgarcia.xyz/sqlite-vec/
- **GitHub**: https://github.com/asg017/sqlite-vec
- **Author**: Alex Garcia
- **License**: MIT / Apache-2.0 dual
- **Key facts**: Pure C, zero dependencies, brute-force exhaustive scan (no ANN), supports float32/int8/bit vectors, pre-v1 status. ~33ms/query at 1M×128-dim on modern hardware.

### Python integration
- **PyPI**: https://pypi.org/project/sqlite-vec/
- **API pattern**: `vec0` virtual table with `cosine` distance function
- **Installation**: `uv add sqlite-vec`

## SQLite FTS5

### Official documentation
- **URL**: https://www.sqlite.org/fts5.html
- **Source**: SQLite official documentation
- **Key facts**: Built-in full-text search, BM25 ranking with hardcoded k1=1.2 b=0.75, multiple tokenizer options (unicode61, porter, trigram), external content table support.

### BM25 scoring
- **Reference**: Robertson, Zaragoza (2009). "The Probabilistic Relevance Framework: BM25 and Beyond". Foundations and Trends in Information Retrieval.
- **URL**: https://doi.org/10.1561/1500000019
- **Key formula**: `BM25(D,Q) = Σ IDF(q_i) · (f(q_i,D) · (k1+1)) / (f(q_i,D) + k1 · (1-b + b·|D|/avgdl))`

## Reciprocal Rank Fusion (RRF)

### Original paper
- **Title**: Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods
- **Authors**: Cormack, Clarke, Butt
- **Venue**: SIGIR 2009
- **URL**: https://dl.acm.org/doi/10.1145/1571941.1572114
- **Key formula**: `RRF_score(d) = Σ 1/(k + rank_i(d))` where k=60 (paper default)
- **Key insight**: Rank-based fusion requires no score normalization across heterogeneous rankers. Robust across diverse combinations.

## SQLite performance characteristics

### Official documentation
- **URL**: https://www.sqlite.org/whentouse.html
- **Key facts**: Single-file database, serverless, zero-configuration, ACID compliant. Optimal for datasets <1TB, single-writer workloads, embedded applications.
- **Relevance**: Ideal for local-first RAG systems where simplicity and portability outweigh horizontal scalability needs.
