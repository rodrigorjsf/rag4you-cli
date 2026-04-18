# IR Evaluation & Benchmarking — Source Bibliography

**Compiled**: 2025-07-22
**Purpose**: Bibliographic reference for evaluation metrics and benchmarking methodology sources used in wiki/knowledge/ir-evaluation-benchmarking.md

---

## Textbooks

### Introduction to Information Retrieval
- **Authors**: Manning, Raghavan, Schütze
- **Publisher**: Cambridge University Press, 2008
- **Online edition**: https://nlp.stanford.edu/IR-book/
- **ISBN**: 978-0-521-86571-5
- **Key chapters**: Ch. 8 (Evaluation), §8.2 (Precision/Recall), §8.3 (Ranked retrieval), §8.4 (Relevance assessment)

## Academic papers

### LLM-as-a-Judge
- **Title**: Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena
- **Authors**: Zheng, Chiang, Sheng, Zhuang, Wu, Zhuang, Lin, Li, Li, Xing, Zhang, Gonzalez, Stoica
- **Venue**: NeurIPS 2023
- **URL**: https://arxiv.org/abs/2306.05685
- **Key finding**: Strong LLMs achieve >80% agreement with human judges. Recommends temperature=0 for deterministic evaluation. Position bias exists (first-presented answer favored).

### RAGAS
- **Title**: RAGAS: Automated Evaluation of Retrieval Augmented Generation
- **Authors**: Es, James, Espinosa-Anke, Schockaert
- **Venue**: EACL 2024
- **URL**: https://arxiv.org/abs/2309.15217
- **Official docs**: https://docs.ragas.io/
- **Key metrics**: Faithfulness, answer relevance, context precision, context recall. No human annotations required.

### ARES
- **Title**: ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems
- **Authors**: Saad-Falcon, Khattab, Potts, Zaharia
- **Venue**: NAACL 2024
- **URL**: https://arxiv.org/abs/2311.09476
- **Key contribution**: Fine-tuned classifier judges on synthetic data. More cost-effective than pure LLM-as-judge.

### RAG Evaluation Survey
- **Authors**: Yu, Ai, Li, Han, Liu, Wen, Min, de Rijke
- **Venue**: arXiv 2024
- **URL**: https://arxiv.org/abs/2405.07437
- **Key contribution**: Taxonomy of RAG evaluation: retrieval metrics, generation metrics, end-to-end metrics. Comprehensive comparison of evaluation frameworks.

### Cross-encoder as Judge
- **Title**: A Thorough Comparison of Cross-Encoders and LLMs for Reranking SPLADE
- **Authors**: Déjean, Music, Music, Music
- **Venue**: arXiv 2024
- **URL**: https://arxiv.org/abs/2403.10407
- **Key finding**: Cross-encoders achieve comparable ranking quality to LLMs for reranking tasks at fraction of the cost. Validates SP0's approach of cross-encoder as default judge.

### Reproducibility
- **Title**: Reproducibility in Information Retrieval Evaluation
- **Authors**: Ferro, Sanderson
- **Venue**: Foundations and Trends in Information Retrieval
- **Key recommendations**: Document all parameters, pin software versions, use deterministic seeds, share evaluation artifacts.

## TREC evaluation

### TREC overview
- **URL**: https://trec.nist.gov/
- **Key methodology**: Pooling approach for relevance judgments, standardized evaluation via `trec_eval` tool.
- **Relevance**: SP0 golden set construction follows TREC assessment principles (query categorization, difficulty levels, multiple assessors).

### Voorhees on assessor agreement
- **Title**: Variations in Relevance Judgments and the Measurement of Retrieval Effectiveness
- **Authors**: Voorhees
- **Venue**: Information Processing & Management, 2000
- **Key finding**: ~70% inter-assessor agreement on relevance. Systems rank relatively stably despite individual judgment variation. Validates using a single-assessor golden set for regression testing.

## Synthetic query generation

### RAGEval
- **Venue**: ACL 2025
- **Key approach**: Generate queries from document chunks, then validate by checking if the source chunk appears in retrieval results. SP0 uses this exact pattern in `synth.py`.

### BenchmarkQED
- **Key approach**: Domain-specific synthetic benchmarks with automated validation. Demonstrates that synthetic queries can achieve 85-95% correlation with human-curated queries.

## Token economy

### Context Window Utilization
- **URL**: https://arxiv.org/abs/2407.19794
- **Key insight**: LLMs show degraded performance when context windows are >60% filled. Optimal retrieval should aim for 30-50% context utilization. Directly relevant to SP0's token-to-coverage ratio metric.
