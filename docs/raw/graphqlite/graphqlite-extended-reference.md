# GraphQLite — Extended Documentation Reference (from Official PDF v0.4.4)

## Source

- **PDF**: docs/raw/graphqlite/GraphQLite-documentation.pdf
- **Extracted**: docs/raw/graphqlite/graphqlite-full-documentation.md (13,089 lines)
- **Version**: 0.4.4 (MIT License)
- **Date**: 19/04/2026
- **URL**: https://colliery-io.github.io/graphqlite/latest/

---

## Architecture: Transpiler Design

GraphQLite adds Cypher query language support to SQLite via a transpiler pipeline:

```
Cypher String → Parser (Bison GLR) → AST → Transformer (SQL Generator) → SQLite Executor → Result Formatter (JSON)
```

### Why Transpiler, Not Custom Engine

- **Durability/atomicity**: Uses SQLite's WAL and journalling machinery
- **Standard tooling**: Underlying tables are plain SQLite — inspectable with any SQLite tool
- **Proven query planner**: Generated SQL benefits from SQLite's optimizer
- **Trade-off**: Translation overhead (~1ms for simple queries) + EAV join impedance

### Parser Details

- Bison GLR grammar (`cypher_gram.y`) with Flex scanner (`cypher_scanner.l`)
- GLR needed for Cypher's syntactic ambiguities (e.g., `(n)` is both expression and node pattern)
- Known conflicts: `%expect 4` shift/reduce, `%expect-rr 3` reduce/reduce (intentional)
- Error messages include position information

---

## Storage Model: Entity-Attribute-Value (EAV)

### Core Tables (auto-created on first load)

```sql
nodes        (id INTEGER PRIMARY KEY, user_id TEXT UNIQUE, created_at)
edges        (id INTEGER PRIMARY KEY, source_id INTEGER, target_id INTEGER, type TEXT)
node_labels  (node_id INTEGER, label TEXT)
property_keys (id INTEGER PRIMARY KEY, key TEXT UNIQUE)

-- Typed property tables (one per type)
node_props_text    (node_id, key_id, value TEXT)
node_props_int     (node_id, key_id, value INTEGER)
node_props_real    (node_id, key_id, value REAL)
node_props_bool    (node_id, key_id, value INTEGER)
node_props_json    (node_id, key_id, value TEXT)
edge_props_text    (edge_id, key_id, value TEXT)
edge_props_int     (edge_id, key_id, value INTEGER)
edge_props_real    (edge_id, key_id, value REAL)
```

### Key Indexes

- `idx_node_labels_label` — `(label, node_id)` for label filtering
- `idx_node_props_int_key_value` — `(key_id, value, node_id)` covering index
- `idx_edges_source` — `(source_id, type)` for outgoing traversal
- `idx_edges_target` — `(target_id, type)` for incoming traversal

---

## Performance Characteristics

### Benchmark Reference (in-memory, single-core MacBook)

| Operation | Typical Latency |
|-----------|----------------|
| Extension loading (schema init) | ~5ms (once per connection) |
| Simple CREATE (:Person {name: 'Alice'}) | 0.5–1ms |
| Simple MATCH (n:Person) RETURN (10 nodes) | 0.5–2ms |
| MATCH (a)-[:KNOWS]->(b) (100 relationships) | 1–5ms |
| Bulk insert via insert_nodes_bulk() | 100–500x faster than Cypher CREATE |
| gql_load_graph() on 100K nodes/edges | ~50–100ms |
| PageRank on 100K nodes | ~180ms |
| PageRank on 1M nodes | ~38s |

### Scaling Characteristics

| Scale | Behavior |
|-------|----------|
| < 10K nodes | Sub-1ms queries; EAV fits in SQLite page cache |
| 10K–100K nodes | Property lookups 5–50ms; bulk insert worthwhile |
| 100K–1M nodes | CSR cache mandatory for algorithms; full scan expensive |
| > 1M nodes | CSR uses 60MB+ heap; consider pre-computing centrality |

### CSR Graph Cache Memory

Formula: ~(20N + 8E) bytes

| Nodes | Edges | Memory |
|-------|-------|--------|
| 10K | 50K | ~600KB |
| 100K | 500K | ~6MB |
| 1M | 5M | ~60MB |

---

## Python API Reference (Key Methods)

### Graph Class

```python
from graphqlite import Graph

g = Graph("path.db")           # File-backed
g = Graph(":memory:")          # In-memory

# Node operations
g.upsert_node(id, properties, label="Label")
g.get_node(id) -> dict
g.get_all_nodes(label="Label") -> list
g.node_degree(id) -> int

# Edge operations
g.upsert_edge(source_id, target_id, properties, rel_type="TYPE")
g.has_edge(source_id, target_id) -> bool
g.get_neighbors(id) -> list

# Querying
g.query("MATCH ... RETURN ...", params={}) -> list[dict]
g.stats() -> {"nodes": int, "edges": int}

# Bulk operations (100-500x faster)
id_map = g.insert_nodes_bulk([(id, props, label), ...])
g.insert_edges_bulk([(src, tgt, props, type), ...], id_map)

# Algorithms (requires gql_load_graph() first)
g.pagerank(damping=0.85, iterations=20)
g.community_detection(iterations=10)
g.shortest_path(source_id, target_id)
```

### Connection Class

```python
from graphqlite import connect

conn = connect("path.db")
conn.cypher("MATCH ...", params={})  # Parameterized queries
conn.sqlite_connection              # Access raw sqlite3.Connection
```

### Loading with Other Extensions

