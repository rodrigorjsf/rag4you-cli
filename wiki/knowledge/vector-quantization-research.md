# Vector Quantization for Embedding Storage and ANN Search

**Summary**: Research compendium on modern vector quantization (VQ) methods — TurboQuant, QJL, and PolarQuant — from Google Research. Covers how random-rotation-based quantizers achieve near-optimal distortion at 2.5–3.5 bits/coordinate, their applicability to embedding vector storage in RAG systems, and the tradeoffs against product quantization (PQ) for nearest-neighbor retrieval.
**Sources**: docs/raw/turboquant/turbo-quant.pdf, docs/raw/turboquant/1-bit-quantized.pdf, docs/raw/turboquant/polar-quant.pdf
**Last updated**: 2026-04-19

---

## Table of Contents

1. [Context and Motivation for RAG Systems](#1-context-and-motivation-for-rag-systems)
2. [QJL — 1-Bit Quantized JL Transform](#2-qjl--1-bit-quantized-jl-transform)
3. [TurboQuant — Near-Optimal VQ at Any Bit-Width](#3-turboQuant--near-optimal-vq-at-any-bit-width)
4. [PolarQuant — Polar Coordinate Quantization](#4-polarquant--polar-coordinate-quantization)
5. [Applicability Analysis: Embedding Storage in rag4you-cli](#5-applicability-analysis-embedding-storage-in-rag4you-cli)
6. [ANN Search: TurboQuant vs Product Quantization](#6-ann-search-turboQuant-vs-product-quantization)
7. [Implementation Paths](#7-implementation-paths)
8. [Summary Table](#8-summary-table)

---

## 1. Context and Motivation for RAG Systems

All three papers primarily address **LLM KV cache quantization** — compressing the key/value embedding cache that transformer decoders maintain during token generation. However, the underlying techniques are general vector quantization methods that apply directly to **stored embedding vectors in vector databases**, which is rag4you-cli's use case.

The core problem is identical: given a high-dimensional float32 embedding vector, compress it to a compact binary or low-bitwidth integer representation while preserving inner product (cosine similarity) accuracy for subsequent queries. (source: turbo-quant.pdf §1)

**Why this matters for rag4you-cli:**

- Embedding vectors occupy ~70–85% of the sqlite-vec database size (float32 per coordinate × dimension × n_docs)
- BGE-small (384-d), BGE-base (768-d), Jina-v2 (768-d), BGE-large (1024-d) at float32 = 1536–4096 bytes per vector
- At 3 bits/coord, storage drops 10–11× (float32 = 32 bits → 3 bits)
- Cosine similarity is preserved with provably bounded distortion

See [[sqlite-vec-fts5-hybrid-search]] for current storage architecture and [[embedding-models-research]] for the embedding model tiers these vectors come from.

---

## 2. QJL — 1-Bit Quantized JL Transform

**Paper**: "QJL: 1-Bit Quantized JL Transform for KV Cache Quantization with Zero Overhead"
**Authors**: Zandieh, Daliri, Han (NYU / Adobe Research / Independent), 2024
**Code**: https://github.com/amirzandieh/QJL (CUDA kernels available)
(source: 1-bit-quantized.pdf)

### Core algorithm

1. Draw a random Gaussian matrix **S** ∈ ℝ^(m×d) (orthogonalized via QR in practice)
2. For a vector **k** ∈ ℝ^d: `QJL(k) = sign(S · k)` → m-bit binary vector
3. For inner product estimation: `ProdQJL(q, k) = sqrt(π/2) · ‖k‖₂/m · <Sq, sign(Sk)>`

### Key theoretical properties

- **Unbiased**: E[ProdQJL(q,k)] = ⟨q, k⟩ (source: 1-bit-quantized.pdf §Lemma 3.2)
- **Low distortion**: bounded inner product error comparable to unquantized JL transform
- **Zero overhead**: no quantization constants (zero points, scales) to store per block — unlike KIVI, KVQuant, etc. (source: 1-bit-quantized.pdf §1)
- The asymmetry is critical: applying QJL to only the stored vector (key) while keeping the query unquantized gives an unbiased estimator. Applying QJL to both gives a biased angle estimator. (source: 1-bit-quantized.pdf §3)

### Practical results

- 3-bit quantization: 5× memory reduction vs FP16, no accuracy drop on LongBench (source: 1-bit-quantized.pdf §4.2)
- Works with Llama-2 7B and Llama-3 8B; supports bfloat16, FP16, FP32
- Outlier channels treated separately: identify in prefill, apply independent QJL instances

### Implementation note

The CUDA kernel computes `sign(S·k)` for quantization and `<Sq, sign(Sk)>` for inner product. Orthogonalizing **S** improves performance in practice (consistent with random Fourier feature literature). (source: 1-bit-quantized.pdf §4.1)

---

## 3. TurboQuant — Near-Optimal VQ at Any Bit-Width

**Paper**: "TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate"
**Authors**: Zandieh (Google Research), Daliri (NYU), Hadian (Google DeepMind), Mirrokni (Google Research), 2025
**Code**: Not open-sourced in paper
(source: turbo-quant.pdf)

### Core insight

Existing VQ methods either: (a) require slow data-dependent preprocessing (k-means, PQ codebooks), or (b) have suboptimal distortion bounds. TurboQuant is data-oblivious (online), GPU-friendly, and provably near-optimal. (source: turbo-quant.pdf §1)

### Two-stage algorithm

**Stage 1 — MSE-optimal quantizer (TurboQuant_mse):**
1. Apply random rotation **Π** to input vector → each coordinate independently follows Beta(d/2−1, d/2−1) distribution (by concentration on hypersphere) (source: turbo-quant.pdf §Lemma 1)
2. Solve 1-D k-means (Lloyd-Max algorithm) for the Beta distribution at each bit-width — precomputed once per bit-width
3. Quantize each coordinate to nearest centroid independently (exploits near-independence of rotated coordinates in high dimensions)
4. Dequantize: lookup centroids → rotate back

**Distortion (unit-norm input):**
- General: D_mse ≤ sqrt(2/3π) · 4^(-b) for any b ≥ 0
- b=1: 0.36, b=2: 0.117, b=3: 0.03, b=4: 0.009 (source: turbo-quant.pdf §Theorem 1)

**Stage 2 — Inner product optimizer (TurboQuant_prod):**
- MSE quantizer introduces bias for inner product estimation
- Fix: apply TurboQuant_mse at (b-1) bits → compute residual **r** = **x** - dequant(**x**) → apply QJL on residual at 1 bit
- Result: unbiased inner product estimator at bit-width b, with distortion proportional to ‖residual‖² (source: turbo-quant.pdf §3.2, Theorem 2)

### Lower bound

TurboQuant_mse is within factor sqrt(2/3π) ≈ 2.7 of the information-theoretic Shannon lower bound. For b=1, factor is only ~1.45. (source: turbo-quant.pdf §Theorem 3, §3.3)

### KV cache results

- 3.5-bit: identical quality to full-precision on LongBench (Llama-3.1-8B-Instruct, Ministral-7B)
- 2.5-bit: marginal degradation (49.44 vs 50.06 average score)
- Outlier handling: 32 channels at 3 bits + 96 channels at 2 bits → 2.5 bits effective (source: turbo-quant.pdf §4.3, Table 1)

---

## 4. PolarQuant — Polar Coordinate Quantization

**Paper**: "PolarQuant: Quantizing KV Caches with Polar Transformation"
**Authors**: Han (KAIST), Kacham, Mirrokni, Zandieh (Google Research), Karbasi (Yale), 2025
**Implementation**: PyTorch + CUDA kernels
(source: polar-quant.pdf)

### Core insight

Quantize angles in polar coordinates rather than Cartesian coordinates. After random preconditioning:
- Cartesian coordinates are difficult to quantize (outliers, non-uniform distribution)
- Polar angles concentrate tightly around π/4 with an analytically computable distribution
- No explicit normalization (zero point / scale) needed per block

### Recursive polar transformation

1. Group pairs of coordinates → transform to 2D polar (radius + angle)
2. Collect radii → recurse log₂(d) levels
3. Final output: 1 radius + (d-1) angles organized into log₂(d) levels

Angular distribution at level ℓ: sin^(2^(ℓ-1)-1)(2θ) shape, increasingly concentrated around π/4 at higher levels (source: polar-quant.pdf §Lemma 2)

### Bit allocation

Level 1 angles (range [0, 2π)): 4 bits; levels 2+: 2 bits each. For d=128 (Llama): 3.875 bits/coord. Radius stored in FP16 per token. (source: polar-quant.pdf §4.1)

### Results

- 4.2× KV cache compression, best quality among compared methods on LongBench
- Needle-in-Haystack: recall 0.991 vs exact 0.995 vs KIVI 0.984
- PolarQuant-R (online codebook): best average 48.37 vs exact 48.63 (source: polar-quant.pdf §Table 1)
- 14% faster generation than KIVI; offline codebook matches runtime of exact method at prefill

---

## 5. Applicability Analysis: Embedding Storage in rag4you-cli

### Direct applicability

These methods quantize any high-dimensional float32 vector while preserving inner product / cosine similarity. This maps directly to quantizing stored embedding vectors in sqlite-vec before writing them to the database.

| Dimension | float32 bytes | 3-bit bytes | Compression |
|-----------|-------------|-------------|-------------|
| BGE-small 384-d | 1,536 B | ~144 B | 10.7× |
| BGE-base / Jina 768-d | 3,072 B | ~288 B | 10.7× |
| BGE-large 1,024-d | 4,096 B | ~384 B | 10.7× |

The agent-engineering-toolkit indexes ~247 files. At 512-token chunks with ~50% overlap, corpus ≈ 1,000–5,000 chunks per collection. Compressed storage savings: modest at this scale (~5–50 MB saved). More impactful at larger corpora (SP1 target).

### Critical constraint: sqlite-vec compatibility

sqlite-vec stores vectors as native float32 blobs; its ANN search uses float32 cosine/dot-product operations. Quantized integer vectors would require:
- Custom dequantization before passing to sqlite-vec (negating storage speedup in query path), OR
- A separate quantized index layer alongside sqlite-vec (double storage during transition), OR
- Migrating from sqlite-vec to a quantization-aware store (out of scope for SP0/SP1)

**Verdict**: Full integration of these quantization methods is SP2/SP3 territory, not SP0. TurboQuant's ANN recall benchmarks inform SP2 model tier recommendations. (source: turbo-quant.pdf §4.4)

### Why SP2 and beyond, not SP0

SP0 measures the current toolkit RAG as a black box. The quantization papers are relevant for SP1 (new core architecture) and SP2 (model + storage tier decisions), specifically:
- Whether to store embeddings at float32, float16, or quantized integer
- Whether to use TurboQuant-style online quantization for large-corpus deployments
- Storage tier tradeoffs in the decision matrix

---

## 6. ANN Search: TurboQuant vs Product Quantization

This is the most directly actionable finding for rag4you-cli. TurboQuant was benchmarked against Product Quantization (PQ) and RabitQ for ANN search on OpenAI embedding datasets. (source: turbo-quant.pdf §4.4)

### Recall comparison (recall@1@k, k=1..64)

| Method | d=200 (GloVe) | d=1536 (OpenAI) | d=3072 (OpenAI) |
|--------|--------------|----------------|----------------|
| PQ (2-bit) | competitive | lower | lower |
| RabitQ (2-bit) | lower | lower | lower |
| TurboQuant (2-bit) | best | best | best |
| TurboQuant (4-bit) | best | best | best |

TurboQuant consistently outperforms data-dependent PQ even though PQ has the unfair advantage of training on the same dataset. (source: turbo-quant.pdf §4.4, Figure 5)

### Indexing time comparison (4-bit, seconds)

| Method | d=200 | d=1536 | d=3072 |
|--------|-------|--------|--------|
| PQ | 37s | 240s | 494s |
| RabitQ | 597s | 2,268s | 3,957s |
| **TurboQuant** | **0.0007s** | **0.0013s** | **0.0021s** |

TurboQuant indexing is essentially zero (random rotation + codebook lookup — no training phase). (source: turbo-quant.pdf §Table 2)

**SP2 implication**: For the model decision matrix, "which embedding tier performs best at lower storage cost?" is now answerable: a TurboQuant-quantized 4-bit 768-d vector likely outperforms a raw float32 384-d vector in both storage and recall.

---

## 7. Implementation Paths

### Path A: Post-embedding quantization layer (TurboQuant_prod)

After fastembed generates float32 embeddings, apply TurboQuant_prod before sqlite-vec storage:
- Compute: random rotation **Π** (precomputed per collection) → Lloyd-Max quantize per coordinate → QJL residual
- Store: integer indices + 1-bit residual + ‖x‖₂ scalar
- Query: dequantize at search time → pass to sqlite-vec
- Pros: data-oblivious, zero indexing overhead, provably near-optimal inner product
- Cons: dequantization overhead at query time; sqlite-vec expects float32 anyway

### Path B: QJL-based asymmetric inner product (QJL)

Store `sign(S·embedding)` as binary vectors; query with `S·query_embedding` (unquantized):
- Inner product: `ProdQJL(q, k) = sqrt(π/2) · ‖k‖₂/m · <Sq, sign(Sk)>`
- Pros: unbiased, zero overhead, open-source CUDA kernels
- Cons: requires custom sqlite-vec extension or bypass; float32 retrieval still needed for hybrid RRF

### Path C: Use quantization for re-ranking only (PolarQuant)

Full float32 for sqlite-vec retrieval (top-K candidates), then re-rank using quantized vectors for pairwise similarity computation. No storage integration needed. PyTorch implementation available.

### Recommended near-term action

For SP0/SP1: **no integration**. Use as research context for SP2 model tier design:
- Include "quantized storage" as an explicit tier option in the SP2 decision matrix
- Reference TurboQuant ANN recall results when comparing embedding model sizes (small 384-d quantized vs medium 768-d unquantized)
- Note QJL open-source availability for potential SP1 optional integration

---

## 8. Summary Table

| Method | Bit-width | Distortion type | Unbiased IP? | Indexing cost | Open source | Notes |
|--------|-----------|----------------|-------------|--------------|-------------|-------|
| **QJL** | 1-bit (3-bit combined) | Inner product | ✓ Yes | Zero | ✓ CUDA kernel | Foundation for TurboQuant_prod |
| **TurboQuant_mse** | Any b | MSE | ✗ Biased at low b | Zero | ✗ | Within 2.7× of Shannon bound |
| **TurboQuant_prod** | Any b | Inner product | ✓ Yes | Zero | ✗ | MSE(b-1) + QJL residual |
| **PolarQuant** | ~3.875-bit | MSE + angle | Approximate | ~11s prefill | PyTorch | Best long-context KV results |
| **PQ (baseline)** | 2–4-bit | MSE | ✗ | Minutes–hours | ✓ faiss | Data-dependent; worse ANN recall |

---

## Related pages

- [[embedding-models-research]] — FastEmbed models (BGE, Jina, GTE-Qwen2) whose output vectors these methods would quantize
- [[sqlite-vec-fts5-hybrid-search]] — Current storage architecture; sqlite-vec compatibility constraints for quantized vectors
- [[rag-research-compendium]] — Full RAG pipeline context: where embedding quantization fits in the indexing and retrieval phases
- [[ir-evaluation-benchmarking]] — Metrics (precision@k, MRR) used to measure quantization quality degradation
