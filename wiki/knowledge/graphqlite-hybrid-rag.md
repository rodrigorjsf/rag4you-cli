# GraphQLite Hybrid RAG

**Summary**: GraphQLite is a SQLite extension that adds graph database capabilities via Cypher queries. Combined with sqlite-vec and FTS5, it enables a triple-hybrid RAG stack (vector + keyword + graph) in a single SQLite database for multi-hop reasoning and entity-aware retrieval.
**Sources**: docs/raw/graphqlite-hybrid-rag.md, docs/raw/graphqlite/graphqlite-extended-reference.md, docs/raw/graphqlite/graphqlite-full-documentation.md, github.com/colliery-io/graphqlite (v0.4.4)
**Last updated**: 2025-07-24
---

## Overview

GraphQLite (source: github.com/colliery-io/graphqlite) adds a full graph database layer to SQLite via a Cypher query language transpiler. It runs on the same SQLite connection as [[sqlite-vec-fts5-hybrid-search|sqlite-vec and FTS5]], enabling a **triple-hybrid RAG architecture** where vector search, keyword search, and graph traversal all operate on the same database file.

This is significant for rag4you-cli because it enables:
- **Multi-hop reasoning** — follow entity relationships across documents
- **Community-based retrieval** — cluster related entities for topic-level context
- **Entity importance ranking** — PageRank scores boost authoritative entities
- **Co-occurrence graphs** — connect concepts that appear together in chunks

## Architecture

GraphQLite works as a **transpiler**, not a separate database engine (source: graphqlite-full-documentation.md):

```
Cypher Query → Lexer → Parser (Bison GLR) → AST → SQL Generator → SQLite Engine → JSON Results
```

This means:
- No separate graph database process
- All data lives in standard SQLite tables (EAV schema)
- Full ACID transactions from SQLite
- Compatible with all other SQLite extensions (sqlite-vec, FTS5)
- Translation overhead: ~1ms per simple query

### Why Transpiler (Not Custom Engine)

- **Durability/atomicity**: Uses SQLite's WAL and journalling machinery
- **Standard tooling**: Underlying tables are plain SQLite — inspectable with any SQLite tool
- **Proven query planner**: Generated SQL benefits from SQLite's optimizer (source: graphqlite-full-documentation.md, Architecture section)

### Internal Schema (Auto-created)

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

### CSR Graph Cache

For algorithm execution, GraphQLite builds a Compressed Sparse Row (CSR) representation in memory:
- O(V + E) space, O(1) neighbor access
- Must call `gql_load_graph()` before algorithms
- Must call `gql_reload_graph()` after structural changes
- Free with `gql_unload_graph()` when done
- Memory formula: ~(20N + 8E) bytes

| Nodes | Edges | CSR Memory |
|-------|-------|------------|
| 10K | 50K | ~600KB |
| 100K | 500K | ~6MB |
| 1M | 5M | ~60MB |

## Performance Benchmarks (from Official PDF)

Measured on single-core MacBook, `:memory:` database (source: graphqlite-full-documentation.md):

| Operation | Typical Latency |
|-----------|----------------|
| Extension loading (schema init) | ~5ms (once) |
| Simple CREATE | 0.5–1ms |
| Simple MATCH (10 nodes) | 0.5–2ms |
| MATCH with relationship (100 rels) | 1–5ms |
| gql_load_graph() 100K nodes | ~50–100ms |
| PageRank 100K nodes | ~180ms |
| PageRank 1M nodes | ~38s |
| Bulk insert (vs Cypher CREATE) | 100–500x faster |

### Scaling Characteristics

| Scale | Behavior | Recommendation |
|-------|----------|----------------|
| < 10K nodes | Sub-1ms queries | Cypher CREATE is fine |
| 10K–100K nodes | Property lookups 5–50ms | Use bulk insert |
| 100K–1M nodes | Full scan expensive | CSR cache mandatory for algorithms |
| > 1M nodes | CSR uses 60MB+ | Consider partitioning, pre-compute centrality |

### GraphRAG vs Vector RAG Accuracy (External Benchmarks)

Recent independent benchmarks (Diffbot/FalkorDB 2025) show:
- **GraphRAG**: >90% accuracy on schema-bound/multi-hop queries
- **Vector RAG**: 0% accuracy on schema-bound queries (cannot follow relationships)
- **Hybrid (vector + FTS)**: ~40% improvement over vector-only on mixed workloads
- Sub-100ms query times for typical hybrid RAG on commodity hardware

## Graph Algorithms (18 Built-in)

