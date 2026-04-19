# GraphQLite — Hybrid Vector + Graph RAG Reference

## Project Details

- **Repository**: https://github.com/colliery-io/graphqlite
- **Version**: 0.4.4
- **License**: MIT
- **What it is**: SQLite extension adding graph database capabilities via Cypher query language
- **Architecture**: Transpiler (Cypher → AST → SQL → SQLite execution)
- **Install**: `pip install graphqlite` (Python), `brew install graphqlite`, `cargo add graphqlite` (Rust)

## Core Architecture

GraphQLite adds a graph layer to SQLite through:

1. **Cypher Transpiler**: Parses Cypher queries → AST → generates optimized SQL
2. **EAV Property Model**: Entity-Attribute-Value schema for flexible node/edge properties
3. **CSR Graph Cache**: Compressed Sparse Row in-memory cache for fast algorithm execution
4. **SQL Execution**: Ultimately runs standard SQLite SQL, so it coexists with all SQLite extensions

### Integration with sqlite-vec

GraphQLite has first-class support for sqlite-vec (the vector extension used by rag4you-cli):

```python
import sqlite3
import graphqlite
import sqlite_vec

conn = sqlite3.connect(":memory:")

# Load GraphQLite FIRST (creates schema), then sqlite-vec
graphqlite.load(conn)
sqlite_vec.load(conn)

# Now both graph (Cypher) and vector (vec0) queries work on same connection
```

---

## Graph Algorithms (18 Built-in)

### Centrality
- **PageRank** — Node importance via link structure (`graph.pagerank(damping=0.85, iterations=20)`)
- **Degree Centrality** — In/out/total degree counts
- **Betweenness Centrality** — Bridge node detection
- **Closeness Centrality** — Average shortest path distance
- **Eigenvector Centrality** — Influence propagation

### Community Detection
- **Louvain** — Modularity-based community detection (`graph.louvain(resolution=1.0)`)
- **Leiden** — Improved Louvain with guaranteed connectivity (Python only)
- **Label Propagation** — Fast community assignment via neighbor voting

### Components
- **Weakly Connected Components** — Undirected connectivity
- **Strongly Connected Components** — Directed connectivity (Tarjan/Kosaraju)

### Pathfinding
- **Shortest Path / Dijkstra** — Weighted/unweighted shortest paths
- **A* (A-Star)** — Heuristic-guided shortest path (with lat/lon support)
- **All-Pairs Shortest Path** — Floyd-Warshall style

### Traversal
- **BFS** — Breadth-first search with max_depth
- **DFS** — Depth-first search with max_depth

### Similarity
- **Node Similarity** — Jaccard similarity based on shared neighbors
- **KNN** — k-Nearest Neighbors by structural similarity

### Clustering
- **Triangle Count** — Local clustering coefficient per node

---

## GraphRAG Implementation (Official Example)

The `examples/llm-graphrag/` directory provides a complete working GraphRAG system.

### Dependencies (pyproject.toml)

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

### Ingestion Pipeline (ingest.py)

The ingestion pipeline:
1. Loads HotpotQA dataset (multi-hop QA requiring cross-document reasoning)
2. Chunks documents and generates embeddings via `sentence-transformers`
3. Extracts entities via spaCy NER
4. Creates graph nodes (Document, Chunk, Entity) and edges (HAS_CHUNK, MENTIONS, COOCCURS)
5. Stores embeddings in sqlite-vec virtual table
6. Stores graph structure via GraphQLite Cypher

#### Entity Extraction Pattern

```python
import spacy

nlp = spacy.load("en_core_web_sm")

def extract_entities(text: str) -> list[dict]:
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        entities.append({
            "text": ent.text,
            "label": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char,
        })
    return entities
```

#### Graph Schema (Cypher)

```cypher
// Nodes
CREATE (d:Document {title: $title, source: $source})
CREATE (c:Chunk {text: $text, index: $idx, doc_id: $doc_id})
CREATE (e:Entity {name: $name, type: $type})

// Edges
CREATE (d)-[:HAS_CHUNK {order: $idx}]->(c)
CREATE (c)-[:MENTIONS {count: $count}]->(e)
CREATE (e1)-[:COOCCURS {weight: $weight, chunk_id: $chunk_id}]->(e2)
```

#### Vector Storage Pattern

```python
# Create vec0 virtual table alongside graph
conn.execute("""
    CREATE VIRTUAL TABLE chunk_embeddings USING vec0(
        chunk_id TEXT PRIMARY KEY,
        embedding FLOAT[384]
    )
""")

# Insert embeddings
conn.execute(
    "INSERT INTO chunk_embeddings (chunk_id, embedding) VALUES (?, ?)",
    (chunk_id, embedding_bytes)
)
```

### Retrieval Pipeline (rag.py)

