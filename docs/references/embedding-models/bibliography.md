# Embedding Models — Source Bibliography

**Compiled**: 2025-07-22
**Purpose**: Bibliographic reference for embedding models and FastEmbed sources used in wiki/knowledge/embedding-models-research.md

---

## FastEmbed

### Official documentation
- **URL**: https://qdrant.github.io/fastembed/
- **GitHub**: https://github.com/qdrant/fastembed
- **PyPI**: https://pypi.org/project/fastembed/
- **Key facts**: ONNX Runtime based (no PyTorch), CPU-optimized, pre-quantized models, data parallelism built-in. Supports dense, sparse, late-interaction, and cross-encoder models.

## BGE Embedding Models (BAAI)

### BGE technical report
- **Title**: C-Pack: Packaged Resources To Advance General Chinese Embedding
- **Authors**: Xiao, Liu, Shao, Cao, Bian, Luo, Feng, Li, Qu
- **Venue**: arXiv 2023
- **URL**: https://arxiv.org/abs/2309.07597
- **Key contribution**: Training methodology for BGE models using contrastive learning with hard negatives. v1.5 fixed similarity distribution clustering from v1.0.

### Model cards
| Model | HuggingFace URL | Dimensions | Max tokens | Size |
|---|---|---|---|---|
| BAAI/bge-small-en-v1.5 | https://huggingface.co/BAAI/bge-small-en-v1.5 | 384 | 512 | 33M params |
| BAAI/bge-base-en-v1.5 | https://huggingface.co/BAAI/bge-base-en-v1.5 | 768 | 512 | 109M params |
| BAAI/bge-large-en-v1.5 | https://huggingface.co/BAAI/bge-large-en-v1.5 | 1024 | 512 | 335M params |

### MTEB Benchmark
- **Title**: MTEB: Massive Text Embedding Benchmark
- **Authors**: Muennighoff, Tazi, Magne, Reimers
- **Venue**: EACL 2023
- **URL**: https://arxiv.org/abs/2210.07316
- **Leaderboard**: https://huggingface.co/spaces/mteb/leaderboard
- **Key insight**: BGE models rank consistently in top tier for retrieval tasks among models of similar parameter count.

## Code Embedding Models

### Jina Embeddings v2 for Code
- **HuggingFace**: https://huggingface.co/jinaai/jina-embeddings-v2-base-code
- **Key facts**: 768 dimensions, 8192 token context (ALiBi position extrapolation), Apache-2.0 license, 161M params. Ideal for long code files.

### Nomic Embed Code
- **HuggingFace**: https://huggingface.co/nomic-ai/nomic-embed-code
- **Note**: Large model (7B params), requires PyTorch/Transformers — NOT available via FastEmbed ONNX. Alternative `nomic-embed-text-v1.5` (768d, Apache-2.0) IS available in FastEmbed.

### GTE-Qwen2
- **Title**: mGTE: Generalized Long-Context Text Representation and Reranking Models for Multilingual Text Retrieval
- **HuggingFace**: https://huggingface.co/Alibaba-NLP/gte-Qwen2-1.5B-instruct
- **Key facts**: 1536 dimensions, 1.5B params, requires PyTorch — NOT available via FastEmbed ONNX.
- **Note**: Implementation must handle this model via transformers library, not FastEmbed.

## Cross-Encoder Reranking

### BGE Reranker v2 M3
- **HuggingFace**: https://huggingface.co/BAAI/bge-reranker-v2-m3
- **Key facts**: 568M params, cross-encoder architecture (encodes query+document jointly), multilingual. Available in FastEmbed via `TextCrossEncoder`.

### Cross-encoder architecture
- **Title**: Passage Re-ranking with BERT
- **Authors**: Nogueira, Cho
- **Venue**: arXiv 2019
- **URL**: https://arxiv.org/abs/1901.04085
- **Key contribution**: Joint encoding of query-document pairs through BERT produces richer interaction signals than bi-encoder (independent encoding). More accurate but more expensive.

## Chunking Strategies

### Code-aware chunking
- **Title**: cAST: Code-Aware Semantic Chunking for Retrieval-Augmented Generation in Software Engineering
- **Authors**: CMU researchers
- **Venue**: arXiv 2025
- **Key finding**: AST-aware chunking improves Recall@5 by +4.3 over line-based chunking for code retrieval tasks.

### General chunking
- **Source**: LlamaIndex documentation
- **URL**: https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/
- **Key patterns**: SentenceSplitter (default), TokenTextSplitter, SemanticSplitter, CodeSplitter (tree-sitter based)