| Category | Algorithms | RAG Relevance |
|----------|-----------|---------------|
| Centrality | PageRank, Degree, Betweenness, Closeness, Eigenvector | Entity importance ranking |
| Community | Louvain, Leiden, Label Propagation | Topic clustering |
| Components | Weakly/Strongly Connected | Document grouping |
| Pathfinding | Dijkstra, A*, All-Pairs | Multi-hop reasoning |
| Traversal | BFS, DFS | Relationship exploration |
| Similarity | Node Similarity, KNN | Entity deduplication |
| Clustering | Triangle Count | Local structure analysis |

### Key Algorithms for RAG

**PageRank** — Rank entities by importance in the knowledge graph. Boost retrieval scores for chunks mentioning high-PageRank entities:

```python
pr_results = graph.pagerank(damping=0.85, iterations=30)
entity_importance = {r['user_id']: r['score'] for r in pr_results}
```

**Louvain Community Detection** — Group entities into topic communities. Use for topic-level retrieval expansion:

```python
communities = graph.louvain(resolution=0.5)  # larger communities
# resolution=1.0 for finer-grained communities
```

**Shortest Path** — Find connection paths between entities for multi-hop reasoning:

```python
path = graph.shortest_path("entity_A", "entity_B")
```

## GraphRAG Pipeline

The official GraphQLite example (`examples/llm-graphrag/`) demonstrates a complete GraphRAG system:

### Ingestion

1. **Chunk documents** and generate [[embedding-models-research|embeddings]] via sentence-transformers
2. **Extract entities** via spaCy NER (PERSON, ORG, LOCATION, etc.)
3. **Create graph nodes**: Document, Chunk, Entity
4. **Create graph edges**: HAS_CHUNK, MENTIONS, COOCCURS (entities co-occurring in same chunk)
5. **Store embeddings** in sqlite-vec virtual table

```cypher
CREATE (d:Document {title: $title})
CREATE (c:Chunk {text: $text, index: $idx})
CREATE (e:Entity {name: $name, type: $type})
CREATE (d)-[:HAS_CHUNK]->(c)
CREATE (c)-[:MENTIONS]->(e)
CREATE (e1)-[:COOCCURS {weight: $weight}]->(e2)
```

### Hybrid Retrieval (Three Strategies)

#### Strategy 1: Vector Search (Semantic)

```python
# KNN via sqlite-vec
chunks = conn.execute("""
    SELECT chunk_id, distance FROM chunk_embeddings
    WHERE embedding MATCH ? ORDER BY distance LIMIT ?
""", (query_emb_bytes, top_k)).fetchall()
```

#### Strategy 2: Graph Traversal (Multi-hop)

```cypher
-- Find related chunks via entity co-occurrence (2 hops)
MATCH (c:Chunk)-[:MENTIONS]->(e:Entity)-[:COOCCURS]->(e2:Entity)<-[:MENTIONS]-(c2:Chunk)
WHERE c.id IN $seed_chunk_ids
RETURN DISTINCT c2.id, c2.text, count(*) as relevance
ORDER BY relevance DESC LIMIT 10
```

#### Strategy 3: Community Expansion (Topic-level)

```python
# Detect communities, then expand retrieval to same-community entities
communities = graph.louvain(resolution=1.0)
query_entities = extract_entities(query)
community_chunks = expand_by_community(query_entities, communities)
```

#### Combined Ranking

```python
def hybrid_retrieve(query, conn, graph, model, top_k=10):
    query_emb = model.encode([query], normalize_embeddings=True)

    vector_results = vector_search(conn, query_emb, k=top_k)
    graph_results = graph_traverse(conn, vector_results, hops=2)
    community_results = community_expand(graph, vector_results)

    # Deduplicate and fuse scores (RRF or weighted combination)
    all_results = deduplicate(vector_results + graph_results + community_results)
    return rank_by_fusion(all_results)[:top_k]
```

## Integration with rag4you-cli

### Triple-Hybrid Architecture

```
┌─────────────────────────────────────────────────────┐
│              rag4you-cli RAG Engine                  │
├─────────────────────────────────────────────────────┤
│ sqlite-vec     │ FTS5           │ GraphQLite        │
│ (Vector)       │ (Keyword)      │ (Graph)           │
│                │                │                   │
│ Semantic KNN   │ BM25 scoring   │ Entity traversal  │
│ Cosine sim     │ Term matching  │ Community detect  │
│ ANN search     │ Full-text      │ PageRank boost    │
├─────────────────────────────────────────────────────┤
│           Single SQLite Database File               │
│     All extensions loaded on same connection        │
└─────────────────────────────────────────────────────┘
```