The retrieval combines three strategies:

#### 1. Vector Search (Semantic Similarity)

```python
# KNN vector search via sqlite-vec
results = conn.execute("""
    SELECT chunk_id, distance
    FROM chunk_embeddings
    WHERE embedding MATCH ?
    ORDER BY distance
    LIMIT ?
""", (query_embedding_bytes, top_k)).fetchall()
```

#### 2. Graph Traversal (Entity Co-occurrence)

```python
# Find entities in retrieved chunks, then traverse COOCCURS edges
graph_context = conn.execute("""
    MATCH (c:Chunk)-[:MENTIONS]->(e:Entity)-[:COOCCURS]->(e2:Entity)<-[:MENTIONS]-(c2:Chunk)
    WHERE c.id IN $chunk_ids
    RETURN DISTINCT c2.id, c2.text, count(*) as relevance
    ORDER BY relevance DESC
    LIMIT 10
""", {"chunk_ids": retrieved_chunk_ids}).fetchall()
```

#### 3. Community Detection (Topic Clustering)

```python
# Run Louvain to find topic communities
communities = graph.louvain(resolution=1.0)

# Get community members for entities in query
query_entities = extract_entities(query)
entity_communities = {e['name']: get_community(e, communities) for e in query_entities}

# Retrieve chunks from same communities
community_chunks = get_chunks_by_community(entity_communities)
```

#### Combined Context Assembly

```python
def build_rag_context(query: str, conn, graph, model):
    query_emb = model.encode([query], normalize_embeddings=True)

    # Strategy 1: Vector search
    vector_chunks = vector_search(conn, query_emb, top_k=5)

    # Strategy 2: Graph traversal from vector results
    graph_chunks = graph_traverse(conn, vector_chunks, hops=2)

    # Strategy 3: Community-based expansion
    community_chunks = community_expand(graph, vector_chunks)

    # Deduplicate and rank
    all_chunks = deduplicate(vector_chunks + graph_chunks + community_chunks)
    ranked = rank_by_relevance(all_chunks, query_emb)

    return format_context(ranked[:10])
```

### LLM Generation

```python
# Send combined context to Ollama (local LLM)
response = httpx.post("http://localhost:11434/api/generate", json={
    "model": "llama3",
    "prompt": f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:",
    "stream": False,
})
```

---

## GraphQLite Tutorial: Building GraphRAG

From `docs/src/tutorials/graphrag.md`:

### Step 1: Schema Design

```cypher
// Document → Chunk → Entity hierarchy
CREATE (d:Document {title: "...", url: "..."})
CREATE (c:Chunk {text: "...", embedding_id: "..."})
CREATE (e:Entity {name: "...", type: "PERSON|ORG|LOCATION|..."})

// Relationships
(d)-[:HAS_CHUNK]->(c)
(c)-[:MENTIONS]->(e)
(e)-[:COOCCURS {weight: N}]->(e)  // co-occurrence in same chunk
```

### Step 2: PageRank for Entity Importance

```python
# After building the graph, compute PageRank
pr_results = graph.pagerank(damping=0.85, iterations=30)

# Use PageRank scores to boost entity relevance in retrieval
entity_scores = {r['user_id']: r['score'] for r in pr_results}
```

### Step 3: Multi-hop Retrieval

```cypher
// 2-hop traversal from seed entities
MATCH (e:Entity {name: $seed})-[:COOCCURS*1..2]->(e2:Entity)<-[:MENTIONS]-(c:Chunk)
RETURN c.text, c.embedding_id, count(DISTINCT e2) as entity_overlap
ORDER BY entity_overlap DESC
LIMIT 10
```

### Step 4: Community-Based Topic Retrieval

```python
# Detect communities for topic clustering
communities = graph.louvain(resolution=0.5)  # lower resolution = larger communities

# Group entities by community
from collections import defaultdict
community_map = defaultdict(list)
for result in communities:
    community_map[result['community']].append(result['user_id'])

# For a query, find which community the query entities belong to
# Then retrieve all chunks mentioning entities in that community
```

---

## Architecture: How GraphQLite Works Internally

### Transpiler Pipeline

```
Cypher Query String
    ↓
[Lexer] → Token Stream
    ↓
[Parser] → Abstract Syntax Tree (AST)
    ↓
[Planner] → Logical Plan
    ↓
[SQL Generator] → SQLite SQL + Parameters
    ↓
[SQLite Engine] → Results
```

### EAV Schema (Auto-created)

