# TurboQuant Vector Quantization

**Summary**: TurboQuant is a data-oblivious online vector quantizer from Google Research (ICLR 2026) that achieves near-optimal distortion (within 2.72x of Shannon limit) with zero preprocessing. Directly applicable to RAG embedding compression for memory-efficient ANN search. Official paper benchmarks confirm 99%+ recall on OpenAI embeddings at 4-bit with zero indexing time.
**Sources**: docs/research/turboquant/turbo-quant.md, docs/research/turboquant/1-bit-quantized.md, docs/research/turboquant/polar-quant.md, docs/raw/turboquant/turboquant-implementations.md, docs/raw/turboquant/turboquant-applicability-examples.md
**Last updated**: 2025-07-24
---

## Overview

TurboQuant (arXiv:2504.19874) solves the problem of compressing high-dimensional embedding vectors while preserving search quality. Unlike [[embedding-models-research|traditional approaches]] (Product Quantization, ScaNN) that require expensive offline training on representative data, TurboQuant is **data-oblivious** — the same quantizer works on any input distribution without calibration (source: turbo-quant.md, Section 1).

The algorithm was developed at Google Research by Amir Zandieh, Majid Daliri, Majid Hadian, and Vahab Mirrokni. It unifies two use cases:

1. **KV cache compression** — Quantize key/value embeddings during LLM inference (streaming, one-at-a-time)
2. **Vector database compression** — Compress RAG embedding vectors for memory-efficient approximate nearest neighbor (ANN) search

## Algorithm

TurboQuant operates in three stages (source: turbo-quant.md, Algorithm 1-2):

### Stage 1: Random Rotation

Multiply input vector **x** ∈ ℝᵈ by a Haar-distributed orthogonal matrix **Π** (generated via QR decomposition). After rotation, each coordinate independently follows a Beta(1/2, (d-1)/2) distribution regardless of original input distribution. This is the key insight: it transforms worst-case inputs into statistically predictable ones.

### Stage 2: Lloyd-Max Scalar Quantization

Since coordinates are now approximately i.i.d. Beta (converging to Gaussian for large d), quantize each coordinate independently using the optimal 1D scalar quantizer (Lloyd-Max). The codebook is pre-computed analytically from the Beta PDF — no data needed.

### Stage 3: QJL Residual Correction (Inner-Product Variant)

For unbiased inner-product estimation (needed for cosine similarity search), apply a 1-bit [[sqlite-vec-fts5-hybrid-search|Quantized Johnson-Lindenstrauss]] (QJL) transform to the residual. This corrects the bias inherent in MSE-optimal quantizers at the cost of one extra bit per coordinate.

## Theoretical Guarantees

| Property | Bound | Reference |
|----------|-------|-----------|
| MSE distortion | E[‖x − x̂‖²] ≤ (√3π/2) · 4^{−b} | Theorem 1 |
| Shannon ratio | Within 2.72x of information-theoretic limit | Theorem 3 |
| Inner-product | Unbiased: E[⟨y, x̂⟩] = ⟨y, x⟩ | Theorem 2 |
| IP variance | Var ≤ (√3·π²·‖y‖²) / (d · 4^b) | Theorem 2 |

## RAG Embedding Search Results

The paper explicitly benchmarks TurboQuant on RAG-relevant embedding datasets (source: turbo-quant.md, Section 4.4):

### Indexing Speed (100K vectors, 4-bit)

| Dataset | Dimension | PQ Time | RaBitQ Time | TurboQuant | Speedup |
|---------|-----------|---------|-------------|------------|---------|
| GloVe | 200 | 37.04s | 597.25s | 0.0007s | 52,914x |
| OpenAI text-embedding-3 | 1,536 | 239.75s | 2,267.59s | 0.0013s | 184,423x |
| OpenAI text-embedding-3 | 3,072 | 494.42s | 3,957.19s | 0.0021s | 235,438x |

### Recall Performance (all-MiniLM-L6-v2, d=384)

