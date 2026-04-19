from __future__ import annotations

from bench.judges.base import Judge, Judgment

DEFAULT_MODEL = "BAAI/bge-reranker-base"


class CrossEncoderJudge(Judge):
    """Relevance judge backed by a fastembed cross-encoder reranker.

    bge-reranker-v2-m3 is not in the fastembed ONNX registry; bge-reranker-base
    is the available alternative and is used by default.
    """

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        self._model = TextCrossEncoder(model_name=model)

    def score_batch(self, query: str, chunks: list[str]) -> list[Judgment]:
        if not chunks:
            return []
        scores = list(self._model.rerank(query, chunks))
        return [Judgment(score=float(s)) for s in scores]
