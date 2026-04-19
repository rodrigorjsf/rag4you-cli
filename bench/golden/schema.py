from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Collection(StrEnum):
    docs = "docs"
    code = "code"
    all = "all"


class QueryKind(StrEnum):
    conceptual = "conceptual"
    navigational = "navigational"
    factual = "factual"
    procedural = "procedural"
    failure = "failure"


class Difficulty(StrEnum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class QueryLength(StrEnum):
    short = "short"
    long = "long"


class GoldenQuery(BaseModel):
    id: str = Field(..., description="Unique query identifier, e.g. docs-001")
    collection: Collection
    query: str
    query_kind: QueryKind
    difficulty: Difficulty
    length: QueryLength
    expected_files: list[str] = Field(
        default_factory=list,
        description="Files that MUST appear in top-K for this query to be considered a hit",
    )
    expected_answer: str = Field(..., description="Canonical ground-truth answer")
    must_contain: list[str] = Field(
        default_factory=list,
        description="Tokens/phrases that should appear in retrieved chunks",
    )
    tags: list[str] = Field(default_factory=list)