| Bits | Recall@10 | Compression | Recommended Use |
|------|-----------|-------------|-----------------|
| 3 | 77.6% | 10.7x | IoT, mobile |
| 4 | 86.2% | 8.0x | Balanced |
| **6** | **95.3%** | **5.3x** | **RAG, search** |
| 8 | 99.5% | 4.0x | Near-lossless |

## Available Implementations

### Firmamento-Technologies/TurboQuant (Recommended for RAG)

- **Focus**: FAISS-compatible vector search
- **Install**: `pip install turboquant`
- **API**: Drop-in FAISS replacement (`TurboQuantIndex`, `IVFTurboQuantIndex`)
- **Verified**: 3,823 tests, 6/6 paper claims confirmed
- **Features**: Save/load, brute-force + IVF sub-linear search

```python
from turboquant import TurboQuantIndex
index = TurboQuantIndex(dimension=384, num_bits=6)
index.add(embeddings)  # No training step
similarities, indices = index.search(query_emb, k=10)
```

### yashkc2025/turboquant (General Purpose)

- **Focus**: Both KV cache and vector database use cases
- **API**: Lower-level (`TurboQuantMSE`, `TurboQuantProd`)
- **Uses**: `uv` for dependency management

### helgklaizar/turboquant-mlx (Apple Silicon)

- **Focus**: MLX implementation for on-device inference on Apple hardware

### vivekvar-dl/turboquant (HuggingFace Integration)

- **Focus**: First open-source implementation with HuggingFace Transformers integration
- **Features**: Recall benchmarks for NN search, plug-and-play with transformers pipeline
- **URL**: github.com/vivekvar-dl/turboquant

### TheTom/turboquant_plus (llama.cpp Integration)

- **Focus**: LLM KV compression via llama.cpp integration
- **Features**: Practical inference framework integration, llama.cpp compatibility
- **URL**: github.com/TheTom/turboquant_plus
- **Relevance**: Demonstrates TurboQuant's dual application — KV cache for LLM inference + vector DB for retrieval

### QJL Official (amirzandieh/QJL)

- **Focus**: CUDA kernels for KV cache quantization
- **Note**: By the same first author; QJL is the building block for TurboQuant Algorithm 2

## Official Paper Applicability Examples (Section 4.4)

The paper explicitly tests TurboQuant on **RAG-relevant embedding datasets** (source: turbo-quant.md, Section 4.4, Figure 5):

### Datasets Used for NN Search Benchmarks

| Dataset | Dimension | Source |
|---------|-----------|--------|
| GloVe | 200 | Standard word embeddings |
| DBpedia Entities (OpenAI3) | 1,536 | Qdrant/dbpedia-entities-openai3-text-embedding-3-large-1536-1M |
| DBpedia Entities (OpenAI3) | 3,072 | Qdrant/dbpedia-entities-openai3-text-embedding-3-large-3072-1M |

### Official Recall Comparison (Figure 5)

- **GloVe (d=200)**: TurboQuant 4-bit ≈ 0.95 Recall@1@64 vs PQ 4-bit ≈ 0.85
- **OpenAI3 (d=1536)**: TurboQuant 4-bit ≈ 0.99 Recall@1@64 vs PQ 4-bit ≈ 0.975
- **OpenAI3 (d=3072)**: TurboQuant 4-bit ≈ 0.99 Recall@1@64 vs PQ 4-bit ≈ 0.95

The paper shows TurboQuant consistently matches or exceeds RaBitQ and dominates PQ at all bit-widths tested.

### Embedding Model Compatibility Guide

| Embedding Model | Dimension | Recommended Bits | Expected Recall | Compression |
|-----------------|-----------|-----------------|-----------------|-------------|
| all-MiniLM-L6-v2 | 384 | 6 | 95.3% | 5.3x |
| BGE-small-en-v1.5 | 384 | 6 | ~95% | 5.3x |
| BGE-base-en-v1.5 | 768 | 5-6 | ~93-96% | 5.3-6.4x |
| text-embedding-3-small | 1,536 | 4-6 | ~95-99% | 5.3-8.0x |
| text-embedding-3-large | 3,072 | 4 | ~99% | 8.0x |

