# RAG Foundations — Source Bibliography

**Compiled**: 2025-07-22
**Purpose**: Bibliographic reference for RAG academic papers and official documentation used in wiki/knowledge/rag-research-compendium.md

---

## Foundational papers

### 1. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
- **Authors**: Lewis, Perez, Piktus, Petroni, Karpukhin, Goyal, Küttler, Lewis, Yih, Rocktäschel, Riedel, Kiela
- **Venue**: NeurIPS 2020
- **URL**: https://arxiv.org/abs/2005.11401
- **DOI**: 10.48550/arXiv.2005.11401
- **Key contribution**: Introduced RAG architecture combining parametric memory (BART seq2seq) with non-parametric memory (dense vector index). Two variants: RAG-Sequence (same document for entire output) and RAG-Token (different document per token). Achieves state-of-the-art on open-domain QA without task-specific architectures.

### 2. Dense Passage Retrieval for Open-Domain Question Answering
- **Authors**: Karpukhin, Oguz, Min, Lewis, Wu, Edunov, Chen, Yih
- **Venue**: EMNLP 2020
- **URL**: https://arxiv.org/abs/2004.04906
- **Key contribution**: Dense retrieval using dual-encoder BERT models outperforms BM25 on open-domain QA. Foundation for modern RAG retrieval.

### 3. ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT
- **Authors**: Khattab, Zaharia
- **Venue**: SIGIR 2020
- **URL**: https://arxiv.org/abs/2004.12832
- **Key contribution**: Late interaction architecture: encode queries and documents independently, then perform fine-grained matching via MaxSim. Balances efficiency and effectiveness.

## Surveys and best practices

### 4. Retrieval-Augmented Generation for Large Language Models: A Survey
- **Authors**: Gao, Xiong, Gao, Jia, Pan, Bi, Dai, Sun, Wang, Wang
- **Venue**: arXiv 2024
- **URL**: https://arxiv.org/abs/2312.10997
- **Key contribution**: Defines Naive RAG → Advanced RAG → Modular RAG taxonomy. Comprehensive survey of retrieval, generation, and augmentation techniques.

### 5. Searching for Best Practices in Retrieval-Augmented Generation
- **Authors**: Wang, Yang, Zhu, Wang, Lin, Wan, Bai, Liu
- **Venue**: EMNLP 2024
- **URL**: https://arxiv.org/abs/2407.01219
- **Key contribution**: Empirical evaluation of RAG pipeline components. Findings: hybrid search (vector + BM25) outperforms either alone; reranking consistently improves quality; chunk size of 512 tokens with 10% overlap is a robust default.

## Hybrid search

### 6. Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods
- **Authors**: Cormack, Clarke, Butt
- **Venue**: SIGIR 2009
- **URL**: https://dl.acm.org/doi/10.1145/1571941.1572114
- **Key contribution**: RRF formula `score(d) = Σ 1/(k + rank(d))` with k=60. Rank-based fusion requires no score normalization. Outperforms individual rankers and Condorcet methods.

### 7. Blended RAG: Improving RAG Accuracy with Semantic Search and Hybrid Query-Based Retrievers
- **Authors**: Sawarkar, Mangal, Solanki
- **Venue**: IEEE-MIPR 2024
- **URL**: https://arxiv.org/abs/2404.07220
- **Key contribution**: Demonstrates that combining dense retrieval, sparse retrieval (BM25), and semantic search with RRF consistently outperforms single-retriever approaches.

## Advanced RAG paradigms

### 8. Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection
- **Authors**: Asai, Wu, Wang, Sil, Hajishirzi
- **Venue**: ICLR 2024
- **URL**: https://arxiv.org/abs/2310.11511
- **Key contribution**: LLM learns to adaptively retrieve and self-reflect using special tokens. Decides when to retrieve, which passages to use, and whether generation is supported by evidence.

