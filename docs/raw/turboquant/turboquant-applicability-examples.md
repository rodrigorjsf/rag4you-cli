# TurboQuant — Applicability Examples & Implementation Guide

## Official Paper RAG Applicability (Section 4.4)

The TurboQuant paper (arXiv:2504.19874, ICLR 2026) explicitly benchmarks on embedding datasets used in RAG systems:

### Datasets Tested

| Dataset | Dimension | Source |
|---------|-----------|--------|
| GloVe | 200 | Standard word embeddings |
| DBpedia Entities (OpenAI3) | 1,536 | HuggingFace: Qdrant/dbpedia-entities-openai3-text-embedding-3-large-1536-1M |
| DBpedia Entities (OpenAI3) | 3,072 | HuggingFace: Qdrant/dbpedia-entities-openai3-text-embedding-3-large-3072-1M |

### Recall Results (Section 4.4, Figure 5)

TurboQuant consistently outperforms both Product Quantization and RaBitQ across all tested dimensions and bit-widths:

- **GloVe (d=200)**: TurboQuant 4-bit achieves ~0.95 Recall@1@64 vs PQ 4-bit ~0.85
- **OpenAI3 (d=1536)**: TurboQuant 4-bit achieves ~0.99 Recall@1@64 vs PQ 4-bit ~0.975
- **OpenAI3 (d=3072)**: TurboQuant 4-bit achieves ~0.99 Recall@1@64 vs PQ 4-bit ~0.95

### Indexing Speed (Table 2)

| Dimension | Product Quantization | RaBitQ | TurboQuant | Speedup vs PQ |
|-----------|---------------------|--------|------------|---------------|
| 200 | 37.04s | 597.25s | 0.0007s | 52,914x |
| 1,536 | 239.75s | 2,267.59s | 0.0013s | 184,423x |
| 3,072 | 494.42s | 3,957.19s | 0.0021s | 235,438x |

**Key insight**: Zero indexing time because TurboQuant is data-oblivious — no codebook training needed.

---

## Implementation Repositories

### 1. Firmamento-Technologies/TurboQuant (RAG-Focused, Recommended)

- **URL**: https://github.com/Firmamento-Technologies/TurboQuant
- **License**: Apache 2.0
- **Install**: `pip install turboquant`
- **Focus**: FAISS-compatible vector search for RAG
- **Tests**: 3,823 tests, 6/6 paper claims verified
- **API**: Drop-in FAISS replacement

#### Complete RAG Integration Example

```python
from sentence_transformers import SentenceTransformer
from turboquant import TurboQuantIndex

# 1. Generate embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")
docs = ["Document one text...", "Document two text...", ...]
embeddings = model.encode(docs, normalize_embeddings=True)

# 2. Build compressed index (6-bit: 95.3% recall, 5.3x compression)
index = TurboQuantIndex(dimension=384, num_bits=6)
index.add(embeddings)

# 3. Search
query_emb = model.encode(["search query"], normalize_embeddings=True)
similarities, doc_indices = index.search(query_emb, k=10)

# 4. Persist
index.save("my_rag_index")
loaded = TurboQuantIndex.load("my_rag_index")
```

#### IVF for Large-Scale RAG (>100K documents)

```python
from turboquant import IVFTurboQuantIndex

index = IVFTurboQuantIndex(
    dimension=384, num_bits=6,
    nlist=100,    # sqrt(N) partitions
    nprobe=10,    # partitions searched per query
)
index.train(embeddings)
index.add(embeddings)
similarities, indices = index.search(query_emb, k=10)
```

#### Package Structure

```
turboquant/
  __init__.py          # exports TurboQuantIndex, IVFTurboQuantIndex
  core/
    quantizer.py       # TurboQuantMSE (Algo 1), TurboQuantProd (Algo 2)
    lloyd_max.py       # Optimal scalar quantizer for Beta/Gaussian PDF
    rotation.py        # Haar-distributed random rotation (QR decomposition)
    qjl.py            # 1-bit Quantized Johnson-Lindenstrauss
  index/
    flat.py           # TurboQuantIndex — brute-force FAISS-compatible
    ivf.py            # IVFTurboQuantIndex — sub-linear with K-means
  utils/
    caching.py        # Codebook cache keyed by (d, b)
```

### 2. yashkc2025/turboquant (General Purpose)

- **URL**: https://github.com/yashkc2025/turboquant
- **License**: MIT
- **Focus**: Both KV cache and vector database use cases
- **Install**: Uses `uv` for dependency management

#### NN Search Example (TurboQuantProd)

```python
import numpy as np
from turboquant.main.prod import TurboQuantProd

# Unit-norm vectors required
X = np.random.randn(100_000, 256)
X /= np.linalg.norm(X, axis=1, keepdims=True)

query = np.random.randn(256)
query /= np.linalg.norm(query)

# Compress
tq = TurboQuantProd(d=256, b=4)
idx, qjl, gamma = tq.quantize(X)

# Reconstruct and search
X_hat = tq.dequantize(idx, qjl, gamma)
scores = query @ X_hat.T
topk = np.argsort(-scores)[:10]
```

#### KV Cache Streaming Example (TurboQuantMSE)

```python
from turboquant.main.mse import TurboQuantMSE

tq = TurboQuantMSE(dim=128, bits=3)

# During generation — one key per token
for key_vec in incoming_keys:
    idx = tq.quantize(key_vec[np.newaxis])
    cache.append(idx)

# During attention
all_keys = tq.dequantize(np.concatenate(cache, axis=0))
scores = query @ all_keys.T
```

