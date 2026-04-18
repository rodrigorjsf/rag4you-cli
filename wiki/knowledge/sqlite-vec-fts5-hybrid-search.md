# SQLite-vec + FTS5 + RRF Hybrid Search — Research Reference

**Summary**: Authoritative reference for the rag4you-cli storage backend covering sqlite-vec, FTS5, BM25, Reciprocal Rank Fusion, and hybrid search architecture design.
**Sources**: docs/references/storage-backend/bibliography.md
**Last updated**: 2025-07-22
---

## Table of Contents

1. [sqlite-vec Overview](#1-sqlite-vec-overview)
2. [sqlite-vec API Reference](#2-sqlite-vec-api-reference)
3. [sqlite-vec vec0 Virtual Table](#3-sqlite-vec-vec0-virtual-table)
4. [sqlite-vec KNN Queries](#4-sqlite-vec-knn-queries)
5. [sqlite-vec Performance and Limitations](#5-sqlite-vec-performance-and-limitations)
6. [sqlite-vec Python Integration](#6-sqlite-vec-python-integration)
7. [SQLite FTS5 Overview](#7-sqlite-fts5-overview)
8. [FTS5 BM25 Ranking](#8-fts5-bm25-ranking)
9. [FTS5 Tokenizers](#9-fts5-tokenizers)
10. [FTS5 External Content Tables](#10-fts5-external-content-tables)
11. [Reciprocal Rank Fusion (RRF)](#11-reciprocal-rank-fusion-rrf)
12. [Hybrid Search Architecture](#12-hybrid-search-architecture)
13. [SQLite as a Vector Database](#13-sqlite-as-a-vector-database)
14. [Design Decisions for rag4you-cli](#14-design-decisions-for-rag4you-cli)

---

## 1. sqlite-vec Overview

**Source**: <https://alexgarcia.xyz/sqlite-vec/> · <https://github.com/asg017/sqlite-vec>

sqlite-vec is a vector search SQLite extension written entirely in C with zero
dependencies. It is a successor to `sqlite-vss`.

### Key Characteristics

| Property | Value |
|---|---|
| License | MIT / Apache-2.0 dual |
| Language | Pure C, no dependencies |
| Status | Pre-v1 (expect breaking changes) |
| Sponsor | Mozilla Builders (primary), Fly.io, Turso, SQLite Cloud |
| Vector types | `float32`, `int8`, `bit` |
| Search method | Brute-force exhaustive scan (no ANN index yet) |
| Storage | Shadow tables inside the SQLite database file |
| Platforms | Linux, macOS, Windows, WASM, Raspberry Pi, mobile |

### Core Principle

sqlite-vec works like SQLite FTS5 — declare a virtual table, insert with
`INSERT INTO`, and query with `SELECT ... WHERE ... MATCH ... ORDER BY distance`.

```sql
create virtual table vec_movies using vec0(
  synopsis_embedding float[768]
);

insert into vec_movies(rowid, synopsis_embedding)
  select rowid, embed(synopsis) from movies;

select rowid, distance
from vec_movies
where synopsis_embedding match embed('scary futuristic movies')
order by distance
limit 20;
```

---

## 2. sqlite-vec API Reference

**Source**: <https://alexgarcia.xyz/sqlite-vec/api-reference.html>

### Constructors

| Function | Description |
|---|---|
| `vec_f32(vector)` | Creates float32 vector from BLOB or JSON. Subtype 223. |
| `vec_int8(vector)` | Creates int8 vector from BLOB or JSON. Elements must be -128..127. Subtype 225. |
| `vec_bit(vector)` | Creates binary vector from BLOB. 1 byte per 8 elements. Subtype 224. |

### Operations

| Function | Description |
|---|---|
| `vec_length(vector)` | Number of elements in the vector |
| `vec_type(vector)` | Returns `'float32'`, `'int8'`, or `'bit'` |
| `vec_add(a, b)` | Element-wise addition (float32 and int8 only) |
| `vec_sub(a, b)` | Element-wise subtraction (float32 and int8 only) |
| `vec_normalize(vector)` | L2 normalization (float32 only) |
| `vec_slice(vector, start, end)` | Extract subset (useful for Matryoshka embeddings) |
| `vec_to_json(vector)` | Convert vector to JSON text representation |
| `vec_each(vector)` | Table function to iterate each element |

### Distance Functions

| Function | Description | Vector Types |
|---|---|---|
| `vec_distance_L2(a, b)` | Euclidean (L2) distance | float32, int8 |
| `vec_distance_cosine(a, b)` | Cosine distance | float32, int8 |
| `vec_distance_hamming(a, b)` | Hamming distance | bit only |

### Quantization

| Function | Description |
|---|---|
| `vec_quantize_binary(vector)` | Quantize float32/int8 to bitvector. Positive→1, negative→0. |
| `vec_quantize_i8(vector)` | Quantize float32 to int8 (documentation pending) |

### Meta

| Function | Description |
|---|---|
| `vec_version()` | Returns installed version string |
| `vec_debug()` | Returns debugging info (version, date, commit, build flags) |

---

## 3. sqlite-vec vec0 Virtual Table

**Source**: <https://alexgarcia.xyz/sqlite-vec/features/vec0.html>

The `vec0` virtual table is the primary storage mechanism. It stores vectors in
chunked shadow tables inside the same SQLite database.

### Column Types

```sql
create virtual table vec_chunks using vec0(
  document_id integer partition key,
  contents_embedding float[768],
  user_id integer partition key,    -- partition key
  label text,                        -- metadata column
  +contents text                     -- auxiliary column (+ prefix)
);
```

| Column Type | Description | KNN WHERE? | Max Count |
|---|---|---|---|
| **Vector columns** | The vector data (float, int8, bit) | MATCH only | — |
| **Metadata columns** | Regular typed columns (TEXT, INTEGER, FLOAT, BOOLEAN) | Yes (`=`, `!=`, `>`, `>=`, `<`, `<=`) | 16 |
| **Auxiliary columns** | Large data stored in separate table (prefix `+`) | No (SELECT only) | 16 |
| **Partition key** | Internal sharding key for selective queries | `=` only | 4 |

### Metadata Columns — Supported Operations

Metadata columns in a KNN `WHERE` clause support only:
- `=`, `!=`, `>`, `>=`, `<`, `<=`
- Boolean columns: `=` and `!=` only
- **NOT** supported: `IS NULL`, `LIKE`, `GLOB`, `REGEXP`, scalar functions

### Partition Keys — Best Practices

- Each unique partition key value should have **~100+ vectors**
- Over-sharding degrades KNN performance
- Useful for per-user or per-time-period isolation
- Vectors with the same partition key are collocated together

### Distance Metrics

```sql
create virtual table vec_docs using vec0(
  embedding float[768] distance_metric=cosine  -- default is L2
);
```

Available metrics: `l2` (default), `cosine`.

---

## 4. sqlite-vec KNN Queries

**Source**: <https://alexgarcia.xyz/sqlite-vec/features/knn.html>

### Two Query Methods

**Method 1: vec0 virtual table (recommended)**

```sql
select document_id, distance
from vec_documents
where contents_embedding match :query
  and k = 10;
```

Or with `LIMIT` (SQLite ≥ 3.41 only):

```sql
select document_id, distance
from vec_documents
where contents_embedding match :query
limit 10;
```

**Method 2: Manual scalar functions (brute-force)**

```sql
select id, contents,
  vec_distance_cosine(contents_embedding, :query) as distance
from documents
order by distance
limit 10;
```

### JOINing Back to Source Tables

```sql
with knn_matches as (
  select document_id, distance
  from vec_documents
  where contents_embedding match :query and k = 10
)
select documents.id, documents.contents, knn_matches.distance
from knn_matches
left join documents on documents.id = knn_matches.document_id;
```

### Data Integrity for Manual Storage

When storing vectors in regular columns, use CHECK constraints:

```sql
create table documents(
  id integer primary key,
  contents text,
  contents_embedding blob
    check(typeof(contents_embedding) == 'blob'
      and vec_length(contents_embedding) == 768)
);
```

---

## 5. sqlite-vec Performance and Limitations

**Source**: <https://alexgarcia.xyz/blog/2024/sqlite-vec-stable-release/index.html>

### Architecture

- **Brute-force only** — no ANN index (HNSW, IVF, DiskANN planned for future)
- Vectors stored in **chunks** in shadow tables, read chunk-by-chunk during KNN
- Does not require all vectors in RAM (uses SQLite's I/O)
- `PRAGMA mmap_size` can accelerate KNN by memory-mapping the database

### Benchmarks (from author, Mac M1 Mini 8GB)

**100k vectors, stored on disk, average KNN query time:**

| Dimensions | float32 | bit (quantized) |
|---|---|---|
| 3072 | 214 ms | 11 ms |
| 1536 | 105 ms | ~6 ms |
| 768 | ~50 ms | ~4 ms |
| 384 | ~30 ms | ~3 ms |

**1M vectors (SIFT1M, 128-dim, in-memory):**

| Method | Build Time | Query Time |
|---|---|---|
| sqlite-vec static (in-memory) | 1 ms | 17 ms |
| sqlite-vec vec0 | ~4 s | 33 ms |
| Faiss (brute force) | 126 ms | 10 ms |
| NumPy | 0 ms | 136 ms |

### Practical Limits

| Scale | float32 | binary quantized |
|---|---|---|
| < 100k vectors | ✅ Sub-100ms for all dimensions | ✅ Excellent |
| 100k–500k vectors | ⚠️ Acceptable for dim ≤ 768 | ✅ Fast |
| 1M+ vectors | ❌ All float dims exceed 100ms target | ⚠️ ~124 ms for bit vectors |

### Quantization Benefits

- **Binary quantization**: 32× storage reduction, ~10× faster queries (source: docs/references/storage-backend/bibliography.md)
- Only ~5–10% quality loss with models trained for binary quantization
- Supported models: `mxbai-embed-large-v1`, `nomic-embed-text-v1.5`
- **Matryoshka embeddings**: Truncate dimensions with `vec_slice()` + `vec_normalize()`

### Current Limitations

1. **Pre-v1**: Expect breaking API changes
2. **No ANN index**: Brute-force only (tracked in [#25](https://github.com/asg017/sqlite-vec/issues/25))
3. **Single-threaded**: Relies on SQLite's single-writer model
4. **No ACID guarantees for concurrent vector writes**: Standard SQLite WAL mode applies
5. **Memory**: Large float32 vectors at scale need significant I/O or mmap

---

## 6. sqlite-vec Python Integration

**Source**: <https://alexgarcia.xyz/sqlite-vec/python.html>

### Installation

```bash
pip install sqlite-vec  # or: uv add sqlite-vec (see [[python-uv]])
```

### Loading the Extension

```python
import sqlite3
import sqlite_vec

db = sqlite3.connect(":memory:")
db.enable_load_extension(True)
sqlite_vec.load(db)
db.enable_load_extension(False)
```

### Working with Vectors

**From Python lists:**

```python
from sqlite_vec import serialize_float32

embedding = [0.1, 0.2, 0.3, 0.4]
db.execute('select vec_length(?)', [serialize_float32(embedding)])
```

**From NumPy arrays (zero-copy via Buffer protocol):**

```python
import numpy as np

embedding = np.array([0.1, 0.2, 0.3, 0.4])
db.execute("SELECT vec_length(?)", [embedding.astype(np.float32)])
```

### Requirements

- **Recommended**: SQLite ≥ 3.41 for LIMIT-based KNN
- **macOS caveat**: Default system Python blocks SQLite extensions. Use
  `brew install python` for Homebrew Python with extension support, or manage dependencies via [[python-uv]].
- **Alternative**: Use `pysqlite3` package for bundled up-to-date SQLite

---

## 7. SQLite FTS5 Overview

**Source**: <https://www.sqlite.org/fts5.html>

FTS5 is SQLite's built-in full-text search virtual table module. It provides
efficient text search over large document collections.

### Table Creation

```sql
CREATE VIRTUAL TABLE docs USING fts5(title, body);

-- With tokenizer configuration
CREATE VIRTUAL TABLE docs USING fts5(
  title, body,
  tokenize = 'porter unicode61',
  prefix = '2 3'
);
```

### Query Syntax

```sql
-- MATCH operator
SELECT * FROM docs WHERE docs MATCH 'search terms';

-- Table-valued function syntax
SELECT * FROM docs('search terms');

-- Boolean operators (in precedence order: NOT > AND > OR)
SELECT * FROM docs WHERE docs MATCH 'python AND (tutorial OR guide) NOT video';

-- Column filters
SELECT * FROM docs WHERE title MATCH 'sqlite';
SELECT * FROM docs WHERE docs MATCH 'body : vector search';

-- Prefix queries
SELECT * FROM docs WHERE docs MATCH 'embed*';

-- NEAR queries
SELECT * FROM docs WHERE docs MATCH 'NEAR(vector search, 5)';

-- Phrase queries
SELECT * FROM docs WHERE docs MATCH '"vector database"';
```

### Sorting by Relevance

```sql
-- Using the rank column (faster than bm25() directly)
SELECT * FROM docs WHERE docs MATCH 'query' ORDER BY rank;

-- Using bm25() with column weights
SELECT * FROM docs WHERE docs MATCH 'query'
ORDER BY bm25(docs, 10.0, 5.0);  -- title weight=10, body weight=5

-- Custom rank mapping per query
SELECT * FROM docs WHERE docs MATCH 'query'
  AND rank MATCH 'bm25(10.0, 5.0)'
ORDER BY rank;
```

### Key Options

| Option | Description |
|---|---|
| `tokenize` | Tokenizer selection (unicode61, ascii, porter, trigram) |
| `prefix` | Prefix index lengths for faster prefix queries |
| `content` | External content table or `''` for contentless |
| `content_rowid` | Rowid column name in external content table |
| `columnsize` | Store per-column token counts (default 1, set 0 to save space) |
| `detail` | Index detail level: `full`, `column`, or `none` |

---

## 8. FTS5 BM25 Ranking

**Source**: <https://www.sqlite.org/fts5.html#the_bm25_function>

### Algorithm

FTS5 implements the Okapi BM25 algorithm (see [[ir-evaluation-benchmarking]] for evaluation methodology). The score for document D and query Q:

```
BM25(D, Q) = -1 × Σ(i=1..nPhrase) IDF(qi) × f(qi,D) × (k1+1) / (f(qi,D) + k1 × (1 - b + b × |D|/avgdl))
```

Where:
- `nPhrase` = number of phrases in the query
- `|D|` = number of tokens in document D
- `avgdl` = average tokens across all documents
- `k1 = 1.2` (hardcoded)
- `b = 0.75` (hardcoded)

**IDF (Inverse Document Frequency):**

```
IDF(qi) = ln((N - n(qi) + 0.5) / (n(qi) + 0.5))
```

Where:
- `N` = total rows in FTS5 table
- `n(qi)` = rows containing phrase qi

**Important**: FTS5 multiplies by -1 so that **better matches have lower scores**.
This means `ORDER BY rank` (ascending) returns best results first (source: docs/references/storage-backend/bibliography.md).

### Column Weights

```sql
-- weight title=10, body=5, other columns default=1.0
SELECT * FROM docs WHERE docs MATCH ?
ORDER BY bm25(docs, 10.0, 5.0);
```

### Persistent Rank Configuration

```sql
-- Set default ranking for the table
INSERT INTO docs(docs, rank) VALUES('rank', 'bm25(10.0, 5.0)');
```

### Built-in Auxiliary Functions

| Function | Description |
|---|---|
| `bm25(table, w1, w2, ...)` | BM25 relevance score (lower = better match) |
| `highlight(table, col, open, close)` | Returns text with matches wrapped in markup |
| `snippet(table, col, open, close, ellip, max_tokens)` | Returns fragment with matches highlighted |

---

## 9. FTS5 Tokenizers

**Source**: <https://www.sqlite.org/fts5.html#tokenizers>

### Built-in Tokenizers

| Tokenizer | Description | Best For |
|---|---|---|
| **unicode61** (default) | Unicode 6.1 standard, case-insensitive, removes diacritics from Latin | General multilingual text |
| **ascii** | Non-ASCII chars are always token chars | ASCII-heavy content |
| **porter** | Wrapper; applies Porter stemming to another tokenizer | English text (corrected → correct) |
| **trigram** | Every 3-char sequence is a token | Substring matching, LIKE/GLOB |

### Configuration Examples

```sql
-- Porter stemmer on top of unicode61
CREATE VIRTUAL TABLE docs USING fts5(
  content, tokenize = 'porter unicode61'
);

-- Unicode61 with custom token characters
CREATE VIRTUAL TABLE docs USING fts5(
  content, tokenize = "unicode61 tokenchars '-_'"
);

-- Trigram for substring matching
CREATE VIRTUAL TABLE docs USING fts5(
  content, tokenize = 'trigram'
);
```

### Recommendation for RAG

For a RAG system processing English text:
- **`porter unicode61`** is the best default — it stems words and handles
  Unicode properly.
- Add `prefix='2 3'` if prefix queries are common.
- Consider `trigram` only if substring matching is needed.

---

## 10. FTS5 External Content Tables

**Source**: <https://www.sqlite.org/fts5.html#external_content_and_contentless_tables>

### Contentless Tables (Index Only)

```sql
CREATE VIRTUAL TABLE ft USING fts5(content, content='');
```

- No column values stored, only the FTS index
- Significantly smaller database size
- Reading columns returns NULL (except rowid)
- Cannot UPDATE or DELETE without 'delete' command

### Contentless-Delete Tables (Recommended)

```sql
CREATE VIRTUAL TABLE ft USING fts5(
  content, content='', contentless_delete=1
);
```

- Supports DELETE and UPDATE (all columns must be provided)
- Recommended over plain contentless tables for new code

### External Content Tables

```sql
CREATE TABLE documents(id INTEGER PRIMARY KEY, title TEXT, body TEXT);

CREATE VIRTUAL TABLE docs_fts USING fts5(
  title, body,
  content='documents', content_rowid='id'
);
```

Keep in sync with triggers:

```sql
CREATE TRIGGER docs_ai AFTER INSERT ON documents BEGIN
  INSERT INTO docs_fts(rowid, title, body) VALUES(new.id, new.title, new.body);
END;
CREATE TRIGGER docs_ad AFTER DELETE ON documents BEGIN
  INSERT INTO docs_fts(docs_fts, rowid, title, body)
    VALUES('delete', old.id, old.title, old.body);
END;
CREATE TRIGGER docs_au AFTER UPDATE ON documents BEGIN
  INSERT INTO docs_fts(docs_fts, rowid, title, body)
    VALUES('delete', old.id, old.title, old.body);
  INSERT INTO docs_fts(rowid, title, body) VALUES(new.id, new.title, new.body);
END;
```

### FTS5 Maintenance Commands

```sql
INSERT INTO ft(ft) VALUES('rebuild');     -- Rebuild index from content table
INSERT INTO ft(ft) VALUES('optimize');    -- Merge all b-trees into one
INSERT INTO ft(ft, rank) VALUES('merge', 500);  -- Incremental merge
INSERT INTO ft(ft) VALUES('integrity-check');    -- Verify consistency
```

---

## 11. Reciprocal Rank Fusion (RRF)

**Source**: Cormack, G.V., Clarke, C.L.A., & Buettcher, S. (2009). "Reciprocal
Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods."
SIGIR '09, pp. 758–759. ACM. DOI: `10.1145/1571941.1572114`

### Algorithm

Given multiple ranked lists for the same query, as applied in [[rag-research-compendium]], each document receives a fused
score:

```
RRF_score(d) = Σ(i=1..n) 1 / (k + rank_i(d))
```

Where:
- `d` = document
- `n` = number of ranking systems (e.g., 2 for BM25 + vector)
- `k` = constant (recommended: **60**)
- `rank_i(d)` = position of document d in system i's ranking (1-based)
- If d is absent from system i's results, it contributes 0

### Properties

1. **Rank-based, not score-based**: Uses ranking positions, not raw scores
2. **No normalization needed**: BM25 and cosine distance have different scales — RRF sidesteps this entirely
3. **Parameter k**: Controls how much influence lower-ranked items have
   - k=60 is the paper's recommendation and widely adopted default
   - Higher k → more uniform weighting across ranks
   - Lower k → top-ranked items dominate more
4. **Simple to implement**: No training, no calibration, no learned weights (source: docs/references/storage-backend/bibliography.md)
5. **Proven effective**: Outperforms Condorcet, CombMNZ, and individual rank learning methods (source: docs/references/storage-backend/bibliography.md)

### Python Implementation

```python
def reciprocal_rank_fusion(
    ranked_lists: list[list[int]],  # list of ranked doc_id lists
    k: int = 60
) -> list[tuple[int, float]]:
    """Fuse multiple ranked lists using RRF."""
    scores: dict[int, float] = {}
    for ranked_list in ranked_lists:
        for rank, doc_id in enumerate(ranked_list, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

### Example

Document A: rank 3 in BM25, rank 10 in vector search:

```
RRF(A) = 1/(60+3) + 1/(60+10) = 1/63 + 1/70 ≈ 0.01587 + 0.01429 = 0.03016
```

Document B: rank 1 in BM25, absent in vector search:

```
RRF(B) = 1/(60+1) + 0 = 1/61 ≈ 0.01639
```

Document A ranks higher because it appears in **both** lists.

---

## 12. Hybrid Search Architecture

### Schema Design for rag4you-cli

```sql
-- Main document/chunk storage
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT,  -- JSON
    created_at TEXT DEFAULT (datetime('now'))
);

-- FTS5 index (external content, synced via triggers)
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    content,
    content='chunks',
    content_rowid='id',
    tokenize='porter unicode61'
);

-- Vector index (dimension must match active [[embedding-models-research]] model)
CREATE VIRTUAL TABLE chunks_vec USING vec0(
    chunk_id INTEGER PRIMARY KEY,
    embedding float[768] distance_metric=cosine
);
```

### Hybrid Query Pattern (SQL + Python RRF)

**Step 1: FTS5 query (keyword/lexical search)**

```sql
SELECT rowid, rank as bm25_score
FROM chunks_fts
WHERE chunks_fts MATCH :query
ORDER BY rank
LIMIT :n;
```

**Step 2: Vector query (semantic search)**

```sql
SELECT chunk_id, distance
FROM chunks_vec
WHERE embedding MATCH :query_embedding
  AND k = :n;
```

**Step 3: RRF fusion in Python**

```python
def hybrid_search(query: str, query_embedding: bytes, n: int = 20, k: int = 60):
    # Get FTS5 results (ranked by BM25)
    fts_results = db.execute(
        "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY rank LIMIT ?",
        [query, n]
    ).fetchall()

    # Get vector results (ranked by distance, ascending)
    vec_results = db.execute(
        "SELECT chunk_id FROM chunks_vec WHERE embedding MATCH ? AND k = ?",
        [query_embedding, n]
    ).fetchall()

    # Apply RRF
    fts_ids = [row[0] for row in fts_results]
    vec_ids = [row[0] for row in vec_results]
    fused = reciprocal_rank_fusion([fts_ids, vec_ids], k=k)

    # Fetch full chunk data for top results
    top_ids = [doc_id for doc_id, score in fused[:n]]
    # ... fetch from chunks table
```

### Alternative: Pure SQL Approach (Simpler, Less Flexible)

```sql
WITH fts_ranked AS (
    SELECT rowid as id, ROW_NUMBER() OVER (ORDER BY rank) as fts_rank
    FROM chunks_fts WHERE chunks_fts MATCH :query
    LIMIT 50
),
vec_ranked AS (
    SELECT chunk_id as id, ROW_NUMBER() OVER (ORDER BY distance) as vec_rank
    FROM chunks_vec WHERE embedding MATCH :query_embedding AND k = 50
),
fused AS (
    SELECT
        COALESCE(f.id, v.id) as id,
        COALESCE(1.0 / (60 + f.fts_rank), 0) +
        COALESCE(1.0 / (60 + v.vec_rank), 0) as rrf_score
    FROM fts_ranked f
    FULL OUTER JOIN vec_ranked v ON f.id = v.id
)
SELECT c.*, fused.rrf_score
FROM fused
JOIN chunks c ON c.id = fused.id
ORDER BY fused.rrf_score DESC
LIMIT 10;
```

> **Note**: SQLite does not natively support `FULL OUTER JOIN`. Use
> `LEFT JOIN` + `UNION ALL` with `WHERE ... IS NULL` as a workaround.

### Practical Pure-SQLite Workaround

```sql
WITH fts_ranked AS (
    SELECT rowid as id, ROW_NUMBER() OVER (ORDER BY rank) as fts_rank
    FROM chunks_fts WHERE chunks_fts MATCH :query LIMIT 50
),
vec_ranked AS (
    SELECT chunk_id as id, ROW_NUMBER() OVER (ORDER BY distance) as vec_rank
    FROM chunks_vec WHERE embedding MATCH :query_embedding AND k = 50
),
all_ids AS (
    SELECT id FROM fts_ranked
    UNION
    SELECT id FROM vec_ranked
),
fused AS (
    SELECT
        a.id,
        COALESCE(1.0 / (60 + f.fts_rank), 0) +
        COALESCE(1.0 / (60 + v.vec_rank), 0) as rrf_score
    FROM all_ids a
    LEFT JOIN fts_ranked f ON a.id = f.id
    LEFT JOIN vec_ranked v ON a.id = v.id
)
SELECT c.*, fused.rrf_score
FROM fused
JOIN chunks c ON c.id = fused.id
ORDER BY fused.rrf_score DESC
LIMIT 10;
```

---

## 13. SQLite as a Vector Database

### Advantages for Local RAG

| Advantage | Detail |
|---|---|
| **Zero infrastructure** | Single file, no server, no Docker |
| **Portable** | Database file can be copied, backed up, version-controlled |
| **Unified storage** | Vectors, FTS index, metadata, and content in one file |
| **SQL interface** | Standard querying, JOINs, aggregations alongside vector search |
| **Mature ecosystem** | WAL mode, PRAGMA optimizations, backup APIs |
| **Tiny footprint** | sqlite-vec binary is ~100s of KB |

### Limitations vs Dedicated Vector DBs

| Limitation | Impact | Mitigation |
|---|---|---|
| No ANN index | O(N) per query | Binary quantization, Matryoshka, partitions |
| Single writer | No concurrent inserts | WAL mode for concurrent reads |
| No distributed | Single machine only | Fine for local/desktop RAG |
| Scale ceiling | ~100k float32 vectors for <100ms | Use bit vectors for ~10× speed |

### Scale Guidance

| Dataset Size | Recommendation |
|---|---|
| < 10k vectors | sqlite-vec is ideal; any dimension works |
| 10k–100k vectors | sqlite-vec with cosine distance; consider binary quantization for large dims |
| 100k–500k vectors | Binary quantization strongly recommended; partition by user/doc |
| 500k–1M vectors | At the edge; evaluate latency requirements carefully |
| > 1M vectors | Consider dedicated vector DB or wait for ANN support |

### Performance Tuning

```sql
-- Enable memory-mapping for faster I/O
PRAGMA mmap_size = 268435456;  -- 256 MB

-- WAL mode for concurrent reads during writes
PRAGMA journal_mode = WAL;

-- Increase cache for vector operations
PRAGMA cache_size = -64000;  -- 64 MB
```

---

## 14. Design Decisions for rag4you-cli

Based on this research, the following design choices are recommended for the
rag4you-cli hybrid search backend:

### Storage Architecture

1. **Single SQLite database file** per knowledge base
2. **Three virtual tables**: chunks (regular), chunks_fts (FTS5), chunks_vec (vec0)
3. **External content FTS5** pointing to chunks table, synced with triggers
4. **Cosine distance** as default metric (most embedding models are trained for it)

### Search Strategy

1. **Dual retrieval**: FTS5 for lexical, vec0 for semantic
2. **RRF fusion** with k=60 (paper default) in Python (more flexible than pure SQL)
3. **Retrieve N=50 from each system**, fuse, return top 10–20 to LLM context

### Tokenizer Choice

- **`porter unicode61`** for FTS5 — English stemming with Unicode support
- Add prefix indexes `prefix='2 3'` for autocomplete-style queries

### Embedding Strategy

- Store `float32` vectors by default
- Support binary quantization as opt-in for large collections
- Design vector columns to be configurable per collection. The default model (bge-small) uses 384 dimensions; medium tier (bge-base) uses 768; large tier (bge-large) uses 1024. The vec0 table dimension MUST match the active embedding model (see [[embedding-models-research]]).
- Keep embedding model configurable (not hardcoded)

### Python Integration

- Use `sqlite_vec.load(db)` to load extension
- Use `serialize_float32()` for list→blob conversion
- Use NumPy `.astype(np.float32)` for array→blob conversion
- Require SQLite ≥ 3.41 for LIMIT-based KNN queries
- Use [[tiktoken]] for accurate token counting when chunking content before embedding

---

## Source Index

| # | Source | URL | Content |
|---|---|---|---|
| 1 | sqlite-vec homepage | <https://alexgarcia.xyz/sqlite-vec/> | Overview, installation |
| 2 | sqlite-vec GitHub | <https://github.com/asg017/sqlite-vec> | README, sample usage |
| 3 | sqlite-vec API Reference | <https://alexgarcia.xyz/sqlite-vec/api-reference.html> | All SQL functions |
| 4 | sqlite-vec vec0 docs | <https://alexgarcia.xyz/sqlite-vec/features/vec0.html> | Metadata, partitions, auxiliary columns |
| 5 | sqlite-vec KNN docs | <https://alexgarcia.xyz/sqlite-vec/features/knn.html> | KNN query patterns |
| 6 | sqlite-vec Python docs | <https://alexgarcia.xyz/sqlite-vec/python.html> | Python integration guide |
| 7 | sqlite-vec v0.1.0 release blog | <https://alexgarcia.xyz/blog/2024/sqlite-vec-stable-release/index.html> | Benchmarks, architecture, limitations |
| 8 | sqlite-vec design blog | <https://alexgarcia.xyz/blog/2024/building-new-vector-search-sqlite/index.html> | Design rationale, sqlite-vss comparison |
| 9 | SQLite FTS5 docs | <https://www.sqlite.org/fts5.html> | Complete FTS5 reference |
| 10 | RRF paper | Cormack et al. SIGIR 2009, DOI: 10.1145/1571941.1572114 | Algorithm, k=60 recommendation |

## Related pages

- [[embedding-models-research]]
- [[rag-research-compendium]]
- [[ir-evaluation-benchmarking]]
- [[python-uv]]
- [[tiktoken]]
- [[pydantic-v2]]
