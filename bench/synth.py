"""Synthetic query generator — chunk → LLM → query, with self-validation."""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

import yaml

from bench.corpus import CorpusLoader
from bench.i18n import t


@dataclass
class SynthQuery:
    id: str
    collection: str
    query: str
    source_file: str
    query_kind: str = "synthetic"
    difficulty: str = "medium"
    length: str = "short"
    expected_files: list = None  # type: ignore[assignment]
    expected_answer: str = ""
    must_contain: list = None  # type: ignore[assignment]
    tags: list = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.expected_files is None:
            self.expected_files = [self.source_file]
        if self.must_contain is None:
            self.must_contain = []
        if self.tags is None:
            self.tags = ["synthetic"]


def _is_ollama_reachable(base_url: str) -> bool:
    try:
        import httpx

        resp = httpx.get(f"{base_url}/api/tags", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


def _generate_query_with_ollama(
    chunk_text: str, model: str, base_url: str
) -> str | None:
    try:
        import httpx

        prompt = (
            "Given the following text chunk, write ONE short search query "
            "that a user would type to find this information. "
            "Return only the query string, nothing else.\n\n"
            f"Chunk:\n{chunk_text[:800]}"
        )
        client = httpx.Client(base_url=base_url, timeout=60)
        resp = client.post(
            "/api/chat",
            json={
                "model": model,
                "stream": False,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()
    except Exception:
        return None


def _generate_query_with_judge(
    chunk_text: str, judge: object
) -> str | None:
    """Use a ClaudeJudge or OpenAIJudge as a generator (same SDK, different prompt)."""
    prompt = (
        "Write ONE short search query that a user would type to find this information. "
        "Return only the query string.\n\n"
        f"Text:\n{chunk_text[:800]}"
    )
    try:
        if hasattr(judge, "_client") and hasattr(judge._client, "messages"):
            # Anthropic
            msg = judge._client.messages.create(
                model=judge._model,
                max_tokens=80,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text.strip()
        if hasattr(judge, "_client") and hasattr(judge._client, "chat"):
            # OpenAI
            resp = judge._client.chat.completions.create(
                model=judge._model,
                max_tokens=80,
                messages=[{"role": "user", "content": prompt}],
            )
            return (resp.choices[0].message.content or "").strip()
    except Exception:
        return None
    return None


class SynthGenerator:
    """Generate synthetic queries from corpus chunks using an available LLM."""

    def __init__(
        self,
        target_path: Path,
        toolkit_config: Path,
        judge: object,
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "qwen2.5:7b-instruct",
    ) -> None:
        self._target_path = Path(target_path)
        self._toolkit_config = Path(toolkit_config)
        self._judge = judge
        self._ollama_base_url = ollama_base_url
        self._ollama_model = ollama_model

    def _can_generate(self) -> bool:
        judge_class = type(self._judge).__name__
        if judge_class in ("ClaudeJudge", "OpenAIJudge"):
            return True
        return _is_ollama_reachable(self._ollama_base_url)

    def _generate_one(self, chunk_text: str) -> str | None:
        judge_class = type(self._judge).__name__
        if judge_class in ("ClaudeJudge", "OpenAIJudge"):
            return _generate_query_with_judge(chunk_text, self._judge)
        if _is_ollama_reachable(self._ollama_base_url):
            return _generate_query_with_ollama(chunk_text, self._ollama_model, self._ollama_base_url)
        return None

    def generate(
        self,
        target: object,
        config_path: Path,
        collection: str,
        n: int = 50,
        seed: int = 42,
        print_fn=print,
    ) -> list[SynthQuery]:
        """Generate up to *n* validated synthetic queries. Returns [] when no LLM available."""
        if not self._can_generate():
            print_fn(t("cli.synth.skipped", model=self._ollama_model, n=n))
            return []

        loader = CorpusLoader(self._target_path)
        if not self._toolkit_config.exists():
            return []

        corpus_files = loader.enumerate_from_config(self._toolkit_config)
        if not corpus_files:
            return []

        rng = random.Random(seed)
        # Sample files proportional to n (skip every n-th)
        step = max(1, len(corpus_files) // n)
        sampled = corpus_files[::step][:n]
        rng.shuffle(sampled)

        print_fn(t("cli.synth.generating", n=len(sampled)))

        results: list[SynthQuery] = []
        dropped = 0

        for i, cf in enumerate(sampled):
            file_path = self._target_path / cf.path
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore").strip()
            except OSError:
                continue
            if len(text) < 80:
                continue

            query_text = self._generate_one(text)
            if not query_text:
                continue

            # Self-validate: source file must appear in top-10
            try:
                from bench.target import RagTarget

                chunks = target.search(config_path, query_text, collection=collection, top_k=10)  # type: ignore[attr-defined]
                found = any(cf.path in (c.file_path or "") for c in chunks)
            except Exception:
                found = False

            if not found:
                dropped += 1
                continue

            results.append(
                SynthQuery(
                    id=f"synth-{i:03d}",
                    collection=collection,
                    query=query_text,
                    source_file=cf.path,
                )
            )

        if dropped:
            print_fn(t("cli.synth.dropped", n=dropped))

        return results
