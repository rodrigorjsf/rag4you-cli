# RAG Research Compendium

**Summary**: Comprehensive reference on RAG architectures, retrieval techniques, chunking strategies, reranking, advanced paradigms, and token economy for LLM-based systems.
**Sources**: `docs/references/rag-foundations/bibliography.md`
**Last updated**: 2025-07-22
---

## Table of Contents

1. [Foundational Paper — Lewis et al. (2020)](#1-foundational-paper--lewis-et-al-2020)
2. [Comprehensive RAG Survey — Gao et al. (2024)](#2-comprehensive-rag-survey--gao-et-al-2024)
3. [RAG Best Practices — Wang et al. EMNLP 2024](#3-rag-best-practices--wang-et-al-emnlp-2024)
4. [Retrieval Techniques](#4-retrieval-techniques)
   - 4.1 [Dense Passage Retrieval (DPR)](#41-dense-passage-retrieval-dpr)
   - 4.2 [ColBERT — Late Interaction Retrieval](#42-colbert--late-interaction-retrieval)
   - 4.3 [Hybrid Search and Reciprocal Rank Fusion](#43-hybrid-search-and-reciprocal-rank-fusion)
   - 4.4 [Blended RAG — Sawarkar et al. IEEE-MIPR 2024](#44-blended-rag--sawarkar-et-al-ieee-mipr-2024)
5. [Chunking Strategies](#5-chunking-strategies)
   - 5.1 [Fixed-Size Chunking](#51-fixed-size-chunking)
   - 5.2 [Semantic and Recursive Chunking](#52-semantic-and-recursive-chunking)
   - 5.3 [Contextual Retrieval — Anthropic (2024)](#53-contextual-retrieval--anthropic-2024)
   - 5.4 [LlamaIndex Node Parsers](#54-llamaindex-node-parsers)
6. [Reranking Strategies](#6-reranking-strategies)
7. [Query Decomposition and Transformation](#7-query-decomposition-and-transformation)
8. [Advanced RAG Paradigms](#8-advanced-rag-paradigms)
   - 8.1 [Self-RAG — Adaptive Retrieval](#81-self-rag--adaptive-retrieval)
   - 8.2 [CRAG — Corrective RAG](#82-crag--corrective-rag)
   - 8.3 [GraphRAG — Knowledge Graph RAG](#83-graphrag--knowledge-graph-rag)
9. [Evaluation Metrics and Frameworks](#9-evaluation-metrics-and-frameworks)
10. [Token Economy and Efficiency](#10-token-economy-and-efficiency)
11. [Local and Offline RAG](#11-local-and-offline-rag)
12. [Quick Reference — Paper Index](#12-quick-reference--paper-index)

---

## 1. Foundational Paper — Lewis et al. (2020)

**Title:** Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks  
**Authors:** Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, Douwe Kiela  
**Venue:** NeurIPS 2020  
**URL:** <https://arxiv.org/abs/2005.11401>  
**DOI:** `10.48550/arXiv.2005.11401`

### Core Idea

RAG combines a **parametric memory** (a pre-trained seq2seq model such as BART) with a **non-parametric memory** (a dense vector index of documents accessed via a neural retriever) (source: docs/references/rag-foundations/bibliography.md). The system retrieves relevant passages at inference time and conditions generation on them.

> "We explore a general-purpose fine-tuning recipe for retrieval-augmented
> generation (RAG) — models which combine pre-trained parametric and
> non-parametric memory for language generation."
> — Lewis et al. (2020), Abstract

### Architecture

```
Query ──► Retriever (DPR) ──► Top-K passages
                                    │
Query + Passages ──► Generator (BART/T5) ──► Output
```

1. **Retriever:** Dense Passage Retriever (DPR) encodes queries and passages with bi-encoders (BERT-based). Retrieval uses maximum inner-product search (MIPS) over pre-computed passage embeddings.
2. **Generator:** A seq2seq transformer (BART) generates output conditioned on both the query and retrieved passages.
3. **Marginalization:** The final output probability marginalizes over the retrieved documents.

### Two Variants

| Variant | Marginalization | Behavior |
|---------|----------------|----------|
| **RAG-Sequence** | Per-sequence | Same document conditions the entire generated sequence |
| **RAG-Token** | Per-token | Can switch documents at every generation step |

### Training

- **End-to-end:** Retriever and generator are trained jointly.
- **Loss:** Negative log-likelihood over generated sequences.
- **Distant supervision:** No explicit document-level labels needed — the downstream task signal trains the retriever.

### Key Results

- State-of-the-art on three open-domain QA benchmarks (NaturalQuestions, WebQuestions, CuratedTrec).
- RAG generates more specific, diverse, and factual language than parametric-only baselines.
- Provides provenance: the retrieved documents serve as citations.

### Implementation Insights

- The retriever index can be refreshed independently of the generator, enabling knowledge updates without retraining.
- Top-K is typically set to 5–10 for QA tasks.
- The marginalization approach matters: RAG-Token is more flexible but computationally heavier.

---

## 2. Comprehensive RAG Survey — Gao et al. (2024)

**Title:** Retrieval-Augmented Generation for Large Language Models: A Survey  
**Authors:** Yunfan Gao et al.  
**URL:** <https://arxiv.org/abs/2312.10997>  
**DOI:** `10.48550/arXiv.2312.10997`

### RAG Paradigm Taxonomy

The survey identifies three evolutionary paradigms:

| Paradigm | Description |
|----------|-------------|
| **Naive RAG** | Simple retrieve-then-generate: chunk → embed → retrieve → generate |
| **Advanced RAG** | Adds pre-retrieval optimization (query rewriting), post-retrieval processing (reranking, compression), and iterative retrieval |
| **Modular RAG** | Decomposes RAG into interchangeable modules: routing, scheduling, fusion strategies, and tool integration |

### Tripartite Framework

1. **Retrieval:** Sparse (BM25), dense (DPR, ColBERT), hybrid, and learned retrieval.
2. **Augmentation:** How retrieved content is integrated — concatenation, fusion-in-decoder, cross-attention, iterative refinement.
3. **Generation:** Constrained decoding, faithful generation, attribution.

### Key Challenges Identified

- **Retrieval quality** is the single largest bottleneck.
- **Context window saturation**: More context is not always better — noise degrades output.
- **Evaluation**: No single metric captures all dimensions (faithfulness, relevance, factuality).
- **Scalability**: Retrieval latency grows with corpus size.

---

## 3. RAG Best Practices — Wang et al. EMNLP 2024

**Title:** Searching for Best Practices in Retrieval-Augmented Generation  
**Authors:** Xiaohua Wang, Zhenghua Wang, Xuan Gao, Feiran Zhang et al. (Fudan University)  
**Venue:** EMNLP 2024 (Proceedings, pp. 17716–17736)  
**URL:** <https://arxiv.org/abs/2407.01219>  
**Code:** <https://github.com/FudanDNN-NLP/RAG>

### Workflow Components Evaluated

The paper decomposes a RAG pipeline into **five processing steps** and benchmarks multiple implementations for each:

1. **Query Classification:** Determine if retrieval is needed at all.
2. **Retrieval:** Compare sparse, dense, and hybrid retrievers.
3. **Reranking:** Cross-encoder rerankers significantly boost precision.
4. **Repacking:** How to arrange retrieved passages in the prompt.
5. **Summarization:** Compress retrieved content to fit context windows.

### Key Findings

- **Hybrid retrieval** (BM25 + dense) consistently outperforms either alone (source: docs/references/rag-foundations/bibliography.md).
- **Reranking** provides the highest single-component improvement (source: docs/references/rag-foundations/bibliography.md).
- **Retrieval is optional** for simple factual queries the LLM already knows — a classification step saves latency.
- **Multimodal retrieval** significantly enhances visual QA tasks.

### Practical Recommendations

- Start with hybrid retrieval + cross-encoder reranking as the baseline.
- Use query classification to skip retrieval when unnecessary.
- Compress long retrieved passages before feeding to the generator.
- Balance performance vs. latency — each additional component adds delay.

---

## 4. Retrieval Techniques

### 4.1 Dense Passage Retrieval (DPR)

**Title:** Dense Passage Retrieval for Open-Domain Question Answering  
**Authors:** Vladimir Karpukhin, Barlas Oğuz, Sewon Min, Patrick Lewis, Ledell Wu, Sergey Edunov, Danqi Chen, Wen-tau Yih  
**Venue:** EMNLP 2020  
**URL:** <https://arxiv.org/abs/2004.04906>

**Key concepts:**
- Bi-encoder architecture: separate BERT encoders for queries and passages (source: docs/references/rag-foundations/bibliography.md).
- Retrieval via Maximum Inner Product Search (MIPS) over pre-computed passage embeddings.
- Trained with in-batch negatives and hard negatives from BM25.
- Dramatically outperforms BM25 on open-domain QA when trained on sufficient data.

See [[embedding-models-research]] for a detailed comparison of embedding models used in retrieval.

**Implementation notes:**
- Use FAISS for efficient approximate nearest-neighbor search.
- Hard negative mining during training is critical for performance.
- Pre-computed passage embeddings enable real-time retrieval from millions of documents.

---

### 4.2 ColBERT — Late Interaction Retrieval

**Title:** ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT  
**Authors:** Omar Khattab, Matei Zaharia (Stanford)  
**URL:** <https://arxiv.org/abs/2004.12832>  
**Code:** <https://github.com/stanford-futuredata/ColBERT>

**Key innovation — Late Interaction:**
- Unlike bi-encoders (single-vector), ColBERT produces **per-token embeddings** for both queries and passages.
- Matching uses **MaxSim** — the maximum similarity between each query token and all passage tokens, then summed.
- This provides cross-encoder-like expressiveness with bi-encoder-like efficiency.

```
Score(q, d) = Σ_i max_j sim(q_i, d_j)
```

**Why it matters for RAG:**
- Passage representations are precomputed and stored.
- Query encoding happens on-the-fly.
- Achieves strong recall with low latency — ideal for first-stage retrieval in RAG pipelines.

---

### 4.3 Hybrid Search and Reciprocal Rank Fusion

**Concept:** Combine dense (semantic/vector) and sparse (keyword/BM25) retrieval to capture both semantic meaning and exact lexical matches. See [[sqlite-vec-fts5-hybrid-search]] for a SQLite-based implementation approach.

**Reciprocal Rank Fusion (RRF):**

**Reference:** Cormack, G. V., Clarke, C. L. A., & Buettcher, S. (2009). "Reciprocal rank fusion outperforms Condorcet and individual rank learning methods." *SIGIR '09*, pp. 758–759.

**Formula:**

```
RRF(d) = Σ_{i=1}^{k} 1 / (rank_i(d) + c)
```

Where:
- `k` = number of ranking lists (retrieval methods)
- `rank_i(d)` = rank of document `d` in the i-th list
- `c` = smoothing constant (typically 60)

**Implementation pseudocode:**

```python
def reciprocal_rank_fusion(rankings: list[dict], c: int = 60) -> dict:
    """Fuse multiple ranked lists using RRF."""
    scores = {}
    for rank_list in rankings:
        for doc_id, rank in rank_list.items():
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (rank + c)
    return dict(sorted(scores.items(), key=lambda x: -x[1]))
```

**Why hybrid search works:**
- Dense retrieval captures semantic similarity ("revenue growth" matches "income increase").
- BM25 captures exact terms ("Error code TS-999", specific identifiers).
- RRF combines their strengths without requiring score normalization.

---

### 4.4 Blended RAG — Sawarkar et al. IEEE-MIPR 2024

**Title:** Blended RAG: Improving RAG Accuracy with Semantic Search and Hybrid Query-Based Retrievers  
**Authors:** Kunal Sawarkar et al.  
**Venue:** IEEE-MIPR 2024  
**URL:** <https://arxiv.org/abs/2404.07220>  
**DOI:** `10.1109/MIPR62202.2024.00031`

> "We propose the 'Blended RAG' method of leveraging semantic search
> techniques, such as Dense Vector indexes and Sparse Encoder indexes,
> blended with hybrid query strategies."
> — Sawarkar et al. (2024), Abstract

**Key contributions:**
- Blends dense vector indexes with sparse encoder indexes using hybrid query strategies.
- Sets new benchmarks on NQ and TREC-COVID retrieval datasets.
- When applied end-to-end in a RAG system, surpasses fine-tuning on SQUAD QA benchmark.

**Practical takeaway:** Hybrid retrieval is not just a convenience — it establishes a new performance ceiling for RAG accuracy (source: docs/references/rag-foundations/bibliography.md). See also [[sqlite-vec-fts5-hybrid-search]] for hybrid search implementation details.

---

## 5. Chunking Strategies

Chunking is the process of splitting documents into retrievable units. The choice of strategy directly impacts retrieval precision and downstream generation quality.

### 5.1 Fixed-Size Chunking

**Method:** Split text by character or token count (e.g., 256–512 tokens per chunk).

**Advantages:**
- Simple to implement.
- Predictable chunk sizes for embedding models with token limits.

**Disadvantages:**
- Cuts across semantic boundaries (sentences, paragraphs).
- Loss of context — a chunk may reference entities defined in a different chunk.

**Best for:** Homogeneous, well-structured documents where sections are uniform.

**Implementation (LangChain):**

```python
from langchain.text_splitter import CharacterTextSplitter

splitter = CharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    separator="\n"
)
chunks = splitter.split_text(document_text)
```

---

### 5.2 Semantic and Recursive Chunking

**Semantic Chunking** splits text at natural boundaries (sentences, paragraphs, topic shifts) using NLP heuristics or embedding similarity.

**Recursive Chunking** uses a hierarchy of separators, trying the most natural first:

```
1. Double newline (\n\n) → paragraph boundaries
2. Single newline (\n)   → line boundaries
3. Sentence endings (. ! ?)
4. Word boundaries (space)
5. Character-level (fallback)
```

**Academic evidence:** Comparative evaluations (EMNLP 2024, Bioengineering 2025) confirm that adaptive and semantic chunking outperform fixed-size chunking in precision, recall, and downstream answer correctness.

**References:**
- "Searching for Best Practices in RAG" — EMNLP 2024 (<https://aclanthology.org/2024.emnlp-main.981>)
- "Comparative Evaluation of Advanced Chunking for RAG in LLMs for Clinical Decision Support" — Bioengineering 2025 (<https://www.mdpi.com/2306-5354/12/11/1194>)

**Best practices:**
- Preserve semantic boundaries where possible.
- Allow overlap (50–100 tokens) for context retention across chunk boundaries.
- Enrich chunks with metadata (source, section title, page number).
- Experiment with chunk sizes — optimal size varies by domain (financial docs may work best with 1,024 tokens; prose with 256–512).

---

### 5.3 Contextual Retrieval — Anthropic (2024)

**Source:** Anthropic Official Blog  
**URL:** <https://www.anthropic.com/news/contextual-retrieval>  
**Cookbook:** <https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide>

**The Problem:** Traditional chunking strips context. A chunk saying _"The company's revenue grew by 3%"_ loses which company, which quarter, and what the baseline was.

**The Solution — Contextual Chunk Enrichment:**

For each chunk, use an LLM to generate a 1–2 sentence context summary, then **prepend** it to the chunk before embedding and indexing.

**Prompt template:**

```
<document>
{{WHOLE_DOCUMENT}}
</document>
Here is the chunk we want to situate within the whole document
<chunk>
{{CHUNK_CONTENT}}
</chunk>
Please give a short succinct context to situate this chunk within the
overall document for the purposes of improving search retrieval of the chunk.
Answer only with the succinct context and nothing else.
```

**Example transformation:**

| Before | After |
|--------|-------|
| "The company's revenue grew by 3% over the previous quarter." | "This chunk is from an SEC filing on ACME Corp's performance in Q2 2023; the previous quarter's revenue was $314 million. The company's revenue grew by 3% over the previous quarter." |

**Measured results (Anthropic benchmarks):**

| Configuration | Retrieval Failure Rate (top-20) | Reduction |
|--------------|-------------------------------|-----------|
| Baseline embedding | 5.7% | — |
| + Contextual Embeddings | 3.7% | −35% |
| + Contextual Embeddings + Contextual BM25 | 2.9% | −49% |
| + Contextual Embeddings + Contextual BM25 + Reranking | 1.9% | −67% |

**Implementation considerations:**
- **Cost:** ~$1.02 per million document tokens (with prompt caching).
- **Chunk boundaries:** Choice of chunk size and overlap still matters.
- **Custom prompts:** Domain-specific contextualizer prompts improve results further (e.g., include a glossary).
- **Chunk count:** Anthropic found 20 chunks optimal among 5, 10, and 20.
- **Small knowledge bases** (< 200K tokens / ~500 pages): Consider putting everything in the prompt instead of RAG.

---

### 5.4 LlamaIndex Node Parsers

**Source:** LlamaIndex Official Documentation  
**URL:** <https://developers.llamaindex.ai/python/framework/module_guides/loading/node_parsers/modules/>

LlamaIndex provides modular node parsers for different data types:

| Parser | Use Case |
|--------|----------|
| `SentenceSplitter` | General text — splits by sentences with configurable size and overlap |
| `MarkdownNodeParser` | Markdown documents — respects heading structure |
| `HTMLNodeParser` | HTML — uses BeautifulSoup for tag-aware splitting |
| `JSONNodeParser` | Structured JSON data |
| `CodeSplitter` | Source code — respects function/class boundaries |
| `SimpleFileNodeParser` | Auto-selects parser based on file type |

```python
from llama_index.core.node_parser import SentenceSplitter

splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
nodes = splitter.get_nodes_from_documents(documents)
```

**Key insight:** Use structure-aware parsers for structured documents (HTML, Markdown, code) and sentence/semantic splitters for prose. Chain file-based parsers with text-based parsers for fine-grained control.

---

## 6. Reranking Strategies

Reranking is a **post-retrieval** step that rescores candidate chunks for relevance before passing them to the generator.

### Why Reranking Matters

Initial retrieval (whether dense or sparse) optimizes for recall — it casts a wide net. Reranking optimizes for precision — it selects the most relevant results from the candidate set.

### Cross-Encoder Reranking

**How it works:**
1. Retrieve top-N candidates (e.g., N=150) using fast first-stage retrieval.
2. Pass each (query, passage) pair through a cross-encoder model.
3. The cross-encoder produces a single relevance score per pair.
4. Select top-K results (e.g., K=20) for the generator.

**Key models:**
- `cross-encoder/ms-marco-MiniLM-L-6-v2` — lightweight, runs locally
- Cohere Rerank — cloud API
- Voyage Reranker — cloud API

**Trade-offs:**

| Aspect | First-Stage Retrieval | Reranking |
|--------|----------------------|-----------|
| Speed | Fast (embeddings precomputed) | Slower (runs per query-passage pair) |
| Accuracy | Good recall, moderate precision | High precision |
| Scalability | Handles millions of documents | Applied only to top-N candidates |

### Impact

Per Anthropic's benchmarks, adding reranking to contextual retrieval reduces failure rates by an additional **36%** beyond contextual embeddings alone (from 2.9% → 1.9%).

Per the EMNLP 2024 best practices paper, reranking provides **the highest single-component improvement** in a RAG pipeline.

---

## 7. Query Decomposition and Transformation

Complex queries often require multi-step reasoning. Query transformation techniques rewrite or decompose queries to improve retrieval.

### Techniques

#### Multi-Query Rewriting

**Paper:** DMQR-RAG: Diverse Multi-Query Rewriting for RAG  
**URL:** <https://arxiv.org/abs/2411.13154>

Generate multiple diverse versions of the original query at different information levels. Retrieve for each version and merge results.

#### Query Decomposition

**Paper:** Query Decomposition for RAG: Balancing Exploration-Exploitation  
**URL:** <https://arxiv.org/abs/2510.18633>

Break complex queries into independent subqueries. Frame document retrieval as a multi-armed bandit problem, balancing exploration of new subqueries vs. exploitation of known relevant ones.

#### Step-Back Prompting

Ask the LLM to generate a more abstract, higher-level version of the query. Retrieve based on both the original and the step-back query.

```
Original:  "What was ACME Corp's Q2 2023 EBITDA margin?"
Step-back: "What were ACME Corp's financial performance metrics in 2023?"
```

#### Query Refinement

**Paper:** RQ-RAG: Learning to Refine Queries for Retrieval Augmented Generation  
**URL:** <https://arxiv.org/abs/2404.00610>

Train the LLM to explicitly rewrite, decompose, and disambiguate queries before retrieval. Outperforms state-of-the-art on both single-hop and multi-hop QA.

#### Adaptive Topic-Filtered Retrieval

**Paper:** AT-RAG: An Adaptive RAG Model Enhancing Query Efficiency with Topic Filtering  
**URL:** <https://arxiv.org/abs/2410.12886>

Uses BERTopic for topic modeling to filter and transform queries adaptively, improving relevance for domain-specific retrieval.

#### Multi-Agent Query Processing

**Paper:** MA-RAG: Multi-Agent RAG via Collaborative Chain-of-Thought Reasoning  
**URL:** <https://arxiv.org/abs/2505.20096>

Specialized agents (Planner, Step Definer, Extractor, QA Agent) decompose tasks into subtasks and collaboratively refine retrieval and reasoning.

### Multi-Hop Benchmark

**Paper:** MultiHop-RAG: Benchmarking RAG for Multi-Hop Queries  
**URL:** <https://arxiv.org/abs/2401.15391>

Demonstrates that current RAG systems struggle with multi-hop queries requiring sequential reasoning across multiple passages. Provides a benchmark for future evaluation.

---

## 8. Advanced RAG Paradigms

### 8.1 Self-RAG — Adaptive Retrieval

**Title:** Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection  
**Authors:** Akari Asai, Zeqiu Wu, Yizhong Wang, Avirup Sil, Hannaneh Hajishirzi  
**Venue:** ICLR 2024  
**URL:** <https://arxiv.org/abs/2310.11511>

> "We introduce Self-RAG that enhances an LM's quality and factuality
> through retrieval and self-reflection. Our framework trains a single
> arbitrary LM that adaptively retrieves passages on-demand, and generates
> and reflects on retrieved passages and its own generations using special
> tokens, called reflection tokens."
> — Asai et al. (2023), Abstract

**Key innovations:**
- **Adaptive retrieval:** The model decides when retrieval is needed (not always).
- **Reflection tokens:** Special tokens signal whether retrieved passages are relevant, whether the generation is supported, and whether it is useful.
- **Controllable inference:** Reflection tokens enable tuning the trade-off between factuality and creativity at inference time.

**Pipeline:**

```
1. Query → LM decides: "Do I need retrieval?" (via [Retrieve] token)
2. If yes → Retrieve passages → [IsRel] token evaluates relevance
3. Generate response → [IsSup] token checks if supported by evidence
4. [IsUse] token evaluates overall utility
```

**Results:** Self-RAG (7B/13B) outperforms ChatGPT and Llama2-chat with retrieval on open-domain QA, reasoning, and fact verification tasks (source: docs/references/rag-foundations/bibliography.md).

---

### 8.2 CRAG — Corrective RAG

**Title:** Corrective Retrieval Augmented Generation  
**Authors:** Shi-Qi Yan et al.  
**URL:** <https://arxiv.org/abs/2401.15884>

**Key innovation — Retrieval Evaluation and Correction:**

1. A lightweight **retrieval evaluator** (fine-tuned T5-large) scores retrieved documents as: **Correct**, **Incorrect**, or **Ambiguous**.
2. For **Correct** evidence: decompose-then-recompose — extract, filter, and recombine only relevant knowledge.
3. For **Incorrect** evidence: discard and fall back to web search.
4. For **Ambiguous** evidence: combine both strategies.

**Key insight:** Not all retrieved documents help. Actively evaluating and correcting retrieval quality before generation significantly reduces hallucinations.

**Results:** Consistent improvements over vanilla RAG across four datasets including both short-form and long-form generation tasks.

---

### 8.3 GraphRAG — Knowledge Graph RAG

**Title:** From Local to Global: A Graph RAG Approach to Query-Focused Summarization  
**Authors:** Microsoft Research  
**URL:** <https://arxiv.org/abs/2404.16130>

**Key concepts:**

1. **Knowledge Graph Construction:** Extract entities and relationships from the corpus into a knowledge graph.
2. **Community Detection:** Cluster related nodes into communities using graph algorithms.
3. **Community Summaries:** Generate LLM summaries for each community.
4. **Two Search Modes:**
   - **Local Search:** Start from query-anchored nodes, explore neighborhoods.
   - **Global Search:** Aggregate community summaries across the entire graph.

**When to use GraphRAG:**
- When queries require synthesis across many documents ("What are the main themes?").
- When the corpus has rich entity relationships.
- When disambiguation is important (same term, different contexts).

**Trade-off:** Higher preprocessing cost (graph construction + community summarization) but better answers for global/thematic queries.

---

## 9. Evaluation Metrics and Frameworks

RAG evaluation spans two complementary dimensions: **retrieval quality** (did we find the right passages?) and **generation quality** (did we produce a faithful, relevant answer?) (source: docs/references/rag-foundations/bibliography.md). Standard retrieval metrics such as Precision@k, Recall@k, MRR, and NDCG@k measure how well the retriever surfaces relevant documents. On the generation side, frameworks like RAGAS evaluate faithfulness, answer relevancy, and context precision without requiring ground-truth labels (source: docs/references/rag-foundations/bibliography.md). Benchmarks such as MTEB and BEIR provide standardized leaderboards for comparing embedding models across retrieval tasks, while the Auepora survey (Yu et al., 2024) proposes a unified evaluation process for end-to-end RAG pipelines.

For detailed metric definitions, the RAGAS framework, benchmark comparisons (MTEB/BEIR), and metric selection guidance, see [[ir-evaluation-benchmarking]].

---

## 10. Token Economy and Efficiency

Accurate token counting is essential for managing context windows and cost optimization. See [[tiktoken]] for tokenizer implementation details.

### Context Window Utilization

**Paper:** "Introducing a New Hyper-parameter for RAG: Context Window Utilization"  
**URL:** <https://arxiv.org/abs/2407.19794>

**Key concept:** Context Window Utilization (CWU) measures the value gained from tokens within the context window (source: docs/references/rag-foundations/bibliography.md). Too few tokens underutilize the model; too many add noise and cost.

### Systems Trade-offs

**Paper:** "Towards Understanding Systems Trade-offs in Retrieval-Augmented Generation Model Inference"  
**URL:** <https://arxiv.org/abs/2412.11854>

**Key findings:**
- RAG increases Time-To-First-Token (TTFT) latency due to retrieval overhead.
- Memory usage can be orders of magnitude higher in large deployments.
- Grid-search optimization for chunk size and model combinations can drastically lower latency.

### Adaptive Context Compression

**Paper:** "Enhancing RAG Efficiency with Adaptive Context Compression"  
**Venue:** Findings of EMNLP 2025  
**URL:** <https://aclanthology.org/2025.findings-emnlp.1307>

**Key innovation:** Hierarchical/dynamic compression reduces inference time by > 4× compared to standard RAG. Provides minimal, sufficient context based on query complexity.

### Cost Optimization Strategies

| Strategy | Impact |
|----------|--------|
| **Query classification** (skip retrieval when unnecessary) | Reduces latency by ~50% for simple queries |
| **Prompt caching** (Anthropic, OpenAI) | Reduces cost by up to 90% for repeated prefixes |
| **Adaptive chunk count** | Retrieve fewer chunks for simple queries, more for complex ones |
| **Context compression** | Summarize retrieved content before generation |
| **Reranking + fewer chunks** | Higher precision with fewer tokens in the prompt |
| **Embedding model selection** | Smaller models (e.g., MiniLM) for lower latency; larger for higher accuracy |

### RAG vs. Long Context Windows

Current research finds that RAG still offers better cost-efficiency and citation quality than naive context stuffing, even with 128K–2M token context windows, especially for tasks requiring citations or deep cross-references.

---

## 11. Local and Offline RAG

A fully local RAG system requires no cloud APIs. All components run on-device.

### Component Stack

| Component | Local Options |
|-----------|--------------|
| **Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2`, `BAAI/bge-small-en`, `nomic-ai/nomic-embed-text-v1.5` (see [[embedding-models-research]]) |
| **Vector Database** | ChromaDB, FAISS, Qdrant (local mode), LanceDB, SQLite-VSS |
| **LLM Inference** | Ollama, llama.cpp, vLLM, transformers (HuggingFace) |
| **Reranker** | `cross-encoder/ms-marco-MiniLM-L-6-v2` (local) |
| **Orchestration** | LangChain, LlamaIndex, Haystack, custom Python |
| **BM25 Search** | rank_bm25 (Python), tantivy (Rust), SQLite FTS5 (see [[sqlite-vec-fts5-hybrid-search]]) |

### Recommended Local Models (2024)

**LLMs (quantized for consumer hardware):**
- Llama 3.1 8B (Q4_K_M) — strong general-purpose
- Mistral 7B (Q4_K_M) — excellent instruction following
- Phi-3 Mini (3.8B) — lightweight, strong reasoning
- Qwen 2.5 7B — multilingual support

**Embedding models:**
- `BAAI/bge-small-en-v1.5` — 33M params, excellent quality/size ratio
- `sentence-transformers/all-MiniLM-L6-v2` — 22M params, very fast
- `nomic-ai/nomic-embed-text-v1.5` — 137M params, high quality, open source

### Local RAG Pipeline Architecture

```
Documents ──► Chunking (recursive/semantic)
                    │
                    ├──► Embedding (sentence-transformers) ──► Vector DB (ChromaDB/FAISS)
                    │
                    └──► BM25 Index (rank_bm25 / SQLite FTS5)
                                    │
Query ──► Embed + BM25 lookup ──► RRF Fusion ──► Reranker (cross-encoder)
                                                        │
                                            Top-K chunks + Query ──► LLM (Ollama/llama.cpp)
                                                                            │
                                                                        Response
```

### Best Practices for Local RAG

1. **Chunking:** Use semantic or recursive chunking with 256–512 token chunks and 50–100 token overlap.
2. **Hybrid search:** Always combine vector search with BM25 — this is the single biggest quality improvement.
3. **Reranking:** Add a local cross-encoder reranker (lightweight, runs on CPU).
4. **Quantization:** Use 4-bit quantized models (GGUF format with llama.cpp) for feasible local inference.
5. **Metadata:** Store source, page number, section title with each chunk for traceability.
6. **Prompt design:** Clearly separate retrieved context from the user query in the prompt.
7. **Security:** Air-gap or firewall the system to ensure no data exfiltration.
8. **Hardware:** Use SSD storage for vector DB; GPU acceleration for LLM inference when available.

### Minimum Hardware Requirements

| Component | CPU-Only | With GPU |
|-----------|----------|----------|
| RAM | 16 GB minimum | 16 GB minimum |
| GPU VRAM | N/A | 6–8 GB (7B model, Q4) |
| Storage | 20 GB | 20 GB |
| Model loading | Slower (seconds) | Fast |
| Inference speed | ~5–15 tokens/sec | ~30–80 tokens/sec |

---

## 12. Quick Reference — Paper Index

| # | Paper | Year | Venue | Topic | URL |
|---|-------|------|-------|-------|-----|
| 1 | Lewis et al. — RAG | 2020 | NeurIPS | Foundational RAG | <https://arxiv.org/abs/2005.11401> |
| 2 | Karpukhin et al. — DPR | 2020 | EMNLP | Dense Retrieval | <https://arxiv.org/abs/2004.04906> |
| 3 | Khattab & Zaharia — ColBERT | 2020 | SIGIR | Late Interaction | <https://arxiv.org/abs/2004.12832> |
| 4 | Cormack et al. — RRF | 2009 | SIGIR | Rank Fusion | SIGIR '09, pp. 758–759 |
| 5 | Gao et al. — RAG Survey | 2024 | arXiv | Comprehensive Survey | <https://arxiv.org/abs/2312.10997> |
| 6 | Wang et al. — RAG Best Practices | 2024 | EMNLP | Pipeline Optimization | <https://arxiv.org/abs/2407.01219> |
| 7 | Sawarkar et al. — Blended RAG | 2024 | IEEE-MIPR | Hybrid Retrieval | <https://arxiv.org/abs/2404.07220> |
| 8 | Es et al. — RAGAS | 2023 | arXiv | Evaluation Framework | <https://arxiv.org/abs/2309.15217> |
| 9 | Yu et al. — RAG Eval Survey | 2024 | arXiv | Evaluation Survey | <https://arxiv.org/abs/2405.07437> |
| 10 | Muennighoff et al. — MTEB | 2023 | EACL | Embedding Benchmark | <https://arxiv.org/abs/2210.07316> |
| 11 | Asai et al. — Self-RAG | 2024 | ICLR | Adaptive Retrieval | <https://arxiv.org/abs/2310.11511> |
| 12 | Yan et al. — CRAG | 2024 | arXiv | Corrective RAG | <https://arxiv.org/abs/2401.15884> |
| 13 | Edge et al. — GraphRAG | 2024 | arXiv | KG-based RAG | <https://arxiv.org/abs/2404.16130> |
| 14 | MultiHop-RAG Benchmark | 2024 | arXiv | Multi-hop Evaluation | <https://arxiv.org/abs/2401.15391> |
| 15 | DMQR-RAG | 2024 | arXiv | Query Rewriting | <https://arxiv.org/abs/2411.13154> |
| 16 | AT-RAG | 2024 | arXiv | Adaptive Topic Retrieval | <https://arxiv.org/abs/2410.12886> |
| 17 | RQ-RAG | 2024 | arXiv | Query Refinement | <https://arxiv.org/abs/2404.00610> |
| 18 | MA-RAG | 2025 | arXiv | Multi-Agent RAG | <https://arxiv.org/abs/2505.20096> |

**Official documentation cited:**
- Anthropic Contextual Retrieval: <https://www.anthropic.com/news/contextual-retrieval>
- LlamaIndex Node Parsers: <https://developers.llamaindex.ai/python/framework/module_guides/loading/node_parsers/modules/>
- RAGAS Docs: <https://docs.ragas.io/>
- MTEB Leaderboard: <https://huggingface.co/spaces/mteb/leaderboard>
- MTEB GitHub: <https://github.com/embeddings-benchmark/mteb>
- ColBERT GitHub: <https://github.com/stanford-futuredata/ColBERT>
- FudanDNN RAG: <https://github.com/FudanDNN-NLP/RAG>

---

## Related pages

- [[sqlite-vec-fts5-hybrid-search]]
- [[embedding-models-research]]
- [[ir-evaluation-benchmarking]]
- [[mcp-protocol]]
- [[pydantic-v2]]
- [[tiktoken]]
- [[python-uv]]

---

*Last compiled: 2025-07. Sources verified against arxiv.org, official documentation, and peer-reviewed venues.*