```python
import sqlite3, graphqlite, sqlite_vec

conn = sqlite3.connect("rag.db")
graphqlite.load(conn)    # MUST load GraphQLite FIRST
sqlite_vec.load(conn)    # Then other extensions
# FTS5 is built-in — no loading needed
```

Or via Graph API:
```python
g = graphqlite.Graph("rag.db")
raw_conn = g.connection.sqlite_connection
sqlite_vec.load(raw_conn)
```

---

## Official GraphRAG Tutorial (from PDF)

### Complete Pipeline Steps

1. **Chunk documents** with word-based overlap
2. **Extract entities** via spaCy NER
3. **Create graph**: Document → Chunk → Entity nodes; HAS_CHUNK, MENTIONS, COOCCURS edges
4. **Store embeddings** in sqlite-vec virtual table
5. **Retrieve**: Vector search → Entity lookup → Graph expansion → Combined context
6. **Enhance**: PageRank for entity importance, Louvain for community expansion

### Entity Extraction Pattern

```python
import spacy
nlp = spacy.load("en_core_web_sm")

def extract_entities(text):
    doc = nlp(text)
    return [(ent.text.lower(), ent.label_) for ent in doc.ents]
```

### GraphRAG Retrieval Function

```python
def graphrag_retrieve(g, conn, query, k_chunks=5, expand_hops=2):
    # 1. Vector search for semantically similar chunks
    chunk_ids = vector_search(conn, query_emb, k=k_chunks)

    # 2. Entity lookup via graph
    entities = set()
    for chunk_id in chunk_ids:
        rows = g.connection.cypher(
            "MATCH (c:Chunk {id: $chunk_id})-[:MENTIONS]->(e:Entity) RETURN e.name",
            {"chunk_id": chunk_id}
        )
        entities.update(row["name"] for row in rows)

    # 3. Graph expansion — find related entities
    related = set()
    for entity_name in entities:
        rows = g.connection.cypher(
            "MATCH (e:Entity {id: $eid})-[*1..$hops]-(r:Entity) RETURN DISTINCT r.name",
            {"eid": entity_node_id(entity_name), "hops": expand_hops}
        )
        related.update(row["name"] for row in rows)

    return {"chunks": chunk_texts, "entities": entities, "related": related}
```

### PageRank-Boosted Retrieval

```python
def get_important_entities(g, top_k=20):
    g.connection.cypher("RETURN gql_load_graph()")
    results = g.pagerank(damping=0.85, iterations=20)
    return [r["user_id"] for r in sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]]
```

### Community-Based Retrieval

```python
def get_entity_communities(g):
    g.connection.cypher("RETURN gql_load_graph()")
    results = g.community_detection(iterations=10)
    return {r["user_id"]: r["community"] for r in results}
```

---

## Graph Algorithms (18 Built-in)

| Category | Algorithms | RAG Application |
|----------|-----------|-----------------|
| Centrality | PageRank, Degree, Betweenness, Closeness, Eigenvector | Entity importance ranking |
| Community | Louvain, Leiden, Label Propagation | Topic clustering, query routing |
| Components | Weakly/Strongly Connected | Document grouping |
| Pathfinding | Dijkstra, A*, All-Pairs | Multi-hop reasoning |
| Traversal | BFS, DFS (with max_depth) | Relationship exploration |
| Similarity | Node Similarity, KNN | Entity deduplication |
| Clustering | Triangle Count | Local structure analysis |

### Algorithm Loading

```python
# Must call before any algorithm
g.connection.cypher("RETURN gql_load_graph()")

# After structural changes, reload
g.connection.cypher("RETURN gql_reload_graph()")

# Free memory when done
g.connection.cypher("RETURN gql_unload_graph()")
```

---

## Official Example: examples/llm-graphrag/

The repository includes a production-grade GraphRAG implementation:

```bash
cd examples/llm-graphrag
uv sync
uv run python ingest.py    # Ingests HotpotQA multi-hop dataset
uv run python rag.py       # Interactive query mode
```

### Dependencies

```toml
[project]
name = "llm-graphrag"
requires-python = ">=3.10"
dependencies = [
    "graphqlite",
    "sqlite-vec",
    "numpy>=1.21.0",
    "sentence-transformers>=2.2.0",
    "httpx>=0.25.0",
    "spacy>=3.7.0",
]
```

### Features

- Ingests ~10,000 Wikipedia article chunks from HotpotQA
- Entity co-occurrence graph construction
- Multi-hop question answering
- Uses Ollama for local LLM inference (no API keys)
- Demonstrates cases where plain vector RAG fails but GraphRAG succeeds

---

## Installation Options

| Method | Command | Platforms |
|--------|---------|-----------|
| Python (recommended) | `pip install graphqlite` | macOS, Linux, Windows |
| With Leiden | `pip install graphqlite[leiden]` | Requires graspologic |
| With rustworkx | `pip install graphqlite[rustworkx]` | Graph export support |
| Rust | `cargo add graphqlite` | All platforms |
| From source | `make extension` | Requires GCC/Clang, Bison 3.0+, Flex 2.6+ |

---

## Key Considerations for rag4you-cli

1. **Loading order matters**: GraphQLite must load FIRST (creates schema), then sqlite-vec
2. **CSR cache management**: Must call `gql_load_graph()` before algorithms, `gql_reload_graph()` after structural changes
3. **Bulk insert for ingestion**: 100-500x faster than individual Cypher CREATE
4. **spaCy model**: `en_core_web_sm` (12MB) for speed, `en_core_web_lg` (560MB) for better NER
5. **Memory**: CSR cache uses ~6MB for 100K nodes/500K edges
6. **WAL mode**: Essential for disk-backed databases with concurrent access
7. **Commit between loads**: Commit after loading each extension to ensure schema visibility
