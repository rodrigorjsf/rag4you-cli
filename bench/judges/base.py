from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Judgment:
    score: float
    reasoning: str | None = field(default=None)


class Judge(ABC):
    """Score retrieval relevance between a query and retrieved text chunks.

    Implementations must override ``score_batch``. The single-item helper
    ``score`` delegates to it so backends only need one entry point.
    """

    @abstractmethod
    def score_batch(self, query: str, chunks: list[str]) -> list[Judgment]:
        """Return one Judgment per chunk, in the same order as *chunks*."""

    def score(self, query: str, chunk: str) -> Judgment:
        return self.score_batch(query, [chunk])[0]

    def close(self) -> None:
        """Release any held resources (model handles, HTTP sessions, etc.)."""
