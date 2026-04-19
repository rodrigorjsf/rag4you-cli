# IR Evaluation Metrics & RAG Benchmarking — Research Reference

**Summary**: Authoritative academic and official sources for building the SP0 benchmark harness. Covers classical IR evaluation metrics, RAG-specific evaluation frameworks, benchmarking best practices, checkpoint/resume patterns, and token economy analysis.
**Sources**: `docs/references/evaluation/bibliography.md`
**Last updated**: 2026-04-19

---

## Table of Contents

- [IR Evaluation Metrics \& RAG Benchmarking — Research Reference](#ir-evaluation-metrics--rag-benchmarking--research-reference)
  - [Table of Contents](#table-of-contents)
  - [1. Classical IR Evaluation Metrics](#1-classical-ir-evaluation-metrics)
    - [1.1 Textbook Foundation — Manning, Raghavan, Schütze](#11-textbook-foundation--manning-raghavan-schütze)
      - [Key Formulas (from §8.3)](#key-formulas-from-83)
    - [1.2 TREC Evaluation Methodology](#12-trec-evaluation-methodology)
      - [Core Methodology](#core-methodology)
      - [Key Reference Papers](#key-reference-papers)
      - [trec\_eval Metrics Supported](#trec_eval-metrics-supported)
    - [1.3 Metric Definitions and Formulas](#13-metric-definitions-and-formulas)
      - [Precision@k](#precisionk)
      - [Recall@k](#recallk)
      - [F1@k](#f1k)
      - [Mean Reciprocal Rank (MRR)](#mean-reciprocal-rank-mrr)
      - [Hit Rate@k](#hit-ratek)
      - [Coverage Score](#coverage-score)
      - [Redundancy](#redundancy)
      - [Token-to-Coverage Ratio](#token-to-coverage-ratio)
      - [Self-Sufficiency Rate](#self-sufficiency-rate)
      - [System Metrics](#system-metrics)
  - [2. RAG-Specific Evaluation](#2-rag-specific-evaluation)
    - [2.1 RAGAS Framework](#21-ragas-framework)
      - [Core Metrics](#core-metrics)
      - [Faithfulness Calculation (from official docs)](#faithfulness-calculation-from-official-docs)
      - [Context Precision (from official docs)](#context-precision-from-official-docs)
      - [RAGAS Collections API (v0.3+, 2025)](#ragas-collections-api-v03-2025)
    - [2.2 ARES — Automated RAG Evaluation](#22-ares--automated-rag-evaluation)
      - [Key Innovation](#key-innovation)
      - [Three Evaluation Axes](#three-evaluation-axes)
    - [2.3 RAG Evaluation Survey — Yu et al](#23-rag-evaluation-survey--yu-et-al)
      - [Unified Evaluation Process (Auepora)](#unified-evaluation-process-auepora)
      - [Recent Benchmarks Catalogued](#recent-benchmarks-catalogued)
  - [3. Benchmarking Best Practices](#3-benchmarking-best-practices)
    - [3.1 Golden Set Construction](#31-golden-set-construction)
      - [TREC Pooling Methodology](#trec-pooling-methodology)
      - [SP0 Golden Set Design (20 queries)](#sp0-golden-set-design-20-queries)
    - [3.2 Synthetic Query Generation](#32-synthetic-query-generation)
      - [RAGEval — ACL 2025](#rageval--acl-2025)
      - [BenchmarkQED — Microsoft Research 2025](#benchmarkqed--microsoft-research-2025)
      - [SP0 Synthetic Query Design (`synth.py` — planned, not yet implemented)](#sp0-synthetic-query-design-synthpy--planned-not-yet-implemented)
    - [3.3 Cross-Encoder vs LLM-as-Judge](#33-cross-encoder-vs-llm-as-judge)
      - [Academic Comparison](#academic-comparison)
    - [3.4 The LLM-as-a-Judge Paper](#34-the-llm-as-a-judge-paper)
      - [Core Findings](#core-findings)
      - [MT-Bench Design](#mt-bench-design)
    - [3.5 Reproducibility in IR Experiments](#35-reproducibility-in-ir-experiments)
      - [SIGIR Guidelines](#sigir-guidelines)
      - [Definitions (ACM standard)](#definitions-acm-standard)
      - [Best Practices for SP0](#best-practices-for-sp0)
      - [ACM Artifact Badging](#acm-artifact-badging)
  - [4. Checkpoint and Resume Patterns](#4-checkpoint-and-resume-patterns)
    - [4.1 POSIX Atomic Write Guarantees](#41-posix-atomic-write-guarantees)
      - [The Atomic Rename Pattern](#the-atomic-rename-pattern)
      - [POSIX Guarantees](#posix-guarantees)
      - [Caveats](#caveats)
    - [4.2 JSONL Append Pattern](#42-jsonl-append-pattern)
      - [Why JSONL for Progress Tracking](#why-jsonl-for-progress-tracking)
      - [Recovery After Crash](#recovery-after-crash)
    - [4.3 State Machine for Evaluation Pipelines](#43-state-machine-for-evaluation-pipelines)
      - [State Diagram](#state-diagram)
      - [State Persistence](#state-persistence)
      - [Design Principles](#design-principles)
  - [5. Token Economy in RAG](#5-token-economy-in-rag)
    - [5.1 Context Window Utilization](#51-context-window-utilization)
      - [Key Concept](#key-concept)
      - [SP0 Metrics That Capture CWU](#sp0-metrics-that-capture-cwu)
    - [5.2 Token Counting Methodologies](#52-token-counting-methodologies)
      - [Academic Context](#academic-context)
      - [SP0 Token Metrics (from spec)](#sp0-token-metrics-from-spec)
      - [Encoding Selection for SP0](#encoding-selection-for-sp0)
    - [5.3 Cost-Performance Tradeoffs](#53-cost-performance-tradeoffs)
      - [Academic References](#academic-references)
      - [Cost Optimization Strategies (from literature)](#cost-optimization-strategies-from-literature)
      - [SP0's Token Economy Analysis](#sp0s-token-economy-analysis)
  - [6. Quick Reference — Source Index](#6-quick-reference--source-index)
  - [Related pages](#related-pages)

---

## 1. Classical IR Evaluation Metrics

### 1.1 Textbook Foundation — Manning, Raghavan, Schütze

**Title:** Introduction to Information Retrieval
**Authors:** Christopher D. Manning, Prabhakar Raghavan, Hinrich Schütze
**Publisher:** Cambridge University Press, 2008
**Online edition:** <https://nlp.stanford.edu/IR-book/>
**ISBN:** 978-0-521-86571-5

This is the standard textbook for IR evaluation. The relevant chapters for SP0 are:

| Chapter                                           | Topic                                                                   | SP0 Relevance                       |
| ------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------- |
| **Ch. 8** — Evaluation in Information Retrieval   | Precision, recall, F-measure, ranked evaluation                         | Core metric definitions             |
| **§8.2** — Precision and recall                   | Set-based measures, contingency table                                   | `precision_at_k()`, `recall_at_k()` |
| **§8.3** — Evaluation of ranked retrieval results | Precision-recall curves, interpolated precision, MAP, R-precision, NDCG | `mrr()`, `ndcg_at_k()`              |
| **§8.4** — Assessing relevance                    | Relevance judgments, assessor agreement, pooling                        | Golden set construction methodology |
| **§8.5** — A broader perspective                  | Kappa statistic, assessor variation                                     | Judge calibration                   |

#### Key Formulas (from §8.3)

**Mean Average Precision (MAP):**

```
MAP(Q) = (1/|Q|) × Σⱼ (1/mⱼ) × Σₖ Precision(Rⱼₖ)
```

Where `mⱼ` = number of relevant docs for query `qⱼ`, and `Rⱼₖ` = result set at the rank of the k-th relevant doc.

**NDCG@k** (§8.3, Eq. 44):

```
NDCG(Q, k) = (1/|Q|) × Σⱼ Zₖⱼ × Σₘ₌₁ᵏ (2^R(j,m) - 1) / log₂(1 + m)
```

Where `Zₖⱼ` normalizes so perfect ranking scores 1.

**Practical insight for SP0:** MAP has the best discrimination and stability among common IR metrics (§8.3) (source: docs/references/evaluation/bibliography.md). NDCG is preferred when relevance is graded (not binary). For SP0's binary relevance model (chunk is relevant or not), Precision@k, Recall@k, MRR, and Hit@k are the right choices. NDCG would become relevant if SP1 introduces graded relevance.

---

### 1.2 TREC Evaluation Methodology

**Organization:** NIST (National Institute of Standards and Technology)
**Website:** <https://trec.nist.gov/>
**trec_eval tool:** <https://github.com/usnistgov/trec_eval>

TREC (Text REtrieval Conference) established the de facto standard for IR evaluation since 1992.

#### Core Methodology

1. **Topics (queries):** Standardized information needs with title, description, and narrative fields.
2. **Pooling:** Merge top-K results from multiple systems to create a pool of candidate documents for judging. Unjudged documents are assumed non-relevant.
3. **Relevance judgments (qrels):** Human assessors judge each document in the pool as relevant or non-relevant (sometimes graded: highly relevant, relevant, marginally relevant, non-relevant).
4. **trec_eval:** Computes MAP, NDCG, P@k, Recall, bpref, and dozens of other metrics from system output and qrels files.

#### Key Reference Papers

- **Voorhees, E.M. (1998).** "Variations in Relevance Judgments and the Measurement of Retrieval Effectiveness." SIGIR '98, pp. 315–323. <https://dl.acm.org/doi/10.1145/290941.291022>
  - Finding: While assessors disagree on individual judgments, the relative ranking of systems is stable across different sets of judgments.
  - **SP0 implication:** A 20-query golden set with consistent single-assessor judgments is sufficient for system-level comparison (the SP0 use case).

- **Voorhees, E.M. (2000).** "The TREC-8 Question Answering Track Report." TREC-8 Proceedings. <https://trec.nist.gov/pubs/trec8/papers/qa_report.pdf>
  - Established evaluation standards for QA (the closest TREC task to RAG evaluation).

#### trec_eval Metrics Supported

| Metric       | Description                           | SP0 Equivalent                          |
| ------------ | ------------------------------------- | --------------------------------------- |
| `map`        | Mean Average Precision                | Not in SP0 (binary relevance + small k) |
| `ndcg_cut.K` | NDCG at rank K                        | Future consideration                    |
| `P.K`        | Precision at rank K                   | `precision_at_k()`                      |
| `recall.K`   | Recall at rank K                      | `recall_at_k()`                         |
| `recip_rank` | Reciprocal rank of first relevant doc | `mrr()`                                 |
| `bpref`      | Binary preference metric              | Not in SP0                              |

**Practical insight for SP0:** The trec_eval input format (qrels + run files) is a well-established standard. Even though SP0 computes metrics in Python, adopting the qrels format for golden set storage enables future compatibility with trec_eval and community benchmarks.

---

### 1.3 Metric Definitions and Formulas

These are the exact metrics specified in the SP0 spec and implemented in `bench/metrics.py` (source: docs/references/evaluation/bibliography.md):

#### Precision@k

```
Precision@k = |{relevant} ∩ {retrieved_top_k}| / k
```

- Range: [0, 1]
- Measures: How many of the top-k results are relevant.
- Use: False positives are costly — user sees irrelevant content in RAG context.

#### Recall@k

```
Recall@k = |{relevant} ∩ {retrieved_top_k}| / |{relevant}|
```

- Range: [0, 1]
- Measures: How many of all relevant documents appear in top-k.
- Use: Completeness matters — missing relevant content degrades RAG answer quality.

#### F1@k

```
F1@k = 2 × (Precision@k × Recall@k) / (Precision@k + Recall@k)
```

- Harmonic mean balancing precision and recall.

#### Mean Reciprocal Rank (MRR)

```
MRR = (1/|Q|) × Σᵢ 1/rankᵢ
```

- Range: (0, 1]
- Measures: How high the first relevant result ranks, averaged over queries.
- Use: Critical for RAG where the first relevant chunk often dominates answer quality.

#### Hit Rate@k

```
Hit@k = |{queries with at least 1 relevant doc in top-k}| / |Q|
```

- Range: [0, 1]
- Measures: Fraction of queries where retrieval found at least something useful.
- Use: Binary success metric — "did the retriever help at all?"

#### Coverage Score

```
Coverage = fraction of expected_answer key facts present in retrieved chunks
```

- SP0-specific metric not from classical IR.
- Implemented via judge (cross-encoder or LLM): the judge scores how well the concatenated top-k chunks cover the ground-truth expected answer.
- Range: [0, 1]

#### Redundancy

```
Redundancy = mean pairwise cosine similarity among retrieved chunks
```

- SP0-specific metric.
- High redundancy means the retriever returns overlapping content, wasting context window tokens.
- Computed from chunk embeddings (see [[embedding-models-research]]), not from the judge.

#### Token-to-Coverage Ratio

```
Token-to-Coverage = total_context_tokens / coverage_score
```

- SP0-specific metric for token economy.
- Lower is better: achieving the same coverage with fewer tokens is more efficient.

#### Self-Sufficiency Rate

```
Self-Sufficiency = fraction of queries where coverage ≥ threshold (e.g., 0.8)
```

- SP0-specific metric.
- Answers: "For what fraction of queries does retrieval provide enough context to answer the question?"

#### System Metrics

| Metric        | Unit               | Measures                                            |
| ------------- | ------------------ | --------------------------------------------------- |
| Indexing time | seconds            | Time to index the full corpus for one configuration |
| Query latency | ms (p50, p95, p99) | End-to-end retrieval time per query                 |
| Peak RSS      | MB                 | Maximum resident memory during indexing/querying    |
| DB size       | MB                 | On-disk size of the vector + FTS database           |

---

## 2. RAG-Specific Evaluation

For broader RAG research context including retrieval techniques and chunking strategies, see [[rag-research-compendium]].

### 2.1 RAGAS Framework

**Title:** RAGAS: Automated Evaluation of Retrieval Augmented Generation
**Authors:** Shahul Es, Jithin James, Luis Espinosa-Anke, Steven Schockaert
**Venue:** arXiv preprint (2023), updated 2025
**URL:** <https://arxiv.org/abs/2309.15217>
**Official docs:** <https://docs.ragas.io/>
**GitHub:** <https://github.com/explodinggradients/ragas>
**PyPI:** <https://pypi.org/project/ragas/>

#### Core Metrics

| Metric                  | What It Measures                          | Formula                                                          | Requires              |
| ----------------------- | ----------------------------------------- | ---------------------------------------------------------------- | --------------------- |
| **Faithfulness**        | Are response claims supported by context? | Supported claims / Total claims                                  | LLM judge             |
| **Context Precision**   | Are relevant chunks ranked higher?        | Mean(Precision@k × vₖ) / Relevant items in top-K                 | LLM judge + reference |
| **Context Recall**      | Did retrieval find all needed info?       | Attributable reference claims / Total reference claims           | LLM judge + reference |
| **Answer Relevancy**    | Does the answer address the query?        | cos(question, answer) in embedding space                         | Embedding model       |
| **Context Utilization** | Is retrieved context actually used?       | Same as Context Precision but uses response instead of reference | LLM judge             |
| **Noise Sensitivity**   | Does irrelevant context hurt the answer?  | Empirical degradation measurement                                | LLM judge             |

#### Faithfulness Calculation (from official docs)

1. Extract all atomic claims from the generated response.
2. For each claim, use an LLM judge to classify as: entailed / neutral / unsupported by the retrieved context.
3. `Faithfulness = entailed_claims / total_claims`

**SP0 relationship:** SP0's `coverage_score` is conceptually similar to RAGAS Context Recall — both measure how well retrieved chunks cover the expected answer. SP0 uses a simpler binary-judge approach (cross-encoder as default) rather than RAGAS's claim decomposition, but the SP0 judge interface supports LLM backends (Claude, OpenAI, Ollama) that could implement RAGAS-style evaluation.

#### Context Precision (from official docs)

```
Context Precision@K = Σₖ₌₁ᴷ (Precision@k × vₖ) / (Total relevant in top K)
```

Where `vₖ ∈ {0, 1}` is the relevance indicator at rank k. This is a weighted precision that rewards placing relevant chunks earlier in the ranking.

**Key insight:** RAGAS offers both LLM-based and non-LLM-based variants:

- `LLMContextPrecisionWithReference` — uses an LLM to compare chunks against reference answer.
- `LLMContextPrecisionWithoutReference` — uses an LLM to compare chunks against generated response.
- `NonLLMContextPrecisionWithReference` — uses Levenshtein distance, no LLM needed.
- `IDBasedContextPrecision` — compares document IDs directly.

**SP0 relationship:** SP0's `precision_at_k()` is the classical IR variant (binary relevant/not-relevant from golden set), not RAGAS's weighted version. The SP0 judge interface could be extended to support RAGAS-style weighted precision in future SPs.

#### RAGAS Collections API (v0.3+, 2025)

RAGAS recently introduced a collections-based API:

```python
from ragas.metrics.collections import Faithfulness, ContextPrecision
scorer = Faithfulness(llm=llm)
result = await scorer.ascore(
    user_input="...",
    response="...",
    retrieved_contexts=["..."]
)
```

The legacy `SingleTurnSample` API is deprecated (removed in v1.0).

---

### 2.2 ARES — Automated RAG Evaluation

**Title:** ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems
**Authors:** Jon Saad-Falcon, Omar Khattab, Christopher Potts, Matei Zaharia (Stanford)
**Venue:** NAACL 2024, pp. 338–354
**URL:** <https://arxiv.org/abs/2311.09476>
**Code:** <https://github.com/stanford-futuredata/ARES>

#### Key Innovation

ARES reduces human annotation requirements by:

1. **Synthetic data generation:** Generates synthetic QA pairs to train lightweight LLM judges.
2. **Fine-tuned judges:** Trains small models to evaluate context relevance, faithfulness, and answer relevance.
3. **Prediction-Powered Inference (PPI):** Uses a small human-annotated calibration set (≈150 samples) to statistically correct model predictions with confidence intervals.

#### Three Evaluation Axes

| Axis                | Description                                   | SP0 Equivalent                   |
| ------------------- | --------------------------------------------- | -------------------------------- |
| Context relevance   | Are retrieved passages relevant to the query? | `precision_at_k()`               |
| Answer faithfulness | Is the answer grounded in retrieved context?  | `coverage_score` (partial)       |
| Answer relevance    | Does the answer address the question?         | Not in SP0 scope (no generation) |

**SP0 relationship:** ARES's PPI approach is relevant for future work when SP0 needs to calibrate LLM judge scores against human judgments. The synthetic data generation methodology aligns with SP0's `synth.py` component.

---

### 2.3 RAG Evaluation Survey — Yu et al

**Title:** Evaluation of Retrieval-Augmented Generation: A Survey (Auepora)
**Authors:** Hao Yu et al.
**URL:** <https://arxiv.org/abs/2405.07437>
**DOI:** `10.1007/978-981-96-1024-2_8`

#### Unified Evaluation Process (Auepora)

The survey proposes a three-dimensional evaluation framework:

1. **Retrieval evaluation:** Relevance, diversity, coverage of retrieved documents.
2. **Generation evaluation:** Accuracy, faithfulness, fluency, relevance of generated answers.
3. **End-to-end evaluation:** Overall system quality measured by downstream task performance.

**Key recommendation:** Evaluate retrieval and generation independently — the retrieval component is foundational for trustworthy output (source: docs/references/evaluation/bibliography.md). This aligns with SP0's design choice to evaluate retrieval metrics independently from generation (SP0 does not evaluate generation quality, only retrieval).

#### Recent Benchmarks Catalogued

| Benchmark        | Year | Venue   | Description                                                         |
| ---------------- | ---- | ------- | ------------------------------------------------------------------- |
| **CRAG**         | 2024 | NeurIPS | 4,409 QA pairs across 5 domains, entity popularity stratification   |
| **RAGEval**      | 2025 | ACL     | Schema-based synthetic dataset generation for diverse RAG scenarios |
| **MEMERAG**      | 2025 | ACL     | Multilingual end-to-end meta-evaluation benchmark                   |
| **BenchmarkQED** | 2025 | MSR     | Automated benchmarking toolkit with AutoQ query synthesis           |
| **Cit-eRAG**     | 2026 | WWW     | Academic citation prediction RAG benchmark                          |

---

## 3. Benchmarking Best Practices

### 3.1 Golden Set Construction

#### TREC Pooling Methodology

The standard approach for building IR test collections (Voorhees, 1998; Sparck Jones, 1975):

1. **Topic selection:** Choose 50+ representative information needs covering diverse query types, difficulty levels, and domains.
2. **Document pooling:** Run multiple retrieval systems and pool their top-K results (typically K=100–1000) per query.
3. **Human annotation:** Expert assessors judge each pooled document for relevance (binary or graded).
4. **Completeness check:** Compute inter-annotator agreement (Cohen's κ or Fleiss' κ). Accept if κ ≥ 0.6.
5. **Unjudged documents:** Assumed non-relevant (TREC convention) or handled via bpref metric.

**Reference:** Sanderson, M. & Zobel, J. (2005). "Information Retrieval System Evaluation: Effort, Sensitivity, and Reliability." SIGIR '05, pp. 162–169. <https://dl.acm.org/doi/10.1145/1076034.1076064>

#### SP0 Golden Set Design (20 queries)

SP0 adapts TREC methodology for a small, focused benchmark:

- **Coverage:** 5 query categories (conceptual, navigational, factual, procedural, failure) across 2 collections (docs, code) plus cross-collection queries.
- **Ground truth:** Each query has `expected_files` (known-relevant documents), `expected_answer` (canonical answer), and `must_contain` (required tokens in retrieved chunks).
- **Validation:** Self-consistency check — run the golden set against the current system and verify that at least one configuration achieves reasonable scores.

**Key principle from Voorhees (1998):** For system-level comparison, 20–50 queries with consistent single-assessor judgments provide stable system rankings, even if individual relevance judgments vary between assessors.

---

### 3.2 Synthetic Query Generation

#### RAGEval — ACL 2025

**Title:** RAGEval: Scenario Specific RAG Evaluation Dataset Generation Framework
**Authors:** Zhu et al.
**Venue:** ACL 2025
**URL:** <https://aclanthology.org/2025.acl-long.418/>
**Code:** <https://github.com/OpenBMB/RAGEval>

**Methodology:**

1. Schema-based generation: Define document schemas specifying entity types, relationships, and facts.
2. LLM-guided synthesis: An LLM generates synthetic documents following the schema.
3. Question generation: Generate questions from the synthetic documents with known ground-truth answers.
4. Novel metrics: Completeness, Hallucination, and Irrelevance scores.

#### BenchmarkQED — Microsoft Research 2025

**Title:** BenchmarkQED: Automated Benchmarking of RAG Systems
**URL:** <https://www.microsoft.com/en-us/research/project/benchmarkqed/>

**AutoQ methodology:**

1. Automated query synthesis spanning local-to-global information needs.
2. Queries are generated to cover different retrieval difficulty levels.
3. The toolkit enables reproducible, automated benchmarking across RAG configurations.

#### SP0 Synthetic Query Design (`synth.py` — planned, not yet implemented)

SP0's approach aligns with academic best practices:

1. **Chunk-to-query generation:** Walk corpus chunks; for every Nth chunk, ask an LLM to generate a natural query that the chunk would answer.
2. **Self-validation filter:** Retrieve top-10 for each generated query; drop the query if the source chunk does not appear (noise filter).
3. **Fallback graceful degradation:** If no LLM is available, skip synthetic queries and run only the 20 golden queries.

**Key principle from RAGEval:** Self-validation (ensuring the source chunk appears in retrieval results) is critical for synthetic query quality. SP0's approach of dropping queries that fail self-validation is consistent with this principle.

---

### 3.3 Cross-Encoder vs LLM-as-Judge

#### Academic Comparison

**Key paper:** Déjean, H., Clinchant, S., & Formal, T. (2024). "A Thorough Comparison of Cross-Encoders and LLMs for Reranking SPLADE." arXiv:2403.10407. <https://arxiv.org/abs/2403.10407>

**Findings:**

- On in-domain data (MS MARCO): Cross-encoders and LLM rerankers perform comparably.
- On out-of-domain data (BEIR, LoTTE): Performance diverges significantly depending on task.
- **Cross-encoders:** 5–10× faster, lower cost, strong default choice for production.
- **LLM rerankers:** Better reasoning on complex queries, but higher latency and cost.

**Distillation:** Schlatt, F. et al. (2025). "Rank-DistiLLM: Closing the Effectiveness Gap Between Cross-Encoders and LLMs for Passage Re-ranking." ECIR 2025. <https://link.springer.com/chapter/10.1007/978-3-031-88714-7_31>

- Cross-encoders distilled from LLMs achieve the same effectiveness as their teacher LLMs while being 173× faster and 24× more memory efficient.

**SP0 design rationale:** SP0 defaults to cross-encoder (fastembed reranker, retrieval via [[sqlite-vec-fts5-hybrid-search]]) for:

- Zero-cost evaluation (no API keys needed).
- Fast execution (critical for sweeping 18 configs × 70 queries).
- Sufficient quality for system-level comparison.
- LLM judges (Claude, OpenAI, Ollama) are available as optional upgrades for higher-fidelity evaluation.

---

### 3.4 The LLM-as-a-Judge Paper

**Title:** Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena
**Authors:** Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Siyuan Zhuang, Zhanghao Wu, Yonghao Zhuang, Zi Lin, Zhuohan Li, Dacheng Li, Eric P. Xing, Hao Zhang, Joseph E. Gonzalez, Ion Stoica
**Venue:** NeurIPS 2023 (Datasets and Benchmarks Track)
**URL:** <https://arxiv.org/abs/2306.05685>
**DOI:** `10.48550/arXiv.2306.05685`
**Code:** <https://github.com/lm-sys/FastChat/tree/main/fastchat/llm_judge>

#### Core Findings

1. **Agreement rate:** Strong LLM judges (GPT-4) achieve >80% agreement with human preferences — the same level as human-human agreement (source: docs/references/evaluation/bibliography.md).
2. **Identified biases:**
   - **Position bias:** LLMs prefer the first option in pairwise comparisons.
   - **Verbosity bias:** LLMs prefer longer, more detailed responses.
   - **Self-enhancement bias:** LLMs rate their own outputs higher.
   - **Limited reasoning:** LLMs struggle with math and logic-heavy evaluations.
3. **Mitigation strategies:**
   - Swap position and average scores.
   - Use reference answers to ground evaluations.
   - Use chain-of-thought prompting for complex evaluations.

#### MT-Bench Design

- 80 multi-turn questions across 8 categories (writing, roleplay, extraction, reasoning, math, coding, knowledge, stem).
- Each question has a follow-up turn to test conversation coherence.
- Scores on a 1–10 scale with reference answers.

**SP0 relevance:** When using LLM judges for coverage scoring, SP0 should:

- **Mitigate position bias:** Present chunks in random order (not retrieval rank order) to the judge.
- **Use reference answers:** Ground coverage judgment against the golden set's `expected_answer`.
- **Cache judge responses:** Store judge verdicts in `judge-cache.jsonl` to avoid re-evaluation after resume.

---

### 3.5 Reproducibility in IR Experiments

#### SIGIR Guidelines

**Key reference:** Ferro, N. & Sanderson, M. (2018). "Reproducibility, Replicability, and Reliability in Information Retrieval: A Shared Path toward Trustworthy IR." SIGIR Forum, vol. 52, no. 2.

#### Definitions (ACM standard)

| Term                | Definition                                           |
| ------------------- | ---------------------------------------------------- |
| **Repeatability**   | Same team, same setup → same results                 |
| **Reproducibility** | Different team, same artifacts → same results        |
| **Replicability**   | Different team, different setup → consistent results |

#### Best Practices for SP0

1. **Deterministic runs:** Fix random seeds; document RNG usage.
2. **Environment pinning:** Record Python version, package versions (via `uv.lock`), OS, hardware.
3. **Manifest:** SP0's `manifest.json` records all configuration parameters, software versions, and system specifications for each run.
4. **Raw data preservation:** SP0 stores `raw.jsonl` with every retrieval result, judge score, and timing measurement.
5. **Corpus fingerprinting:** SP0's `corpus.py` (planned — not yet implemented) computes SHA-256 hashes of all indexed files, enabling detection of corpus changes between runs.

#### ACM Artifact Badging

ACM uses artifact badges to signal reproducibility:

- **Artifacts Available:** Code and data are publicly accessible.
- **Artifacts Evaluated — Functional:** Code runs and produces claimed results.
- **Results Reproduced:** An independent team reproduced the results.

**SP0 implication:** The benchmark harness itself is testable (`bench/tests/` — 48 tests, all green as of Phase 1) and its metrics computations are verifiable against known inputs.

---

## 4. Checkpoint and Resume Patterns

### 4.1 POSIX Atomic Write Guarantees

**References:**

- POSIX rename(2): <https://man7.org/linux/man-pages/man2/rename.2.html>
- POSIX fsync(2): <https://man7.org/linux/man-pages/man2/fsync.2.html>
- Dan Luu, "Files are hard": <https://danluu.com/file-consistency/>

#### The Atomic Rename Pattern

The standard crash-safe file update pattern for `bench/persistence.py` (planned — not yet implemented):

```python
import os
import json

def atomic_json_write(path: str, data: dict) -> None:
    """Write JSON atomically via tmp + fsync + rename."""
    tmp_path = path + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.rename(tmp_path, path)
    # Optional: fsync directory for full durability
    dir_fd = os.open(os.path.dirname(path) or ".", os.O_DIRECTORY)
    os.fsync(dir_fd)
    os.close(dir_fd)
```

#### POSIX Guarantees

| Operation                    | Guarantee                                                                                                                                      |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `rename()`                   | Atomic on POSIX-compliant filesystems (ext4, XFS, APFS). The destination is either the old file or the new file, never a partial file.         |
| `fsync(fd)`                  | All data and metadata for the file are flushed to stable storage. After `fsync` + crash, the synced content is guaranteed on disk.             |
| `rename()` without `fsync()` | The rename is atomic in terms of file content, but the directory entry may not be durable. After a crash, the old file might still be present. |
| Cross-directory `rename()`   | NOT guaranteed atomic on all filesystems. SP0 must keep `.tmp` and final file in the same directory.                                           |

#### Caveats

- **NFS, SMB, network filesystems:** May not honor POSIX atomicity guarantees. SP0's `.bench-state/` directory should be on a local filesystem.
- **ext4 with `data=writeback`:** `fsync` might not flush data if the file was recently created. The `tmp + rename` pattern avoids this because `rename` forces a metadata update.
- **Python's `os.rename()`:** On Linux, this is the `rename(2)` syscall. On Windows, it is NOT atomic if the target exists (use `os.replace()` instead, which is atomic on all platforms).

---

### 4.2 JSONL Append Pattern

For `bench/persistence.py`'s (planned — not yet implemented) progress and judge-cache files:

```python
import os
import json

def append_jsonl(path: str, record: dict) -> None:
    """Append a single JSON line with fsync for crash safety."""
    line = json.dumps(record, separators=(",", ":")) + "\n"
    with open(path, "a") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())
```

#### Why JSONL for Progress Tracking

| Property        | Benefit for SP0                                                                                 |
| --------------- | ----------------------------------------------------------------------------------------------- |
| Append-only     | Never modifies existing data — crash during write loses at most the last line                   |
| Line-per-record | Each line is a complete JSON object — partial writes produce invalid JSON only on the last line |
| Easy resume     | On resume, read all valid lines and skip the incomplete last line (if any)                      |
| Streamable      | Can tail the file during a long run to monitor progress                                         |
| grep-friendly   | Can search/filter records with standard tools                                                   |

#### Recovery After Crash

```python
def read_jsonl_safe(path: str) -> list[dict]:
    """Read JSONL file, skipping the last line if it's invalid (crash recovery)."""
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                # Last line may be truncated — skip it
                break
    return records
```

---

### 4.3 State Machine for Evaluation Pipelines

SP0's `bench/checkpoint.py` (planned — not yet implemented) implements a state machine for the sweep lifecycle:

#### State Diagram

```
INIT ──► INDEXING ──► QUERYING ──► JUDGING ──► REPORTING ──► COMPLETE
  │          │            │           │
  └──────────┴────────────┴───────────┴──► ERROR
```

#### State Persistence

Each state transition is recorded in the manifest:

```json
{
  "run_id": "2026-04-XX-toolkit-baseline-abc123",
  "state": "QUERYING",
  "started_at": "2026-04-20T10:00:00Z",
  "config_progress": {
    "small-bge-small-256": "complete",
    "small-bge-small-512": "in_progress",
    "small-bge-small-1024": "pending"
  },
  "query_progress": 42,
  "total_queries": 70
}
```

#### Design Principles

1. **Externalized state:** The state machine itself is stateless; all state lives in checkpoint files.
2. **Idempotent transitions:** Re-running a completed step is a no-op (skip if already done).
3. **Granular progress:** Track progress at the (config × query) level, not just the phase level.
4. **Advisory locking:** Use `fcntl.flock()` to prevent concurrent runs on the same state directory.
5. **Manifest as truth:** The manifest (modeled with [[pydantic-v2]]) is the single source of truth. Progress files (JSONL) are append-only audit logs.

**Reference pattern:** This follows the "Memento + State Machine" design pattern combination. The Memento pattern (serialized state snapshots) enables checkpoint/resume. The State Machine pattern ensures valid transitions and prevents re-execution of completed work.

---

## 5. Token Economy in RAG

### 5.1 Context Window Utilization

**Title:** Introducing a New Hyper-parameter for RAG: Context Window Utilization
**Authors:** Juvekar, A. & Purwar, A.
**URL:** <https://arxiv.org/abs/2407.19794>

#### Key Concept

Context Window Utilization (CWU) measures the effective value gained from tokens in the context window:

- **Too few tokens:** Underutilizes the model; retrieval might miss relevant information.
- **Too many tokens:** Adds noise, increases cost, and can degrade output quality ("lost in the middle" effect).
- **Optimal:** CWU is maximized when the context contains only relevant, non-redundant information.

#### SP0 Metrics That Capture CWU

| SP0 Metric                | CWU Dimension                                                      |
| ------------------------- | ------------------------------------------------------------------ |
| `token_to_coverage_ratio` | Tokens spent per unit of answer coverage (lower is better)         |
| `redundancy`              | Wasted tokens from overlapping chunks (lower is better)            |
| `self_sufficiency_rate`   | Fraction of queries where context is sufficient (higher is better) |
| `coverage_score`          | How well context covers the expected answer (higher is better)     |

**Practical insight:** SP0's sweep across `top_k ∈ {3, 5, 10}` directly measures the CWU tradeoff — increasing top_k adds more context tokens but may not improve coverage proportionally.

---

### 5.2 Token Counting Methodologies

See also: [[tiktoken]] wiki page for API details and [[rag-research-compendium]] for chunking context.

#### Academic Context

Token counting for RAG evaluation requires:

1. **Consistent encoding:** Use the same tokenizer (encoding) across all measurements.
2. **Model-specific counting:** Different models use different tokenizers (cl100k_base for GPT-4, o200k_base for GPT-4o).
3. **Chunk budget awareness:** Count tokens per chunk, not just per query, to measure context window efficiency.

#### SP0 Token Metrics (from spec)

```python
# Computed for each (config, query, top_k) triple:
{
    "query_tokens": int,        # Tokens in the query
    "context_tokens": int,      # Total tokens in retrieved chunks
    "per_chunk_tokens": [int],  # Token count per chunk
    "coverage": float,          # From judge
    "token_to_coverage": float, # context_tokens / coverage
}
```

#### Encoding Selection for SP0

SP0 uses `cl100k_base` as the default encoding because:

- It covers GPT-4, GPT-3.5-turbo, and `text-embedding-ada-002`/`text-embedding-3-*`.
- It provides a reasonable proxy for token counting even when the exact model is not known.
- The encoding is configurable (not hardcoded) per repo conventions.

---

### 5.3 Cost-Performance Tradeoffs

#### Academic References

**Title:** Towards Understanding Systems Trade-offs in Retrieval-Augmented Generation Model Inference
**URL:** <https://arxiv.org/abs/2412.11854>

**Key findings:**

- RAG increases Time-To-First-Token (TTFT) latency due to retrieval overhead.
- Memory usage can be orders of magnitude higher in large deployments.
- Grid-search optimization for chunk size and model combinations drastically lowers latency.

**Title:** Enhancing RAG Efficiency with Adaptive Context Compression
**Venue:** Findings of EMNLP 2025
**URL:** <https://aclanthology.org/2025.findings-emnlp.1307>

**Key finding:** Hierarchical/dynamic compression reduces inference time by >4× compared to standard RAG while maintaining answer quality.

#### Cost Optimization Strategies (from literature)

| Strategy                                  | Token Savings                   | SP0 Relevance                     |
| ----------------------------------------- | ------------------------------- | --------------------------------- |
| **Reranking + fewer chunks**              | 50–80%                          | SP0 measures this via top_k sweep |
| **Query classification** (skip retrieval) | ~50% for simple queries         | Out of SP0 scope                  |
| **Context compression**                   | 30–50%                          | Future SP1 consideration          |
| **Prompt caching**                        | Up to 90% for repeated prefixes | Not applicable to SP0             |
| **Smaller embedding models**              | Lower latency, same recall      | SP0 measures via model sweep      |

#### SP0's Token Economy Analysis

SP0's sweep matrix naturally produces the data needed for cost-performance analysis:

- **chunk_size × top_k** determines `context_tokens`.
- **coverage_score** determines retrieval quality.
- **token_to_coverage_ratio** is the primary cost-performance metric.
- **Pareto frontier:** SP0's report identifies configurations on the Pareto frontier of coverage vs. token cost.

---

## 6. Quick Reference — Source Index

| #   | Source                                  | Type                | Year  | Topic                                 | URL                                                              |
| --- | --------------------------------------- | ------------------- | ----- | ------------------------------------- | ---------------------------------------------------------------- |
| 1   | Manning, Raghavan, Schütze — IIR        | Textbook            | 2008  | IR evaluation metrics                 | <https://nlp.stanford.edu/IR-book/>                              |
| 2   | TREC / trec_eval                        | Tool + Methodology  | 1992– | Standard IR evaluation                | <https://trec.nist.gov/>                                         |
| 3   | Voorhees — Relevance Variations         | Paper (SIGIR)       | 1998  | Assessor agreement, pooling           | <https://dl.acm.org/doi/10.1145/290941.291022>                   |
| 4   | Es et al. — RAGAS                       | Paper + Framework   | 2023  | RAG evaluation metrics                | <https://arxiv.org/abs/2309.15217>                               |
| 5   | RAGAS Official Docs                     | Documentation       | 2025  | Faithfulness, Context Precision, etc. | <https://docs.ragas.io/>                                         |
| 6   | Saad-Falcon et al. — ARES               | Paper (NAACL)       | 2024  | Automated RAG evaluation              | <https://arxiv.org/abs/2311.09476>                               |
| 7   | Yu et al. — RAG Eval Survey             | Paper               | 2024  | Evaluation survey (Auepora)           | <https://arxiv.org/abs/2405.07437>                               |
| 8   | Zheng et al. — LLM-as-a-Judge           | Paper (NeurIPS)     | 2023  | LLM judging methodology               | <https://arxiv.org/abs/2306.05685>                               |
| 9   | Déjean et al. — Cross-Encoder vs LLM    | Paper               | 2024  | Reranking comparison                  | <https://arxiv.org/abs/2403.10407>                               |
| 10  | Schlatt et al. — Rank-DistiLLM          | Paper (ECIR)        | 2025  | Distilled cross-encoders              | <https://link.springer.com/chapter/10.1007/978-3-031-88714-7_31> |
| 11  | Zhu et al. — RAGEval                    | Paper (ACL)         | 2025  | Synthetic dataset generation          | <https://aclanthology.org/2025.acl-long.418/>                    |
| 12  | BenchmarkQED                            | Toolkit (MSR)       | 2025  | Automated RAG benchmarking            | <https://www.microsoft.com/en-us/research/project/benchmarkqed/> |
| 13  | Juvekar & Purwar — CWU                  | Paper               | 2024  | Context window utilization            | <https://arxiv.org/abs/2407.19794>                               |
| 14  | Systems Trade-offs in RAG               | Paper               | 2024  | Latency/memory tradeoffs              | <https://arxiv.org/abs/2412.11854>                               |
| 15  | Adaptive Context Compression            | Paper (EMNLP)       | 2025  | Context compression                   | <https://aclanthology.org/2025.findings-emnlp.1307>              |
| 16  | Ferro & Sanderson — Reproducibility     | Paper (SIGIR Forum) | 2018  | IR experiment reproducibility         | SIGIR Forum vol. 52 no. 2                                        |
| 17  | Sanderson & Zobel — Effort, Sensitivity | Paper (SIGIR)       | 2005  | Test collection design                | <https://dl.acm.org/doi/10.1145/1076034.1076064>                 |
| 18  | POSIX rename(2)                         | Man page            | —     | Atomic file rename                    | <https://man7.org/linux/man-pages/man2/rename.2.html>            |
| 19  | POSIX fsync(2)                          | Man page            | —     | File sync guarantees                  | <https://man7.org/linux/man-pages/man2/fsync.2.html>             |
| 20  | Dan Luu — Files are hard                | Blog                | 2017  | Crash consistency patterns            | <https://danluu.com/file-consistency/>                           |

---

## Related pages

- [[rag-research-compendium]] — Broader RAG research (retrieval techniques, chunking, advanced paradigms)
- [[tiktoken]] — Token counting library API reference
- [[sqlite-vec-fts5-hybrid-search]] — Hybrid search implementation details
- [[embedding-models-research]] — Embedding model selection
- [[pydantic-v2]] — Data validation models for config and metrics

---

*Compiled for rag4you-cli SP0 benchmark harness. Sources verified against arxiv.org, official docs, NIST, and peer-reviewed proceedings.*
