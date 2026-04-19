from __future__ import annotations

import json

from bench.judges.base import Judge, Judgment

DEFAULT_MODEL = "llama3.2"
DEFAULT_BASE_URL = "http://localhost:11434"
_SYSTEM = (
    "You are a relevance judge. Given a query and a retrieved text chunk, "
    "rate how relevant the chunk is to answering the query. "
    'Respond with JSON only: {"score": <float 0.0-1.0>, "reasoning": <string>}'
)


class OllamaJudge(Judge):
    """Relevance judge backed by a local Ollama instance.

    Requires ``httpx`` package (install with ``pip install rag4you-cli[ollama]``).
    Does not require any API key; communicates with a running Ollama server.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        try:
            import httpx
        except ImportError as e:
            raise ImportError("Install rag4you-cli[ollama] to use OllamaJudge") from e
        self._client = httpx.Client(base_url=base_url, timeout=120)
        self._model = model

    def score_batch(self, query: str, chunks: list[str]) -> list[Judgment]:
        return [self._score_one(query, chunk) for chunk in chunks]

    def _score_one(self, query: str, chunk: str) -> Judgment:
        prompt = f"Query: {query}\n\nChunk:\n{chunk}"
        resp = self._client.post(
            "/api/chat",
            json={
                "model": self._model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            },
        )
        resp.raise_for_status()
        content = resp.json()["message"]["content"]
        return _parse_judgment(content)

    def close(self) -> None:
        self._client.close()


def _parse_judgment(text: str) -> Judgment:
    try:
        data = json.loads(text.strip())
        return Judgment(score=float(data["score"]), reasoning=data.get("reasoning"))
    except Exception:
        return Judgment(score=0.0, reasoning=f"parse_error: {text[:120]}")
