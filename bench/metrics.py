from __future__ import annotations

import math

import numpy as np


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Fraction of top-k retrieved documents that are relevant."""
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    return sum(1 for doc in top_k if doc in relevant) / k


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Fraction of all relevant documents found in top-k."""
    if not relevant:
        return 0.0
    top_k = retrieved[:k]
    return sum(1 for doc in top_k if doc in relevant) / len(relevant)


def mrr(queries_results: list[tuple[list[str], set[str]]]) -> float:
    """Mean reciprocal rank of the first relevant result across queries."""
    if not queries_results:
        return 0.0
    rr_sum = 0.0
    for retrieved, relevant in queries_results:
        for rank, doc in enumerate(retrieved, start=1):
            if doc in relevant:
                rr_sum += 1.0 / rank
                break
    return rr_sum / len(queries_results)


def hit_rate_at_k(queries_results: list[tuple[list[str], set[str]]], k: int) -> float:
    """Fraction of queries with at least one relevant document in top-k."""
    if not queries_results:
        return 0.0
    hits = sum(
        1
        for retrieved, relevant in queries_results
        if any(doc in relevant for doc in retrieved[:k])
    )
    return hits / len(queries_results)


def redundancy(embeddings: list[np.ndarray]) -> float:
    """Mean pairwise cosine similarity among retrieved chunk embeddings.

    Higher redundancy means overlapping chunks wasting context-window tokens.
    """
    if len(embeddings) < 2:
        return 0.0
    matrix = np.stack(embeddings)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    normalized = matrix / norms
    sim_matrix = normalized @ normalized.T
    n = len(embeddings)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    if not pairs:
        return 0.0
    return float(sum(sim_matrix[i, j] for i, j in pairs) / len(pairs))


def token_to_coverage_ratio(coverage: float, tokens: int) -> float:
    """Coverage per log-token unit. Higher is better.

    Log denominator avoids over-penalising configs that retrieve more tokens.
    """
    if coverage <= 0.0 or tokens <= 0:
        return 0.0
    return coverage / math.log1p(tokens)


def self_sufficiency_rate(coverages: list[float], threshold: float = 0.8) -> float:
    """Fraction of queries where coverage meets or exceeds threshold."""
    if not coverages:
        return 0.0
    return sum(1 for c in coverages if c >= threshold) / len(coverages)