### 3. helgklaizar/turboquant-mlx (Apple Silicon)

- **URL**: https://github.com/helgklaizar/turboquant-mlx
- **Focus**: MLX implementation for on-device inference
- **Target**: KV cache compression on Apple hardware

### 4. vivekvar-dl/turboquant (First Open-Source Implementation)

- **URL**: https://github.com/vivekvar-dl/turboquant
- **Focus**: HuggingFace Transformers integration
- **Features**: Recall benchmarks for NN search, plug-and-play with transformers

### 5. TheTom/turboquant_plus (llama.cpp Integration)

- **URL**: https://github.com/TheTom/turboquant_plus
- **Focus**: LLM KV compression integration with llama.cpp
- **Features**: Practical inference framework integration, benchmarking

### 6. amirzandieh/QJL (Official, by Paper Author)

- **URL**: https://github.com/amirzandieh/QJL
- **Paper**: "QJL: 1-Bit Quantized JL Transform" (arXiv:2406.03482)
- **Focus**: CUDA kernels for KV cache quantization
- **Relevance**: QJL is the building block for TurboQuant Algorithm 2

---

## Relation with Embedding Models for RAG

### Why TurboQuant Works for RAG Embeddings

1. **Data-oblivious**: Works on any embedding model output without calibration
2. **Preserves cosine similarity**: Unbiased inner-product estimation (Algorithm 2)
3. **Unit-norm assumption**: Standard for cosine similarity search (embeddings are always L2-normalized)
4. **High recall at practical bit-widths**: 95.3% recall at 6-bit (5.3x compression)

### Recommended Configurations by Embedding Model

| Embedding Model | Dimension | Recommended Bits | Expected Recall | Compression |
|-----------------|-----------|-----------------|-----------------|-------------|
| all-MiniLM-L6-v2 | 384 | 6 | 95.3% | 5.3x |
| BGE-small-en-v1.5 | 384 | 6 | ~95% | 5.3x |
| BGE-base-en-v1.5 | 768 | 5-6 | ~93-96% | 5.3-6.4x |
| text-embedding-3-small | 1,536 | 4-6 | ~95-99% | 5.3-8.0x |
| text-embedding-3-large | 3,072 | 4 | ~99% | 8.0x |

### Integration Pattern with sqlite-vec

```python
import sqlite3
import sqlite_vec
import numpy as np
from sentence_transformers import SentenceTransformer
from turboquant import TurboQuantIndex

# Strategy: TurboQuant as primary ANN, sqlite-vec for hybrid
model = SentenceTransformer("all-MiniLM-L6-v2")

# Build TurboQuant index for fast vector search
tq_index = TurboQuantIndex(dimension=384, num_bits=6)
tq_index.add(embeddings)

# Store full embeddings in sqlite-vec for hybrid (vector + FTS5)
conn = sqlite3.connect("rag.db")
sqlite_vec.load(conn)
conn.execute("CREATE VIRTUAL TABLE chunks USING vec0(embedding FLOAT[384])")

# Retrieval: TurboQuant for fast ANN → sqlite-vec for re-ranking
fast_results = tq_index.search(query_emb, k=50)  # broad recall
# Re-rank top candidates with exact cosine via sqlite-vec
```

---

## LLM Agent Implementation Guidance

### Configuration Knobs (for rag4you-cli)

```yaml
vector_quantization:
  enabled: true
  algorithm: "turboquant"
  bits: 6                    # 6-bit for RAG (95%+ recall)
  index_type: "flat"         # "flat" for <100K vectors, "ivf" for larger
  ivf_nlist: null            # Auto: sqrt(N) when index_type=ivf
  ivf_nprobe: 10             # Partitions searched per query
  normalize: true            # Always L2-normalize before quantization
  persistence_path: null     # Auto: alongside DB file
```

### Decision Matrix for Agents

| Corpus Size | Index Type | nlist | nprobe | Expected Latency |
|-------------|-----------|-------|--------|-----------------|
| < 10K | TurboQuantIndex (flat) | — | — | < 1ms |
| 10K – 100K | TurboQuantIndex (flat) | — | — | 1-10ms |
| 100K – 1M | IVFTurboQuantIndex | sqrt(N) | 10-20 | 5-20ms |
| > 1M | IVFTurboQuantIndex | sqrt(N) | 20-50 | 10-50ms |

### Implementation Steps for LLM Agent

1. **Install**: `uv add turboquant sentence-transformers`
2. **Embedding**: Use BGE-small (d=384) — matches verified benchmarks
3. **Normalization**: Always L2-normalize before quantization
4. **Index creation**: `TurboQuantIndex(dimension=384, num_bits=6)`
5. **Persistence**: `index.save()` / `TurboQuantIndex.load()`
6. **Search**: `index.search(query_emb, k=top_k)`

### Known Limitations

- Rotation matrix is O(d²) storage — for d > 4096, use structured Hadamard
- Pure NumPy (no GPU) — sufficient for rag4you-cli scale
- Unit-norm assumption — always normalize embeddings before quantizing
- No fractional bitwidths in pip package (paper's 2.5-bit uses outlier-channel splitting)

---

## References

- Paper: https://arxiv.org/abs/2504.19874
- OpenReview: https://openreview.net/pdf/6593f484501e295cdbe7efcbc46d7f20fc7e741f.pdf
- Google Blog: https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/
- GitHub Topic: https://github.com/topics/turboquant
