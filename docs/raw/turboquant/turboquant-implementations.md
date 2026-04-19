# TurboQuant — Implementation Reference

## Paper Details

- **Title**: TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate
- **Authors**: Amir Zandieh (Google Research), Majid Daliri (NYU), Majid Hadian (Google DeepMind), Vahab Mirrokni (Google Research)
- **Venue**: ICLR 2026
- **arXiv**: [2504.19874](https://arxiv.org/abs/2504.19874)
- **OpenReview**: [ICLR 2026](https://openreview.net/pdf/6593f484501e295cdbe7efcbc46d7f20fc7e741f.pdf)
- **Google Research Blog**: [TurboQuant: Redefining AI efficiency with extreme compression](https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/)

## Algorithm Summary

TurboQuant is a data-oblivious (online) vector quantizer that achieves near-optimal distortion:

1. **Random Rotation** — Multiply input vector by Haar-distributed orthogonal matrix (QR decomposition). After rotation, each coordinate follows a Beta distribution regardless of original input.
2. **Lloyd-Max Scalar Quantization** — Since coordinates are now approximately i.i.d. Beta (converging to Gaussian for large d), quantize each independently using pre-computed optimal 1D quantizer.
3. **QJL Residual Correction** (inner-product variant only) — Apply 1-bit Quantized Johnson-Lindenstrauss transform to residual for unbiased inner-product estimation.

### Theoretical Guarantees

- **MSE**: `E[‖x − x̂‖²] ≤ (√3π / 2) · 4^{−b}` — within factor 2.72x of Shannon limit
- **Inner-product**: Unbiased estimation with variance ≤ `(√3·π²·‖y‖²) / (d · 4^b)`
- **Data-oblivious**: No calibration, no preprocessing, no codebook training needed

### Performance vs Alternatives (from paper Section 4.4)

| Dimension | Product Quantization | RaBitQ | TurboQuant | Speedup vs PQ |
|----------:|---------------------:|-------:|---------:|---:|
| 200 (GloVe) | 37.04s | 597.25s | 0.0007s | 52,914x |
| 1,536 (OpenAI3) | 239.75s | 2,267.59s | 0.0013s | 184,423x |
| 3,072 (OpenAI3) | 494.42s | 3,957.19s | 0.0021s | 235,438x |

---

## Implementation 1: Firmamento-Technologies/TurboQuant (Vector Search Focused)

- **Repository**: https://github.com/Firmamento-Technologies/TurboQuant
- **License**: Apache 2.0
- **Focus**: FAISS-compatible vector quantization for embedding search
- **Install**: `pip install turboquant`
- **Tests**: 3,823 tests, 6/6 paper claims verified

### Key Features

- FAISS-compatible API (`TurboQuantIndex`, `IVFTurboQuantIndex`)
- Pure Python/NumPy (no GPU required)
- Drop-in replacement for FAISS indices
- Save/load support for persistent indices
- Both brute-force and IVF (sub-linear) search

### Benchmark Results (all-MiniLM-L6-v2, d=384)

| Bits | Recall@10 | Cosine Sim | Compression | Memory (10K vectors) |
|------|-----------|-----------|-------------|---------------------|
| 3 | 77.6% | 0.965 | 10.7x | 1.40 MB |
| 4 | 86.2% | 0.990 | 8.0x | 1.88 MB |
| 5 | 92.6% | 0.997 | 6.4x | 2.34 MB |
| 6 | 95.3% | 0.998 | 5.3x | 2.81 MB |
| 8 | 99.5% | — | 4.0x | — |

### Recommended Configuration for RAG

| Use Case | Bits | Recall | Compression |
|----------|------|--------|-------------|
| Maximum compression (IoT, mobile) | 3 | 77.6% | 10.7x |
| Balanced (default) | 4 | 86.2% | 8.0x |
| **High accuracy (RAG, search)** | **6** | **95.3%** | **5.3x** |
| Near-lossless | 8 | 99.5% | 4.0x |

### Code Example: Semantic Search with Sentence Transformers

```python
from sentence_transformers import SentenceTransformer
from turboquant import TurboQuantIndex

model = SentenceTransformer("all-MiniLM-L6-v2")

# Encode documents
docs = ["First document", "Second document", ...]
embeddings = model.encode(docs, normalize_embeddings=True)

# Build compressed index (6-bit for RAG: 95%+ recall, 5.3x compression)
index = TurboQuantIndex(dimension=384, num_bits=6)
index.add(embeddings)

# Semantic search
query_emb = model.encode(["search query"], normalize_embeddings=True)
similarities, doc_indices = index.search(query_emb, k=10)

# Save and load
index.save("my_index")
loaded = TurboQuantIndex.load("my_index")
```

### Code Example: IVF for Large Datasets

```python
from turboquant import IVFTurboQuantIndex
import numpy as np

# Sub-linear search for large corpora
index = IVFTurboQuantIndex(
    dimension=384, num_bits=6,
    nlist=100,    # number of partitions
    nprobe=10,    # partitions to search per query
)

training_data = np.random.randn(50000, 384).astype(np.float32)
index.train(training_data)
index.add(training_data)

query = np.random.randn(1, 384).astype(np.float32)
similarities, indices = index.search(query, k=10)
```

### Package Structure

```
turboquant/
  __init__.py          # exports TurboQuantIndex, IVFTurboQuantIndex, TurboQuantMSE, TurboQuantProd
  core/
    quantizer.py       # TurboQuantMSE (Algorithm 1) and TurboQuantProd (Algorithm 2)
    lloyd_max.py       # Optimal scalar quantizer for Beta/Gaussian PDF
    rotation.py        # Haar-distributed random rotation (QR decomposition)
    qjl.py            # 1-bit Quantized Johnson-Lindenstrauss
  index/
    flat.py           # TurboQuantIndex — brute-force FAISS-compatible
    ivf.py            # IVFTurboQuantIndex — sub-linear with K-means partitioning
  utils/
    caching.py        # Codebook cache keyed by (d, b)
```

---

## Implementation 2: yashkc2025/turboquant (General Purpose)

- **Repository**: https://github.com/yashkc2025/turboquant
- **License**: MIT
- **Focus**: General-purpose TurboQuant (KV cache + vector databases)
- **Install**: `pip install .` (uses `uv`)
- **Dependencies**: numpy, scipy

### Key Features

- Faithful implementation of both Algorithm 1 (MSE) and Algorithm 2 (Prod)
- `TurboQuantMSE` for KV cache compression
- `TurboQuantProd` for unbiased inner-product estimation (NN search)
- Includes benchmark experiments for verification

### Code Example: Nearest-Neighbor Search

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

### Code Example: Streaming KV-Cache

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

### Package Structure

```
turboquant/
  main/
    mse.py        # TurboQuantMSE (Algorithm 1)
    prod.py       # TurboQuantProd (Algorithm 2, with QJL)
    qjl.py        # QJL 1-bit inner-product quantizer
    lloyd_max.py  # Lloyd-Max solver for Beta distribution
    rotation.py   # Haar-distributed random rotation
    caching.py    # Global codebook cache
  misc/
    simple_quant.py  # NaiveQuant baseline
  experiments/
    benchmark_vs_naive.py
    nearest_neighbor.py
    kv_cache_simulation.py
```

---

## Implementation 3: helgklaizar/turboquant-mlx (Apple Silicon)

- **Repository**: https://github.com/helgklaizar/turboquant-mlx
- **Focus**: MLX (Apple Silicon) implementation for on-device inference
- **Note**: Targets KV cache compression on Apple hardware

---

## 4. vivekvar-dl/turboquant (HuggingFace Integration)

- **Repository**: https://github.com/vivekvar-dl/turboquant
- **License**: Open source
- **Focus**: First open-source implementation with HuggingFace Transformers integration
- **Features**: Recall benchmarks for NN search, plug-and-play with transformers pipeline
- **Notable**: Early community implementation that helped validate paper claims

---

## 5. TheTom/turboquant_plus (llama.cpp Integration)

- **Repository**: https://github.com/TheTom/turboquant_plus
- **License**: Open source
- **Focus**: LLM KV compression via llama.cpp integration
- **Features**: Practical inference framework integration, benchmarking
- **Relevance**: Demonstrates TurboQuant's dual application path — KV cache for inference acceleration + vector DB for retrieval
- **Note**: Integrates TurboQuant quantization into the llama.cpp inference stack for lower memory usage during generation

---

## Related: QJL Official Repository

- **Repository**: https://github.com/amirzandieh/QJL
- **Paper**: "QJL: 1-Bit Quantized JL Transform for KV Cache Quantization with Zero Overhead" (arXiv:2406.03482)
- **Authors**: Same first author (Amir Zandieh) — QJL is the building block used in TurboQuant Algorithm 2
- **Contains**: CUDA kernels for KV cache quantization, integrated with HuggingFace transformers
- **Relevance**: QJL provides the 1-bit residual correction that makes TurboQuantProd unbiased for inner products

---

## Applicability to rag4you-cli

### Direct RAG Application

TurboQuant's Section 4.4 explicitly benchmarks on embedding datasets used in RAG:
- OpenAI text-embedding-3 (d=1536, d=3072)
- GloVe embeddings (d=200)
- DBpedia embeddings

At 6-bit quantization: **95%+ recall with 5.3x compression** — suitable for RAG where recall matters.

### Integration Patterns for sqlite-vec

Two possible integration approaches:

1. **Pre-quantized storage**: Quantize embeddings with TurboQuant before storing in sqlite-vec. Store quantized codes as BLOBs. Dequantize at query time for cosine similarity.

2. **Side-by-side index**: Use TurboQuantIndex as the primary search index, with sqlite-vec for hybrid (vector + FTS5) queries. TurboQuantIndex handles ANN search, sqlite-vec handles exact vector ops.

### Known Limitations

- **Rotation cost**: O(d³) for QR decomposition, O(d²) storage. For d > 4096, use randomized Hadamard.
- **No GPU path**: Pure NumPy. Algorithm is trivially parallelizable but no CUDA implementation.
- **Unit-norm assumption**: Inputs must be L2-normalized (standard for cosine-similarity search).
- **No fractional bitwidths**: Paper's 2.5-bit and 3.5-bit results not implemented (requires outlier-channel splitting).

### Recommended Configuration for rag4you-cli

- **Embedding model**: BGE-small (d=384) or BGE-base (d=768)
- **Quantization**: 6-bit for high accuracy, 4-bit for maximum compression
- **Index type**: `TurboQuantIndex` for < 100K vectors, `IVFTurboQuantIndex` for larger corpora
- **Normalization**: Always L2-normalize embeddings before quantization
