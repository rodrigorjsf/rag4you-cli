from __future__ import annotations

import pytest

from bench.judges.base import Judge, Judgment
from bench.judges.cross_encoder import CrossEncoderJudge


def test_judgment_dataclass():
    j = Judgment(score=0.9)
    assert j.score == 0.9
    assert j.reasoning is None


def test_judgment_with_reasoning():
    j = Judgment(score=0.5, reasoning="partial match")
    assert j.reasoning == "partial match"


def test_judge_is_abstract():
    with pytest.raises(TypeError):
        Judge()  # type: ignore[abstract]


def test_cross_encoder_is_judge():
    judge = CrossEncoderJudge()
    assert isinstance(judge, Judge)


def test_score_returns_judgment():
    judge = CrossEncoderJudge()
    result = judge.score("What is RAG?", "RAG stands for Retrieval-Augmented Generation.")
    assert isinstance(result, Judgment)
    assert isinstance(result.score, float)
    assert result.reasoning is None


def test_score_batch_returns_list():
    judge = CrossEncoderJudge()
    chunks = [
        "RAG stands for Retrieval-Augmented Generation.",
        "The capital of France is Paris.",
    ]
    results = judge.score_batch("What is RAG?", chunks)
    assert len(results) == 2
    assert all(isinstance(r, Judgment) for r in results)


def test_score_batch_empty():
    judge = CrossEncoderJudge()
    assert judge.score_batch("query", []) == []


def test_literal_match_scores_higher_than_random():
    """Cross-encoder gate: literal query/chunk match > random chunk."""
    judge = CrossEncoderJudge()
    query = "What is Retrieval-Augmented Generation?"
    literal_chunk = (
        "Retrieval-Augmented Generation (RAG) combines a retrieval step with "
        "a language model to ground answers in retrieved documents."
    )
    random_chunk = (
        "The Eiffel Tower was built between 1887 and 1889 as the entrance arch "
        "for the 1889 World's Fair in Paris."
    )
    results = judge.score_batch(query, [literal_chunk, random_chunk])
    assert results[0].score > results[1].score, (
        f"Literal match ({results[0].score:.4f}) should score higher than "
        f"random chunk ({results[1].score:.4f})"
    )


def test_score_single_delegates_to_batch():
    judge = CrossEncoderJudge()
    chunk = "RAG stands for Retrieval-Augmented Generation."
    single = judge.score("What is RAG?", chunk)
    batch = judge.score_batch("What is RAG?", [chunk])
    assert single.score == pytest.approx(batch[0].score)


def test_close_does_not_raise():
    judge = CrossEncoderJudge()
    judge.close()