```sql
-- GraphQLite creates these tables automatically
CREATE TABLE _gql_nodes (
    id INTEGER PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    labels TEXT  -- JSON array of labels
);

CREATE TABLE _gql_edges (
    id INTEGER PRIMARY KEY,
    source_id INTEGER REFERENCES _gql_nodes(id),
    target_id INTEGER REFERENCES _gql_nodes(id),
    type TEXT NOT NULL
);

CREATE TABLE _gql_node_props (
    node_id INTEGER REFERENCES _gql_nodes(id),
    key TEXT NOT NULL,
    value TEXT  -- JSON-encoded value
);

CREATE TABLE _gql_edge_props (
    edge_id INTEGER REFERENCES _gql_edges(id),
    key TEXT NOT NULL,
    value TEXT  -- JSON-encoded value
);
```

### CSR Graph Cache

For graph algorithms, GraphQLite builds a Compressed Sparse Row (CSR) representation in memory:
- O(V + E) space
- O(1) neighbor access per node
- Must explicitly load with `gql_load_graph()` before algorithms
- Reload with `gql_reload_graph()` after structural changes
- Free with `gql_unload_graph()` when done
- Memory formula: ~(20N + 8E) bytes

#### CSR Memory Usage Table

| Nodes | Edges | CSR Memory |
|-------|-------|------------|
| 10K | 50K | ~600KB |
| 100K | 500K | ~6MB |
| 1M | 5M | ~60MB |

---

## Performance Benchmarks (from Official PDF v0.4.4)

Measured on single-core MacBook, `:memory:` database:

| Operation | Typical Latency |
|-----------|----------------|
| Extension loading (schema init) | ~5ms (once per connection) |
| Simple CREATE (:Person {name: 'Alice'}) | 0.5–1ms |
| Simple MATCH (10 nodes) | 0.5–2ms |
| MATCH with relationship (100 rels) | 1–5ms |
| gql_load_graph() on 100K nodes | ~50–100ms |
| PageRank 100K nodes | ~180ms |
| PageRank 1M nodes | ~38s |
| Bulk insert via insert_nodes_bulk() | 100–500x faster than Cypher CREATE |

### Scaling Characteristics

| Scale | Behavior | Recommendation |
|-------|----------|----------------|
| < 10K nodes | Sub-1ms queries; EAV fits in SQLite page cache | Cypher CREATE is acceptable |
| 10K–100K nodes | Property lookups 5–50ms | Bulk insert worthwhile |
| 100K–1M nodes | Full scan expensive | CSR cache mandatory for algorithms |
| > 1M nodes | CSR uses 60MB+ heap | Consider partitioning, pre-compute centrality |

### GraphRAG vs Vector RAG Accuracy

External benchmarks (Diffbot/FalkorDB 2025) demonstrate GraphRAG's advantage:
- **GraphRAG**: >90% accuracy on schema-bound/multi-hop queries
- **Vector RAG**: 0% accuracy on schema-bound queries (cannot follow relationships)
- **Hybrid search (vector + FTS)**: ~40% improvement over standalone vector search
- Sub-100ms query times for typical hybrid RAG on commodity hardware

---

## Applicability to rag4you-cli

### Triple-Hybrid RAG Stack

The project already uses sqlite-vec + FTS5. Adding GraphQLite enables:

```
┌─────────────────────────────────────────────┐
│              rag4you-cli RAG                 │
├─────────────────────────────────────────────┤
│ sqlite-vec   │ FTS5        │ GraphQLite     │
│ (Vector)     │ (Keyword)   │ (Graph)        │
│              │             │                │
│ Semantic     │ BM25        │ Multi-hop      │
│ similarity   │ term match  │ entity links   │
│ KNN search   │ Full-text   │ Community      │
│              │             │ PageRank       │
├─────────────────────────────────────────────┤
│         Single SQLite Database              │
│         (All extensions on same conn)       │
└─────────────────────────────────────────────┘
```

### Integration Steps

1. **Add dependencies**: `uv add graphqlite sqlite-vec spacy`
2. **Load extensions**: `graphqlite.load(conn)` then `sqlite_vec.load(conn)`
3. **Entity extraction**: Use spaCy NER during ingestion
4. **Graph construction**: Create MENTIONS and COOCCURS edges during chunking
5. **Hybrid retrieval**: Combine vector search + graph traversal + FTS5

### Benefits for Multi-hop QA

- **Co-occurrence graphs** connect concepts across different chunks/documents
- **PageRank** identifies authoritative entities for boosting
- **Community detection** groups related entities for topic-level retrieval
- **Graph traversal** enables multi-hop reasoning (entity A → related entity B → document C)

### Considerations

- **spaCy model size**: `en_core_web_sm` (12MB) vs `en_core_web_lg` (560MB) — tradeoff between accuracy and size
- **Graph maintenance**: Need to rebuild CSR cache when adding new documents
- **Entity resolution**: Same entity may have different surface forms (need normalization)
- **Performance**: Graph algorithms run in-memory; for very large graphs, resolution parameter controls community granularity
