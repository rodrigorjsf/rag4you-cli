from __future__ import annotations

import json

from bench.judges.base import Judge, Judgment

DEFAULT_MODEL = "gpt-4o-mini"
_SYSTEM = (
    "You are a relevance judge. Given a query and a retrieved text chunk, "
    "rate how relevant the chunk is to answering the query. "
    'Respond with JSON only: {"score": <float 0.0-1.0>, "reasoning": <string>}'
)


class OpenAIJudge(Judge):
    """Relevance judge backed by OpenAI.

    Requires ``openai`` package (install with ``pip install rag4you-cli[openai]``).
    """

    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None) -> None:
        try:
            import openai
        except ImportError as e:
            raise ImportError("Install rag4you-cli[openai] to use OpenAIJudge") from e
        self._client = openai.OpenAI(api_key=api_key)
        self._model = model

    def score_batch(self, query: str, chunks: list[str]) -> list[Judgment]:
        return [self._score_one(query, chunk) for chunk in chunks]

    def _score_one(self, query: str, chunk: str) -> Judgment:
        prompt = f"Query: {query}\n\nChunk:\n{chunk}"
        resp = self._client.chat.completions.create(
            model=self._model,
            max_tokens=256,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": prompt},
            ],
        )
        return _parse_judgment(resp.choices[0].message.content or "")

    def close(self) -> None:
        self._client.close()


def _parse_judgment(text: str) -> Judgment:
    try:
        data = json.loads(text.strip())
        return Judgment(score=float(data["score"]), reasoning=data.get("reasoning"))
    except Exception:
        return Judgment(score=0.0, reasoning=f"parse_error: {text[:120]}")
