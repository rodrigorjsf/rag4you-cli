from __future__ import annotations

import numpy as np
import pytest

from bench.metrics import (
    hit_rate_at_k,
    mrr,
    precision_at_k,
    recall_at_k,
    redundancy,
    self_sufficiency_rate,
    token_to_coverage_ratio,
)

# --- precision_at_k ---


def test_precision_at_k_all_relevant():
    retrieved = ["a.md", "b.md", "c.md"]
    relevant = {"a.md", "b.md", "c.md"}
    assert precision_at_k(retrieved, relevant, k=3) == pytest.approx(1.0)


def test_precision_at_k_first_relevant():
    retrieved = ["a.md", "x.md", "y.md"]
    relevant = {"a.md"}
    assert precision_at_k(retrieved, relevant, k=1) == pytest.approx(1.0)
    assert precision_at_k(retrieved, relevant, k=3) == pytest.approx(1 / 3)


def test_precision_at_k_none_relevant():
    retrieved = ["x.md", "y.md"]
    relevant = {"a.md"}
    assert precision_at_k(retrieved, relevant, k=2) == pytest.approx(0.0)


def test_precision_at_k_empty_retrieved():
    assert precision_at_k([], {"a.md"}, k=3) == pytest.approx(0.0)


def test_precision_at_k_k_larger_than_retrieved():
    retrieved = ["a.md"]
    relevant = {"a.md"}
    assert precision_at_k(retrieved, relevant, k=5) == pytest.approx(1 / 5)


# --- recall_at_k ---


def test_recall_at_k_all_found():
    retrieved = ["a.md", "b.md"]
    relevant = {"a.md", "b.md"}
    assert recall_at_k(retrieved, relevant, k=2) == pytest.approx(1.0)


def test_recall_at_k_partial():
    retrieved = ["a.md", "x.md", "y.md"]
    relevant = {"a.md", "b.md"}
    assert recall_at_k(retrieved, relevant, k=3) == pytest.approx(0.5)


def test_recall_at_k_empty_relevant():
    assert recall_at_k(["a.md"], set(), k=3) == pytest.approx(0.0)


def test_recall_at_k_none_found():
    retrieved = ["x.md", "y.md"]
    relevant = {"a.md", "b.md"}
    assert recall_at_k(retrieved, relevant, k=2) == pytest.approx(0.0)


# --- mrr ---


def test_mrr_first_position():
    results = [(["a.md", "b.md"], {"a.md"})]
    assert mrr(results) == pytest.approx(1.0)


def test_mrr_second_position():
    results = [(["x.md", "a.md"], {"a.md"})]
    assert mrr(results) == pytest.approx(0.5)


def test_mrr_no_relevant():
    results = [(["x.md", "y.md"], {"a.md"})]
    assert mrr(results) == pytest.approx(0.0)


def test_mrr_multiple_queries():
    results = [
        (["a.md", "b.md"], {"a.md"}),  # rr = 1.0
        (["x.md", "a.md"], {"a.md"}),  # rr = 0.5
    ]
    assert mrr(results) == pytest.approx(0.75)


def test_mrr_empty():
    assert mrr([]) == pytest.approx(0.0)


# --- hit_rate_at_k ---


def test_hit_rate_all_hit():
    results = [(["a.md"], {"a.md"}), (["b.md"], {"b.md"})]
    assert hit_rate_at_k(results, k=1) == pytest.approx(1.0)


def test_hit_rate_none_hit():
    results = [(["x.md"], {"a.md"}), (["y.md"], {"b.md"})]
    assert hit_rate_at_k(results, k=1) == pytest.approx(0.0)


def test_hit_rate_partial():
    results = [(["a.md"], {"a.md"}), (["y.md"], {"b.md"})]
    assert hit_rate_at_k(results, k=1) == pytest.approx(0.5)


def test_hit_rate_empty():
    assert hit_rate_at_k([], k=3) == pytest.approx(0.0)


# --- redundancy ---


def test_redundancy_identical_vectors():
    v = np.array([1.0, 0.0, 0.0])
    assert redundancy([v, v, v]) == pytest.approx(1.0)


def test_redundancy_orthogonal():
    v1 = np.array([1.0, 0.0])
    v2 = np.array([0.0, 1.0])
    assert redundancy([v1, v2]) == pytest.approx(0.0)


def test_redundancy_single_embedding():
    assert redundancy([np.array([1.0, 0.0])]) == pytest.approx(0.0)


def test_redundancy_empty():
    assert redundancy([]) == pytest.approx(0.0)


def test_redundancy_range():
    v1 = np.array([1.0, 0.0])
    v2 = np.array([0.0, 1.0])
    v3 = np.array([1.0, 0.0])
    r = redundancy([v1, v2, v3])
    assert 0.0 <= r <= 1.0


# --- token_to_coverage_ratio ---


def test_token_to_coverage_positive():
    r = token_to_coverage_ratio(coverage=1.0, tokens=100)
    assert r > 0.0


def test_token_to_coverage_zero_coverage():
    assert token_to_coverage_ratio(0.0, 100) == pytest.approx(0.0)


def test_token_to_coverage_zero_tokens():
    assert token_to_coverage_ratio(0.8, 0) == pytest.approx(0.0)


def test_token_to_coverage_monotone():
    r_low = token_to_coverage_ratio(coverage=0.8, tokens=100)
    r_high = token_to_coverage_ratio(coverage=0.8, tokens=10000)
    assert r_low > r_high


# --- self_sufficiency_rate ---


def test_self_sufficiency_all_pass():
    assert self_sufficiency_rate([0.9, 0.85, 0.95]) == pytest.approx(1.0)


def test_self_sufficiency_none_pass():
    assert self_sufficiency_rate([0.1, 0.2, 0.3]) == pytest.approx(0.0)


def test_self_sufficiency_partial():
    assert self_sufficiency_rate([0.9, 0.5, 0.8]) == pytest.approx(2 / 3)


def test_self_sufficiency_empty():
    assert self_sufficiency_rate([]) == pytest.approx(0.0)


def test_self_sufficiency_custom_threshold():
    assert self_sufficiency_rate([0.6, 0.7, 0.8], threshold=0.65) == pytest.approx(2 / 3)