### 9. Corrective Retrieval Augmented Generation (CRAG)
- **Authors**: Yan, Li, Zhang, Du, Zhao
- **Venue**: arXiv 2024
- **URL**: https://arxiv.org/abs/2401.15884
- **Key contribution**: Lightweight retrieval evaluator assesses relevance of retrieved documents. Triggers corrective actions: if low confidence → web search fallback; if medium → knowledge refinement.

### 10. GraphRAG: Unlocking LLM Discovery on Narrative Private Data
- **Authors**: Edge, Trinh, Cheng, Bradley, Chao, Mody, Truitt, Larson
- **Venue**: arXiv 2024 (Microsoft Research)
- **URL**: https://arxiv.org/abs/2404.16130
- **Key contribution**: Uses LLM-generated knowledge graphs with community detection for summarization. Excels at global questions that require synthesizing information across many documents.

## Chunking and contextual retrieval

### 11. Contextual Retrieval
- **Authors**: Anthropic
- **Venue**: Anthropic Research Blog, September 2024
- **URL**: https://www.anthropic.com/news/contextual-retrieval
- **Key contribution**: Prepending document-level context to each chunk before embedding reduces retrieval failures by 49% (contextual embeddings alone) to 67% (contextual embeddings + BM25 + reranking).

## Query transformation

### 12. Query Rewriting for Retrieval-Augmented Large Language Models
- **Authors**: Ma, Gao, Abubakar, Sun, Shi
- **Venue**: EMNLP 2023
- **URL**: https://arxiv.org/abs/2305.14283
- **Key contribution**: Training a small rewriter model to transform queries before retrieval. Improves performance without modifying the LLM or retriever.

### 13. Decomposed Prompting: A Modular Approach for Solving Complex Tasks
- **Authors**: Khot, Trivedi, Finlayson, Fu, Richardson, Clark, Sabharwal
- **Venue**: ICLR 2023
- **URL**: https://arxiv.org/abs/2210.02406
- **Key contribution**: Decompose complex queries into sub-questions handled by specialized modules. Foundation for multi-step RAG retrieval.

## Evaluation

### 14. Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference (LLM-as-a-Judge)
- **Authors**: Zheng, Chiang, Sheng, Zhuang, Wu, Zhuang, Lin, Li, Li, Xing, Zhang, Gonzalez, Stoica
- **Venue**: NeurIPS 2023
- **URL**: https://arxiv.org/abs/2306.05685
- **Key contribution**: Strong LLMs (GPT-4 class) achieve >80% agreement with human judges. Foundation for using LLMs as evaluation judges in RAG benchmarks. Recommends temperature=0 for deterministic evaluation.

### 15. RAGAS: Automated Evaluation of Retrieval Augmented Generation
- **Authors**: Es, James, Espinosa-Anke, Schockaert
- **Venue**: EACL 2024
- **URL**: https://arxiv.org/abs/2309.15217
- **Official docs**: https://docs.ragas.io/
- **Key contribution**: Framework defining faithfulness, answer relevance, context precision, and context recall metrics for RAG evaluation without human annotations.

### 16. ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems
- **Authors**: Saad-Falcon, Khattab, Potts, Zaharia
- **Venue**: NAACL 2024
- **URL**: https://arxiv.org/abs/2311.09476
- **Key contribution**: Uses fine-tuned classifier judges on synthetic data. Evaluates context relevance, answer faithfulness, and answer relevance. More cost-effective than pure LLM-as-judge approaches.

## Local/offline RAG

### 17. Contextual Retrieval (local components)
- **Source**: Anthropic documentation
- **URL**: https://www.anthropic.com/news/contextual-retrieval
- **Key insight**: Full local RAG stack: sentence-transformers or fastembed for embeddings, SQLite + sqlite-vec for storage, BM25 via FTS5 for keyword search, cross-encoder for reranking.

### 18. FastEmbed documentation
- **Source**: Qdrant
- **URL**: https://qdrant.github.io/fastembed/
- **Key insight**: ONNX runtime enables CPU-only inference with no GPU dependency. Pre-quantized models for fast local embedding generation.
