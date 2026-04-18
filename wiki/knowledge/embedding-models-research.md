# Embedding Models & FastEmbed — Authoritative Research Reference

**Summary**: Comprehensive reference covering FastEmbed, BGE embedding models, code embedding models, cross-encoder reranking, and chunking strategies for the rag4you-cli project.
**Sources**: docs/references/embedding-models/bibliography.md
**Last updated**: 2025-07-22
---

## Table of Contents

1. [FastEmbed (Qdrant)](#1-fastembed-qdrant)
2. [BGE Embedding Models (BAAI)](#2-bge-embedding-models-baai)
3. [Code Embedding Models](#3-code-embedding-models)
4. [Cross-Encoder Reranking](#4-cross-encoder-reranking)
5. [Chunking Strategies for Code vs Documentation](#5-chunking-strategies-for-code-vs-documentation)
6. [Model Selection Matrix for rag4you-cli](#6-model-selection-matrix-for-rag4you-cli)
7. [References](#7-references)

---

## 1. FastEmbed (Qdrant)

### Sources

| Resource | URL |
|----------|-----|
| Official Docs | https://qdrant.github.io/fastembed/ |
| GitHub Repo | https://github.com/qdrant/fastembed |
| Supported Models | https://qdrant.github.io/fastembed/examples/Supported_Models/ |
| PyPI | https://pypi.org/project/fastembed/ |

### What It Is

FastEmbed is a lightweight, fast Python library for embedding generation. It uses **ONNX Runtime** for inference (not PyTorch), making it much lighter and faster, suitable for serverless and CPU-only environments.

### Key Properties

- **Runtime**: ONNX Runtime (CPU by default, optional GPU via `fastembed-gpu`)
- **No PyTorch dependency**: Significantly smaller footprint
- **Data parallelism**: Built-in for encoding large datasets
- **Quantized weights**: Models are pre-quantized for speed
- **Default model**: `BAAI/bge-small-en-v1.5` (384 dimensions)

### Supported Model Categories

| Category | Class | Use Case |
|----------|-------|----------|
| Dense Text | `TextEmbedding` | Semantic search, retrieval |
| Sparse Text | `SparseTextEmbedding` | Exact/keyword search (SPLADE++) |
| Late Interaction | `LateInteractionTextEmbedding` | ColBERT-style retrieval |
| Image | `ImageEmbedding` | Image search |
| Cross-Encoder Reranker | `TextCrossEncoder` | Re-ranking retrieved results |

### Dense Text Embedding Models Relevant to rag4you-cli

| Model | Dim | Max Tokens | License | Size (GB) |
|-------|-----|------------|---------|-----------|
| `BAAI/bge-small-en-v1.5` | 384 | 512 | MIT | 0.067 |
| `BAAI/bge-base-en-v1.5` | 768 | 512 | MIT | 0.210 |
| `BAAI/bge-large-en-v1.5` | 1024 | 512 | MIT | 1.200 |
| `jinaai/jina-embeddings-v2-base-code` | 768 | 8192 | Apache-2.0 | 0.640 |
| `nomic-ai/nomic-embed-text-v1.5` | 768 | — | Apache-2.0 | 0.520 |

### Cross-Encoder Reranker Models in FastEmbed

| Model | License | Size (GB) | Context |
|-------|---------|-----------|---------|
| `BAAI/bge-reranker-base` | MIT | 1.04 | — |
| `BAAI/bge-reranker-v2-m3` | MIT | 2.27 | Multilingual |
| `jinaai/jina-reranker-v1-turbo-en` | Apache-2.0 | 0.15 | 8K |
| `jinaai/jina-reranker-v1-tiny-en` | Apache-2.0 | 0.13 | 8K |
| `Xenova/ms-marco-MiniLM-L-6-v2` | Apache-2.0 | 0.08 | — |
| `Xenova/ms-marco-MiniLM-L-12-v2` | Apache-2.0 | 0.12 | — |

### Python API Patterns

```python
# Installation (use [[python-uv]]: uv add fastembed)
# pip install fastembed          (CPU)
# pip install fastembed-gpu      (GPU)

# Dense embedding
from fastembed import TextEmbedding
model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
embeddings = list(model.embed(["passage: Hello world"]))
# Returns list of numpy arrays, each of shape (384,)

# List all supported models
for m in TextEmbedding.list_supported_models():
    print(m["model"], m["dim"], m["description"])

# Cross-encoder reranking
from fastembed.rerank.cross_encoder import TextCrossEncoder
reranker = TextCrossEncoder(model_name="BAAI/bge-reranker-v2-m3")
scores = list(reranker.rerank("query text", ["doc1", "doc2", "doc3"]))

# GPU execution
model = TextEmbedding(
    model_name="BAAI/bge-small-en-v1.5",
    providers=["CUDAExecutionProvider"]
)

# Custom model registration
from fastembed.common.model_description import PoolingType, ModelSource
TextEmbedding.add_custom_model(
    model="my-org/my-model",
    pooling=PoolingType.MEAN,
    normalization=True,
    sources=ModelSource(hf="my-org/my-model"),
    dim=768,
    model_file="onnx/model.onnx",
)
```

### Important Notes for rag4you-cli

1. **nomic-ai/nomic-embed-code** is a 7B parameter model. It is **NOT** available in FastEmbed's ONNX model list. It requires PyTorch/Transformers or SentenceTransformers directly.
2. **Alibaba-NLP/gte-Qwen2-1.5B-instruct** is also **NOT** in FastEmbed's supported model list. It requires `transformers` with `trust_remote_code=True`.
3. Only `BAAI/bge-*` and `jinaai/jina-embeddings-v2-base-code` from our model list are natively supported by FastEmbed with ONNX.
4. For models not in FastEmbed, the `add_custom_model()` API can register them if ONNX weights are available on HuggingFace.

---

## 2. BGE Embedding Models (BAAI)

### Sources

| Resource | URL |
|----------|-----|
| bge-small-en-v1.5 Model Card | https://huggingface.co/BAAI/bge-small-en-v1.5 |
| bge-base-en-v1.5 Model Card | https://huggingface.co/BAAI/bge-base-en-v1.5 |
| bge-large-en-v1.5 Model Card | https://huggingface.co/BAAI/bge-large-en-v1.5 |
| C-Pack Paper (SIGIR 2024) | https://arxiv.org/abs/2309.07597 |
| FlagEmbedding GitHub | https://github.com/FlagOpen/FlagEmbedding |
| MTEB Leaderboard | https://huggingface.co/spaces/mteb/leaderboard |

### BGE Paper: C-Pack (arXiv:2309.07597)

**Title**: "C-Pack: Packed Resources For General Chinese Embeddings"
**Venue**: SIGIR 2024
**Authors**: Shitao Xiao, Zheng Liu, Peitian Zhang, Niklas Muennighoff, Defu Lian, Jian-Yun Nie

**Key contributions**:
- C-MTEB benchmark (6 tasks, 35 datasets)
- C-MTP training dataset (labeled + unlabeled corpora)
- BGE (BAAI General Embedding) family of models in multiple sizes
- English models achieve SOTA on MTEB benchmark

### Model Comparison

| Model | Parameters | Dimensions | MTEB Avg | Size (ONNX) | Max Tokens |
|-------|-----------|------------|----------|-------------|------------|
| `bge-small-en-v1.5` | 22M | 384 | ~63.98 | 67 MB | 512 |
| `bge-base-en-v1.5` | 110M | 768 | ~67.55 | 210 MB | 512 |
| `bge-large-en-v1.5` | 355M | 1024 | ~70.19 | 1.2 GB | 512 |

### v1.5 Improvements Over v1.0

The v1.5 release specifically addresses the **similarity distribution problem**: v1.0 models had similarity scores clustered in the `[0.6, 1.0]` interval due to contrastive learning with temperature 0.01. The v1.5 models produce a more reasonable distribution, making threshold-based filtering more practical (source: docs/references/embedding-models/bibliography.md).

### Query Instructions for Retrieval

For retrieval tasks (short query → long passage), as covered in [[rag-research-compendium]], prepend to queries:
```
Represent this sentence for searching relevant passages:
```

**Important**: Do NOT add instructions to passages/documents. Only queries need the prefix.

For the v1.5 models, performance without instructions is only slightly degraded — instructions are recommended but not required.

### Practical Guidance from Official Model Card

1. **Relative order matters, not absolute scores** — similarity score of 0.5 does NOT mean "similar." Use relative ranking.
2. **Hard negatives improve fine-tuning** significantly.
3. **Pre-trained models cannot be used directly for similarity** — they must be fine-tuned with contrastive learning first.
4. If fine-tuned accuracy is insufficient, use a cross-encoder reranker on top-k results (source: docs/references/embedding-models/bibliography.md).

---

## 3. Code Embedding Models

### 3.1 Nomic Embed Code (`nomic-ai/nomic-embed-code`)

#### Sources

| Resource | URL |
|----------|-----|
| HuggingFace Model Card | https://huggingface.co/nomic-ai/nomic-embed-code |
| CoRNStack Paper (ICLR 2025) | https://arxiv.org/abs/2412.01007 |
| Blog Post | https://nomic.ai/news/nomic-embed-code |

#### Key Properties

- **Parameters**: 7 billion (decoder-only architecture)
- **Pooling**: **Last-token pooling** (NOT mean pooling)
- **Training data**: CoRNStack — contrastive dataset with consistency filtering and hard negative mining
- **Languages**: Python, Java, Ruby, PHP, JavaScript, Go
- **License**: Apache-2.0 (fully open: weights, data, code)

#### CodeSearchNet Benchmark Results

| Model | Python | Java | Ruby | PHP | JS | Go |
|-------|--------|------|------|-----|----|----|
| Nomic Embed Code | 81.7 | 80.5 | 81.8 | 72.3 | 77.1 | 93.8 |
| Voyage Code 3 | 80.8 | 80.5 | 84.6 | 71.7 | 79.2 | 93.2 |
| OpenAI Embed 3 Large | 70.8 | 72.9 | 75.3 | 59.6 | 68.1 | 87.6 |

#### Query Prompting

When embedding natural language queries, always prefix with:
```
Represent this query for searching relevant code:
```

Code snippets do NOT need a prefix.

#### CoRNStack Paper (arXiv:2412.01007)

**Title**: "CoRNStack: High-Quality Contrastive Data for Better Code Retrieval and Reranking"
**Venue**: ICLR 2025

Key findings:
- Consistency filtering eliminates noisy positives from training data
- Hard negative mining significantly improves code retrieval
- The dataset can also train code reranking models
- Combined retriever + reranker improves function localization on real GitHub issues

#### FastEmbed Compatibility

**nomic-embed-code is NOT natively supported by FastEmbed** (7B parameters, requires PyTorch). Use via `transformers` or `sentence-transformers` directly:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("nomic-ai/nomic-embed-code")
query_emb = model.encode(["Calculate factorial"], prompt_name="query")
code_emb = model.encode(["def fact(n): return 1 if n == 0 else n * fact(n-1)"])
```

### 3.2 Jina Embeddings v2 Base Code (`jinaai/jina-embeddings-v2-base-code`)

#### Sources

| Resource | URL |
|----------|-----|
| HuggingFace Model Card | https://huggingface.co/jinaai/jina-embeddings-v2-base-code |
| Technical Report | https://arxiv.org/abs/2310.19923 |
| Jina AI | https://jina.ai/embeddings/ |

#### Key Properties

- **Parameters**: 161M (BERT-based, JinaBERT variant)
- **Dimensions**: 768
- **Max sequence length**: **8192 tokens** (trained at 512, extrapolates via ALiBi)
- **Pooling**: **Mean pooling**
- **Architecture**: JinaBERT with symmetric bidirectional ALiBi attention
- **Pre-training data**: GitHub-code dataset (codeparrot/github-code)
- **Fine-tuning**: 150M+ coding Q&A and docstring–source-code pairs
- **License**: Apache-2.0

#### Supported Languages (30+)

Assembly, Batchfile, C, C#, C++, CMake, CSS, Dockerfile, FORTRAN, Go, Haskell, HTML, Java, JavaScript, Julia, Lua, Makefile, Markdown, PHP, Perl, PowerShell, Python, Ruby, Rust, SQL, Scala, Shell, TypeScript, TeX, Visual Basic, and English natural language.

#### Jina Embeddings v2 Paper (arXiv:2310.19923)

**Title**: "Jina Embeddings 2: 8192-Token General-Purpose Text Embeddings for Long Documents"

Key contributions:
- Overcomes the conventional 512-token limit
- ALiBi-based position encoding enables extrapolation to 8192+ tokens
- Matches OpenAI Ada-002 performance on MTEB benchmark
- Extended context improves performance on long-document tasks (NarrativeQA)

#### FastEmbed Compatibility

**Natively supported** in FastEmbed (row #19 in supported models list, 0.640 GB ONNX).

```python
from fastembed import TextEmbedding
model = TextEmbedding(model_name="jinaai/jina-embeddings-v2-base-code")
embeddings = list(model.embed(["def hello(): print('world')"]))
```

### 3.3 GTE-Qwen2-1.5B-instruct (`Alibaba-NLP/gte-Qwen2-1.5B-instruct`)

#### Sources

| Resource | URL |
|----------|-----|
| HuggingFace Model Card | https://huggingface.co/Alibaba-NLP/gte-Qwen2-1.5B-instruct |
| GTE Paper | https://arxiv.org/abs/2308.03281 |

#### Key Properties

- **Architecture**: Qwen2-1.5B (decoder-only LLM backbone)
- **Dimensions**: 1536
- **Max Input Tokens**: **32,768** (32k context)
- **Training**: Weakly-supervised + supervised, instruction tuning on query side
- **Attention**: Bidirectional (enhanced for embedding task)
- **Multilingual**: 70+ languages
- **Requirements**: `transformers >= 4.39.2`, `flash_attn >= 2.5.6`

#### GTE Paper (arXiv:2308.03281)

**Title**: "Towards General Text Embeddings with Multi-stage Contrastive Learning"
**Authors**: Zehan Li et al., Alibaba Group

Key findings:
- Multi-stage contrastive learning pipeline: unsupervised pre-training (800M pairs) → supervised fine-tuning (3M triples)
- GTE-base (110M params) outperforms OpenAI Ada-002 and models 10x larger
- Without code-specific fine-tuning, GTE outperforms same-size code retrievers
- The gte-Qwen2 family extends this to LLM-scale (1.5B, 7B parameters)

#### FastEmbed Compatibility

**NOT natively supported by FastEmbed**. Use via `sentence-transformers`:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "Alibaba-NLP/gte-Qwen2-1.5B-instruct",
    trust_remote_code=True
)
query_embeddings = model.encode(["your query"], prompt_name="query")
document_embeddings = model.encode(["your document"])
scores = (query_embeddings @ document_embeddings.T) * 100
```

---

## 4. Cross-Encoder Reranking

### 4.1 BGE Reranker v2 M3 (`BAAI/bge-reranker-v2-m3`)

#### Sources

| Resource | URL |
|----------|-----|
| HuggingFace Model Card | https://huggingface.co/BAAI/bge-reranker-v2-m3 |
| FlagEmbedding GitHub | https://github.com/FlagOpen/FlagEmbedding |
| BGE Documentation | https://bge-model.com/bge/bge_reranker_v2.html |

#### Key Properties

- **Type**: Cross-encoder reranker (NOT an embedding model)
- **Base model**: BGE-M3
- **Parameters**: 568M (~2.27 GB)
- **Multilingual**: Chinese, English, and many other languages
- **Input**: Takes [query, document] pair → outputs relevance score
- **Score range**: Raw logits (can apply sigmoid for [0,1] normalization)

#### Usage with FlagEmbedding

```python
from FlagEmbedding import FlagReranker

reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True)

# Single pair
score = reranker.compute_score(['query', 'passage'])

# Normalized to [0, 1]
score = reranker.compute_score(['query', 'passage'], normalize=True)

# Batch
scores = reranker.compute_score([
    ['what is panda?', 'hi'],
    ['what is panda?', 'The giant panda is a bear endemic to China.']
])
```

#### Usage with FastEmbed

```python
from fastembed.rerank.cross_encoder import TextCrossEncoder

reranker = TextCrossEncoder(model_name="BAAI/bge-reranker-v2-m3")
scores = list(reranker.rerank("What is RAG?", [
    "RAG stands for Retrieval-Augmented Generation...",
    "Red, amber, and green traffic lights...",
    "RAG combines retrieval with language models..."
]))
```

### 4.2 Cross-Encoder vs Bi-Encoder Architecture

#### The Seminal Paper

**Title**: "Passage Re-ranking with BERT"
**Authors**: Rodrigo Nogueira and Kyunghyun Cho (2019)
**arXiv**: https://arxiv.org/abs/1901.04085
**Code**: https://github.com/nyu-dl/dl4marco-bert

#### Architecture Comparison

| Aspect | Bi-Encoder | Cross-Encoder |
|--------|-----------|---------------|
| **Encoding** | Query and document encoded separately | Query and document encoded jointly as `[CLS] Query [SEP] Passage [SEP]` |
| **Interaction** | Shallow — dot product/cosine at vector level | Deep — full attention between all query and passage tokens |
| **Speed** | Fast — document vectors can be pre-computed and indexed | Slow — must re-compute for every query-passage pair |
| **Scalability** | Highly scalable (ANN search over pre-computed vectors) | Does not scale to large corpora directly |
| **Accuracy** | Lower | Significantly higher |
| **Use case** | First-stage retrieval (search millions of docs) | Second-stage re-ranking (score top-k candidates, see [[ir-evaluation-benchmarking]]) |

#### Key Finding from the Paper

> "The interaction-based model [cross-encoder] correlates much better with ground-truth labels than the representation-based model [bi-encoder]. Although representation-based models are appealing due to their efficiency, their performance lags behind that of the interaction-based models in the passage reranking task."

### 4.3 Reranking in RAG Pipelines — Best Practices

#### Two-Stage Retrieve-Then-Rerank Architecture

```
User Query
    │
    ▼
┌──────────────┐    top-N (20–100)    ┌──────────────┐    top-K (3–10)    ┌─────────────┐
│  Bi-Encoder  │ ──────────────────▶  │ Cross-Encoder │ ───────────────▶  │  LLM (Gen)  │
│  Retriever   │                      │   Reranker    │                   │             │
└──────────────┘                      └──────────────┘                   └─────────────┘
   Fast, scalable                        Slow, accurate                    Answer generation
```

#### Practical Guidance

1. **Retriever pool size (N)**: 20–100 candidates. Larger N catches more relevant passages but increases reranker latency.
2. **Reranker output (K)**: 3–10 passages fed to the LLM.
3. **Hybrid retrieval**: Combine dense (embedding) + sparse (BM25) for better recall before reranking. See [[sqlite-vec-fts5-hybrid-search]] for the storage backend design.
4. **Score normalization**: Apply sigmoid to cross-encoder logits for interpretable [0,1] scores.
5. **Batch inference**: Rerank all query-passage pairs in parallel for efficiency.
6. **Domain fine-tuning**: Rerankers benefit greatly from domain-specific fine-tuning with hard negatives.
7. **Context budgeting**: Prune aggressively after reranking to stay within LLM context limits.

---

## 5. Chunking Strategies for Code vs Documentation

### 5.1 Optimal Chunk Sizes — Academic Evidence

| Chunk Size (tokens) | Overlap (%) | Use Case | Reference |
|---------------------|-------------|----------|-----------|
| 100–300 | 20–50 | QA, short abstracts, concise docs | Lewis et al. 2020 (RAG paper) |
| 256–512 | 20–50 | Full papers, technical passages | Gao et al. 2022 (ColBERTv2) |
| 128–256 | 20–50 | Long-context retrieval, QA benchmarks | TREC QA benchmarks |

**Key academic references**:
- Lewis et al. (2020). "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." arXiv:2005.11401 — Used 100-token chunks with DPR (source: docs/references/embedding-models/bibliography.md)
- Borgeaud et al. (2022). "Improving Language Models by Retrieving from Trillions of Tokens." arXiv:2112.04426 — 50% overlap improved factual recall
- Gao et al. (2022). "ColBERTv2: Effective and Efficient Retrieval." arXiv:2112.09118 — 256–512 tokens optimal for paragraph retrieval

### 5.2 Documentation Chunking Recommendations

For **documentation/prose** with BGE models (512-token limit):

1. **Chunk size**: 256–400 tokens (leave headroom for overlap)
2. **Overlap**: 50–100 tokens (20–25%)
3. **Boundary awareness**: Split at paragraph or section boundaries when possible
4. **Metadata enrichment**: Attach section headings, file path, and document title to each chunk

### 5.3 Code-Aware Chunking (AST / Tree-Sitter)

#### The cAST Paper (arXiv:2506.15655)

**Title**: "cAST: Enhancing Code Retrieval-Augmented Generation with Structural Chunking via Abstract Syntax Tree"
**Authors**: Yilin Zhang et al., CMU (2025)

**Key findings**:
- Line-based/fixed-size chunking **breaks semantic structures** — splits functions, merges unrelated code
- AST-aware chunking produces **self-contained, semantically coherent** code units
- Results: Recall@5 ↑4.3 on RepoEval, Pass@1 ↑2.67 on SWE-bench

#### AST-Aware Chunking Pipeline

```
Source Code
    │
    ▼
1. Parse to AST (tree-sitter)
    │
    ▼
2. Extract semantic entities (functions, classes, methods)
    │
    ▼
3. Build scope/context tree (nesting, imports, signatures)
    │
    ▼
4. Chunk at AST boundaries (respecting token limits)
    │
    ▼
5. Merge small siblings to reach optimal chunk size
    │
    ▼
6. Enrich with metadata (scope, imports, signatures)
```

#### Why Tree-Sitter for Code Chunking

1. **Language-agnostic**: Single parser framework for all languages
2. **Incremental parsing**: Efficient for large codebases
3. **Semantic boundaries**: Functions, classes, methods as natural chunk boundaries
4. **Context preservation**: Maintain import context, class scope, nesting
5. **Metadata extraction**: Signatures, docstrings, decorators available from AST

#### Code Chunking Recommendations for rag4you-cli

For **code** with Jina v2 (8192-token context):

1. **Primary unit**: Functions/methods as chunks (natural AST boundaries)
2. **Large functions**: Recursively split at nested block boundaries
3. **Small functions**: Merge sibling functions within the same class/module
4. **Target chunk size**: 200–500 tokens for embedding, up to 2000 for Jina's long context
5. **Context enrichment**: Prepend class name, imports, and function signature to each chunk
6. **No fixed overlap needed**: AST boundaries naturally avoid splitting semantic units

#### Available Tools

| Tool | Language | Description |
|------|----------|-------------|
| `tree-sitter` | Python/C | Standard AST parser, 100+ language grammars |
| `supermemoryai/code-chunk` | TypeScript | Production AST chunker for RAG |
| `chonkie` (CodeChunker) | TypeScript | AST-based chunking library |

### 5.4 Code vs Documentation — Strategy Comparison

| Aspect | Documentation | Code |
|--------|---------------|------|
| **Chunking method** | Sentence/paragraph boundaries | AST-aware (tree-sitter) |
| **Chunk size** | 256–400 tokens | 200–500 tokens (function-level) |
| **Overlap** | 50–100 tokens (sliding window) | None needed (AST boundaries) |
| **Context** | Section headings, doc title | Imports, class scope, signatures |
| **Embedding model** | BGE family (512 token limit) | Jina v2 Code (8192 tokens) or GTE-Qwen2 (32K) |
| **Query prefix** | `Represent this sentence for searching relevant passages:` | `Represent this query for searching relevant code:` (Nomic) or none (Jina) |

---

## 6. Model Selection Matrix for rag4you-cli

### Document Embedding Tiers

| Tier | Model | Dim | Params | FastEmbed | Max Tokens | Best For |
|------|-------|-----|--------|-----------|------------|----------|
| Small | `BAAI/bge-small-en-v1.5` | 384 | 22M | ✅ Native | 512 | Fast prototyping, low-resource |
| Medium | `BAAI/bge-base-en-v1.5` | 768 | 110M | ✅ Native | 512 | Production balance |
| Large | `BAAI/bge-large-en-v1.5` | 1024 | 355M | ✅ Native | 512 | Maximum accuracy |

### Code Embedding Tiers

| Tier | Model | Dim | Params | FastEmbed | Max Tokens | Best For |
|------|-------|-----|--------|-----------|------------|----------|
| Small | `nomic-ai/nomic-embed-code` | — | 7B | ❌ PyTorch only | — | SOTA code retrieval (heavy) |
| Medium | `jinaai/jina-embeddings-v2-base-code` | 768 | 161M | ✅ Native | 8192 | Long code files, 30+ languages |
| Large | `Alibaba-NLP/gte-Qwen2-1.5B-instruct` | 1536 | 1.5B | ❌ Transformers only | 32768 | Maximum context, multilingual |

### Reranker

| Model | Params | FastEmbed | Type | Best For |
|-------|--------|-----------|------|----------|
| `BAAI/bge-reranker-v2-m3` | 568M | ✅ Native | Cross-encoder | Multilingual reranking |

### Integration Architecture Decision

```
FastEmbed-native path (recommended for production):
├── Doc embeddings:  bge-small/base/large-en-v1.5
├── Code embeddings: jina-embeddings-v2-base-code
└── Reranking:       bge-reranker-v2-m3

Transformers/SentenceTransformers path (for maximum quality):
├── Code embeddings: nomic-embed-code (7B, SOTA)
├── Code embeddings: gte-Qwen2-1.5B-instruct (32K context)
└── (falls back to PyTorch, heavier dependencies)
```

### Practical Notes

1. **Query prefixes vary by model** — this MUST be handled per-model in code (use [[pydantic-v2]] models to enforce prefix configuration):
   - BGE: `"Represent this sentence for searching relevant passages: "`
   - Nomic: `"Represent this query for searching relevant code: "`
   - Jina v2 Code: No prefix needed
   - GTE-Qwen2: Uses instruction tuning (prompt via `prompt_name="query"`)

2. **Pooling varies by model**:
   - BGE: CLS token pooling
   - Jina v2: Mean pooling
   - Nomic Embed Code: Last-token pooling
   - GTE-Qwen2: Last-token pooling

3. **Dimension mismatch**: Doc and code embeddings live in different vector spaces. They cannot be mixed in the same index. Use separate collections/indices in [[sqlite-vec-fts5-hybrid-search]].

4. **Token limits**: BGE models truncate at 512 tokens. Jina v2 handles 8192. GTE-Qwen2 handles 32K. Chunk sizes must respect these limits (source: docs/references/embedding-models/bibliography.md).

---

## 7. References

### Papers

| ID | Title | Authors | Venue | arXiv |
|----|-------|---------|-------|-------|
| P1 | C-Pack: Packed Resources For General Chinese Embeddings | Xiao et al. | SIGIR 2024 | [2309.07597](https://arxiv.org/abs/2309.07597) |
| P2 | Passage Re-ranking with BERT | Nogueira & Cho | arXiv 2019 | [1901.04085](https://arxiv.org/abs/1901.04085) |
| P3 | CoRNStack: High-Quality Contrastive Data for Better Code Retrieval and Reranking | Reddy et al. | ICLR 2025 | [2412.01007](https://arxiv.org/abs/2412.01007) |
| P4 | Jina Embeddings 2: 8192-Token General-Purpose Text Embeddings | Günther et al. | arXiv 2023 | [2310.19923](https://arxiv.org/abs/2310.19923) |
| P5 | Towards General Text Embeddings with Multi-stage Contrastive Learning | Li et al. (Alibaba) | arXiv 2023 | [2308.03281](https://arxiv.org/abs/2308.03281) |
| P6 | cAST: Enhancing Code RAG with Structural Chunking via AST | Zhang et al. (CMU) | arXiv 2025 | [2506.15655](https://arxiv.org/abs/2506.15655) |
| P7 | Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks | Lewis et al. | NeurIPS 2020 | [2005.11401](https://arxiv.org/abs/2005.11401) |
| P8 | Improving Language Models by Retrieving from Trillions of Tokens | Borgeaud et al. | ICML 2022 | [2112.04426](https://arxiv.org/abs/2112.04426) |

### Official Model Cards

| Model | URL |
|-------|-----|
| BAAI/bge-small-en-v1.5 | https://huggingface.co/BAAI/bge-small-en-v1.5 |
| BAAI/bge-base-en-v1.5 | https://huggingface.co/BAAI/bge-base-en-v1.5 |
| BAAI/bge-large-en-v1.5 | https://huggingface.co/BAAI/bge-large-en-v1.5 |
| nomic-ai/nomic-embed-code | https://huggingface.co/nomic-ai/nomic-embed-code |
| jinaai/jina-embeddings-v2-base-code | https://huggingface.co/jinaai/jina-embeddings-v2-base-code |
| Alibaba-NLP/gte-Qwen2-1.5B-instruct | https://huggingface.co/Alibaba-NLP/gte-Qwen2-1.5B-instruct |
| BAAI/bge-reranker-v2-m3 | https://huggingface.co/BAAI/bge-reranker-v2-m3 |

### Official Documentation

| Resource | URL |
|----------|-----|
| FastEmbed Docs | https://qdrant.github.io/fastembed/ |
| FastEmbed GitHub | https://github.com/qdrant/fastembed |
| FastEmbed Supported Models | https://qdrant.github.io/fastembed/examples/Supported_Models/ |
| FlagEmbedding GitHub | https://github.com/FlagOpen/FlagEmbedding |
| MTEB Leaderboard | https://huggingface.co/spaces/mteb/leaderboard |
| Tree-sitter | https://tree-sitter.github.io/tree-sitter/ |

## Related pages

- [[sqlite-vec-fts5-hybrid-search]]
- [[rag-research-compendium]]
- [[ir-evaluation-benchmarking]]
- [[python-uv]]
- [[pydantic-v2]]
- [[tiktoken]]
