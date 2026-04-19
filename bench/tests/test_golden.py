from __future__ import annotations

import pytest

from bench.golden import load_golden_queries
from bench.golden.schema import Collection, Difficulty, GoldenQuery, QueryKind, QueryLength


def test_load_golden_queries_returns_list():
    queries = load_golden_queries()
    assert isinstance(queries, list)
    assert len(queries) == 20


def test_load_golden_queries_all_valid():
    queries = load_golden_queries()
    for q in queries:
        assert isinstance(q, GoldenQuery)


def test_golden_query_ids_unique():
    queries = load_golden_queries()
    ids = [q.id for q in queries]
    assert len(ids) == len(set(ids))


def test_golden_query_fields():
    queries = load_golden_queries()
    q = queries[0]
    assert q.id
    assert isinstance(q.collection, Collection)
    assert isinstance(q.query_kind, QueryKind)
    assert isinstance(q.difficulty, Difficulty)
    assert isinstance(q.length, QueryLength)
    assert isinstance(q.expected_files, list)
    assert isinstance(q.must_contain, list)
    assert isinstance(q.tags, list)


def test_golden_query_model_validate():
    data = {
        "id": "test-001",
        "collection": "docs",
        "query": "What is RAG?",
        "query_kind": "conceptual",
        "difficulty": "easy",
        "length": "short",
        "expected_files": ["README.md"],
        "expected_answer": "Retrieval-Augmented Generation.",
        "must_contain": ["retrieval"],
        "tags": ["overview"],
    }
    q = GoldenQuery.model_validate(data)
    assert q.id == "test-001"
    assert q.collection == Collection.docs
    assert q.query_kind == QueryKind.conceptual


def test_collection_enum_values():
    assert Collection.docs == "docs"
    assert Collection.code == "code"
    assert Collection.all == "all"


def test_query_kind_enum_values():
    assert QueryKind.conceptual == "conceptual"
    assert QueryKind.failure == "failure"


def test_golden_query_invalid_collection():
    with pytest.raises(Exception):
        GoldenQuery.model_validate(
            {
                "id": "bad-001",
                "collection": "invalid",
                "query": "x",
                "query_kind": "conceptual",
                "difficulty": "easy",
                "length": "short",
                "expected_answer": "x",
            }
        )