### Setup Pattern

```python
import sqlite3
import graphqlite
import sqlite_vec

conn = sqlite3.connect("rag4you.db")
graphqlite.load(conn)   # Load GraphQLite FIRST
sqlite_vec.load(conn)   # Then sqlite-vec
# FTS5 is built-in to SQLite — no loading needed
```

### Dependencies

```toml
[project]
dependencies = [
    "graphqlite",        # Graph extension
    "sqlite-vec",        # Vector extension
    "sentence-transformers>=2.2.0",
    "spacy>=3.7.0",      # Entity extraction
]
```

### Entity Extraction During Ingestion

```python
import spacy
nlp = spacy.load("en_core_web_sm")  # 12MB model

def extract_and_link_entities(chunk_text: str, chunk_id: str, conn):
    doc = nlp(chunk_text)
    entities = [(ent.text.lower(), ent.label_) for ent in doc.ents]

    for name, label in entities:
        # Create or merge entity node
        conn.execute("""
            MERGE (e:Entity {name: $name})
            SET e.type = $type
        """, {"name": name, "type": label})

        # Link chunk to entity
        conn.execute("""
            MATCH (c:Chunk {id: $chunk_id}), (e:Entity {name: $name})
            CREATE (c)-[:MENTIONS]->(e)
        """, {"chunk_id": chunk_id, "name": name})

    # Create co-occurrence edges between entities in same chunk
    for i, (name1, _) in enumerate(entities):
        for name2, _ in entities[i+1:]:
            conn.execute("""
                MATCH (e1:Entity {name: $n1}), (e2:Entity {name: $n2})
                MERGE (e1)-[r:COOCCURS]->(e2)
                SET r.weight = coalesce(r.weight, 0) + 1
            """, {"n1": name1, "n2": name2})
```

### Combining with TurboQuant

For maximum efficiency, combine [[turboquant-vector-quantization|TurboQuant]] compression with GraphQLite graph enhancement:

1. **TurboQuant** compresses embedding vectors (5.3x at 95% recall)
2. **GraphQLite** adds entity relationships for multi-hop reasoning
3. **FTS5** provides keyword fallback for exact term matching
4. **RRF fusion** combines all three retrieval signals

This combination addresses different failure modes:
- Vector search fails on: exact names, acronyms, rare terms → FTS5 covers
- Keyword search fails on: paraphrases, semantic similarity → Vector covers
- Both fail on: multi-hop reasoning, implicit connections → Graph covers

## Considerations

- **spaCy model selection**: `en_core_web_sm` (12MB, fast) vs `en_core_web_lg` (560MB, better NER)
- **Entity resolution**: Normalize entity names (lowercase, strip whitespace) to avoid duplicates
- **Graph scale**: CSR cache is in-memory; for very large graphs, use higher Louvain resolution
- **Incremental updates**: New documents need entity extraction + graph edge creation
- **Loading order**: GraphQLite must load before sqlite-vec on the same connection
- **Bulk insert**: Use `insert_nodes_bulk()` / `insert_edges_bulk()` for 100-500x speedup over Cypher CREATE during ingestion
- **WAL mode**: Essential for disk-backed databases with concurrent access
- **Commit between loads**: Commit after loading each extension to ensure schema visibility

## Python API Quick Reference (from Official Docs)

```python
from graphqlite import Graph

g = Graph("rag4you.db")    # File-backed, or ":memory:"

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

# Bulk operations (100-500x faster than individual Cypher CREATE)
id_map = g.insert_nodes_bulk([(id, props, label), ...])
g.insert_edges_bulk([(src, tgt, props, type), ...], id_map)

# Algorithms (requires gql_load_graph() first)
g.pagerank(damping=0.85, iterations=20)
g.community_detection(iterations=10)
g.shortest_path(source_id, target_id)
```

## Installation Options

| Method | Command | Notes |
|--------|---------|-------|
| Standard | `pip install graphqlite` | macOS, Linux, Windows |
| With Leiden | `pip install graphqlite[leiden]` | Requires graspologic |
| With rustworkx | `pip install graphqlite[rustworkx]` | Graph export support |
| Rust | `cargo add graphqlite` | All platforms |

## Related pages

- [[sqlite-vec-fts5-hybrid-search]]
- [[turboquant-vector-quantization]]
- [[rag-research-compendium]]
- [[embedding-models-research]]