## Applicability to rag4you-cli

### Integration with sqlite-vec

Two approaches for combining TurboQuant with the project's existing [[sqlite-vec-fts5-hybrid-search]] backend:

1. **Pre-quantized storage**: Quantize embeddings before storing in sqlite-vec. Store compressed codes as BLOBs, dequantize at query time.

2. **Parallel index**: Use `TurboQuantIndex` as primary ANN search engine alongside sqlite-vec for hybrid queries. TurboQuant handles fast vector retrieval; sqlite-vec + FTS5 handle hybrid keyword/semantic search.

### Configuration Guidance for LLM Agents

When implementing TurboQuant in rag4you-cli:

- **Embedding model**: [[embedding-models-research|BGE-small]] (d=384) — matches verified benchmarks
- **Bit-width**: 6 bits for RAG (95.3% recall, 5.3x compression)
- **Index type**: `TurboQuantIndex` for < 100K vectors; `IVFTurboQuantIndex` with `nlist=sqrt(N)` for larger
- **Normalization**: Always L2-normalize before quantization (required by algorithm)
- **Persistence**: Use `index.save()` / `TurboQuantIndex.load()` for disk persistence

### Decision Matrix for LLM Agent Implementation

| Corpus Size | Index Type | nlist | nprobe | Expected Latency |
|-------------|-----------|-------|--------|-----------------|
| < 10K | TurboQuantIndex (flat) | — | — | < 1ms |
| 10K – 100K | TurboQuantIndex (flat) | — | — | 1-10ms |
| 100K – 1M | IVFTurboQuantIndex | sqrt(N) | 10-20 | 5-20ms |
| > 1M | IVFTurboQuantIndex | sqrt(N) | 20-50 | 10-50ms |

### Implementation Steps

1. **Install**: `uv add turboquant sentence-transformers`
2. **Embed**: Use BGE-small (d=384) or compatible model
3. **Normalize**: Always L2-normalize embeddings before quantization
4. **Index**: `TurboQuantIndex(dimension=384, num_bits=6)`
5. **Persist**: `index.save("path")` / `TurboQuantIndex.load("path")`
6. **Search**: `index.search(query_emb, k=top_k)`

### Limitations

- Rotation matrix is O(d²) storage — for d > 4096, structured Hadamard transform preferred
- Pure NumPy (no GPU acceleration) — sufficient for rag4you-cli scale
- Unit-norm assumption — standard for cosine similarity search (normalize before quantizing)
- No fractional bitwidths in current implementations (paper's 2.5-bit/3.5-bit results use outlier-channel splitting)

## Building Blocks: QJL and PolarQuant

### QJL (1-Bit Quantized JL Transform)

QJL (source: 1-bit-quantized.md) provides the 1-bit inner-product quantizer used as the residual correction in TurboQuant Algorithm 2. Key properties:

- Maps key vectors to binary codes: **k̃** = sign(**Sk**) where **S** is a random Gaussian matrix
- Preserves inner products with (1±ε) distortion using m ≥ O(ε⁻² log n) bits
- Zero overhead: quantization is just sign extraction after matrix multiply
- Official CUDA implementation at github.com/amirzandieh/QJL

### PolarQuant

PolarQuant (source: polar-quant.md) is a related quantization approach that:

- Transforms vectors to polar coordinates after random preconditioning
- Quantizes angles independently (they become i.i.d. after Gaussian preconditioning)
- Uses Lloyd-Max on the angle distribution (known analytically from Lemma 2)
- Shares the same random preconditioning insight as TurboQuant but operates in polar space

## Related pages

- [[embedding-models-research]]
- [[sqlite-vec-fts5-hybrid-search]]
- [[graphqlite-hybrid-rag]]
- [[rag-research-compendium]]
