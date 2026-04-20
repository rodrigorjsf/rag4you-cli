"""BenchConfig — pydantic model for bench run configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

# ── Model registry ────────────────────────────────────────────────────────────

_DOCS_MODELS: dict[str, tuple[str, int]] = {
    "small":  ("BAAI/bge-small-en-v1.5", 384),
    "medium": ("BAAI/bge-base-en-v1.5", 768),
    "large":  ("BAAI/bge-large-en-v1.5", 1024),
}
_CODE_MODELS: dict[str, tuple[str, int]] = {
    "small":  ("nomic-ai/nomic-embed-code", 256),
    "medium": ("jinaai/jina-embeddings-v2-base-code", 768),
    "large":  ("Alibaba-NLP/gte-Qwen2-1.5B-instruct", 1536),
}
_MODEL_SLUG: dict[str, str] = {
    "BAAI/bge-small-en-v1.5":               "bge-small",
    "BAAI/bge-base-en-v1.5":                "bge-base",
    "BAAI/bge-large-en-v1.5":               "bge-large",
    "nomic-ai/nomic-embed-code":             "nomic-code",
    "jinaai/jina-embeddings-v2-base-code":   "jina-base",
    "Alibaba-NLP/gte-Qwen2-1.5B-instruct":   "gte-qwen2",
}

COLLECTION_MODELS: dict[str, dict[str, tuple[str, int]]] = {
    "docs": _DOCS_MODELS,
    "code": _CODE_MODELS,
}


@dataclass
class SweepEntry:
    config_id: str
    collection: str
    chunk_size: int
    model_tier: str
    model_name: str
    dimensions: int


# ── Pydantic settings ─────────────────────────────────────────────────────────

class CrossEncoderSettings(BaseModel):
    model: str = "BAAI/bge-reranker-base"
    device: str = "cpu"


class ClaudeSettings(BaseModel):
    model: str = "claude-haiku-4-5-20251001"
    api_key_env: str = "ANTHROPIC_API_KEY"
    max_concurrent: int = 5


class OpenAISettings(BaseModel):
    model: str = "gpt-4o-mini"
    api_key_env: str = "OPENAI_API_KEY"
    max_concurrent: int = 5


class OllamaSettings(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5:7b-instruct"
    max_concurrent: int = 2


class JudgeSettings(BaseModel):
    type: str = "cross-encoder"
    cross_encoder: CrossEncoderSettings = Field(
        default_factory=CrossEncoderSettings, alias="cross-encoder"
    )
    claude: ClaudeSettings = Field(default_factory=ClaudeSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)

    model_config = {"populate_by_name": True}


class TargetSettings(BaseModel):
    path: Path
    rag_config_template: Path = Field(
        default_factory=lambda: Path("bench/templates/toolkit-rag.config.yaml.j2")
    )
    toolkit_rag_config: Path | None = None

    @field_validator("path", mode="before")
    @classmethod
    def _expand_path(cls, v: Any) -> Path:
        return Path(str(v)).expanduser()

    def resolved_toolkit_config(self) -> Path:
        if self.toolkit_rag_config is not None:
            return Path(self.toolkit_rag_config).expanduser().resolve()
        return (Path(self.path) / "rag" / "rag.config.yaml").resolve()


class SweepSettings(BaseModel):
    collections: list[str] = Field(default_factory=lambda: ["docs", "code"])
    chunk_sizes: dict[str, list[int]] = Field(
        default_factory=lambda: {"docs": [256, 512, 1024], "code": [1000, 1500, 2500]}
    )
    models: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "docs": ["small", "medium", "large"],
            "code": ["small", "medium", "large"],
        }
    )
    top_k: list[int] = Field(default_factory=lambda: [3, 5, 10])


class ScoringWeights(BaseModel):
    coverage: float = 0.5
    token_to_coverage_ratio: float = 0.3
    precision_at_5: float = 0.2


class ScoringSettings(BaseModel):
    composite_weights: ScoringWeights = Field(default_factory=ScoringWeights)
    self_sufficiency_threshold: float = 0.8


class BenchConfig(BaseModel):
    lang: str = "en"
    judge: JudgeSettings = Field(default_factory=JudgeSettings)
    target: TargetSettings
    sweep: SweepSettings = Field(default_factory=SweepSettings)
    scoring: ScoringSettings = Field(default_factory=ScoringSettings)
    state_dir: Path = Field(default_factory=lambda: Path(".bench-state"))
    reports_dir: Path = Field(default_factory=lambda: Path("reports"))

    @classmethod
    def from_yaml(cls, path: Path) -> "BenchConfig":
        with Path(path).open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return cls.model_validate(data)

    @classmethod
    def from_target(cls, target_path: Path | str, **overrides: Any) -> "BenchConfig":
        """Create a minimal BenchConfig from a target path (CLI --target shortcut)."""
        resolved = Path(target_path).expanduser().resolve()
        return cls(target=TargetSettings(path=resolved), **overrides)

    def expand_sweep(self) -> list[SweepEntry]:
        """Expand the sweep matrix into individual ordered SweepEntry items."""
        entries: list[SweepEntry] = []
        for collection in self.sweep.collections:
            chunk_sizes = self.sweep.chunk_sizes.get(collection, [512])
            tiers = self.sweep.models.get(collection, ["small"])
            model_map = COLLECTION_MODELS.get(collection, _DOCS_MODELS)
            for chunk_size in chunk_sizes:
                for tier in tiers:
                    if tier not in model_map:
                        continue
                    model_name, dims = model_map[tier]
                    slug = _MODEL_SLUG.get(model_name, tier)
                    config_id = f"{collection}-c{chunk_size}-{slug}"
                    entries.append(
                        SweepEntry(
                            config_id=config_id,
                            collection=collection,
                            chunk_size=chunk_size,
                            model_tier=tier,
                            model_name=model_name,
                            dimensions=dims,
                        )
                    )
        return entries
