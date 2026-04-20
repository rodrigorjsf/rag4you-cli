"""RagTarget — subprocess bridge to the toolkit RAG CLI."""

from __future__ import annotations

import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SearchChunk:
    file_path: str
    content: str
    score: float
    collection: str
    start_line: int | None = None
    end_line: int | None = None
    section_header: str | None = None
    language: str | None = None
    symbol_name: str | None = None
    source: str = "rrf"

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "content": self.content,
            "score": self.score,
            "collection": self.collection,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "section_header": self.section_header,
            "language": self.language,
            "symbol_name": self.symbol_name,
            "source": self.source,
        }


@dataclass
class IndexResult:
    config_id: str
    collection: str | None
    wall_time_s: float
    returncode: int
    stderr: str = ""


_HEADER_RE = re.compile(
    r"^### Result \d+ — `([^`]+)`(?:\s+\(lines (\d+)-(\d+)\))?\s+\[score: ([\d.]+)\]$"
)


def _parse_result_block(block: str, default_collection: str) -> SearchChunk | None:
    """Parse one ``### Result N —`` block into a SearchChunk.

    Uses first and last bare ``` lines as content fence boundaries so that
    embedded code blocks inside the content are preserved correctly.
    """
    lines = block.split("\n")
    if not lines:
        return None

    m = _HEADER_RE.match(lines[0])
    if not m:
        return None

    file_path = m.group(1)
    start_line = int(m.group(2)) if m.group(2) else None
    end_line = int(m.group(3)) if m.group(3) else None
    score = float(m.group(4))

    section_header: str | None = None
    language: str | None = None
    symbol_name: str | None = None
    result_collection = default_collection

    for line in lines[1:]:
        if line == "```":
            break
        if line.startswith("**Section**: "):
            section_header = line[len("**Section**: "):]
        elif line.startswith("**Collection**: "):
            result_collection = line[len("**Collection**: "):]
        elif line.startswith("**") and line.endswith("**") and "**:" not in line:
            inner = line[2:-2]
            for part in inner.split(" | "):
                if part.startswith("Language: "):
                    language = part[len("Language: "):]
                elif part.startswith("Symbol: "):
                    symbol_name = part[len("Symbol: "):]

    # Exactly-three-backtick lines mark fence boundaries.
    fence_indices = [i for i, ln in enumerate(lines) if ln == "```"]
    if len(fence_indices) < 2:
        return None

    open_idx = fence_indices[0]
    close_idx = fence_indices[-1]
    content = "\n".join(lines[open_idx + 1 : close_idx])

    return SearchChunk(
        file_path=file_path,
        content=content,
        score=score,
        collection=result_collection,
        start_line=start_line,
        end_line=end_line,
        section_header=section_header,
        language=language,
        symbol_name=symbol_name,
        source="rrf",
    )


class RagTarget:
    """Subprocess bridge to the toolkit RAG CLI.

    Generates per-sweep ``rag.config.yaml`` files, invokes ``rag index`` and
    ``rag search`` via ``uv run --project``, and parses the markdown search
    output into :class:`SearchChunk` lists.
    """

    def __init__(self, toolkit_path: Path, state_dir: Path) -> None:
        self.toolkit_path = Path(toolkit_path).resolve()
        self.state_dir = Path(state_dir).resolve()
        self._rag_project_dir = self.toolkit_path / "rag"

    # ── Config dir helpers ────────────────────────────────────────────────────

    def config_dir(self, config_id: str) -> Path:
        return self.state_dir / "configs" / config_id

    def config_path(self, config_id: str) -> Path:
        return self.config_dir(config_id) / "rag.config.yaml"

    # ── Config generation ─────────────────────────────────────────────────────

    def generate_config(
        self,
        config_id: str,
        context: dict[str, Any],
        template_path: Path,
    ) -> Path:
        """Render a Jinja2 template into .bench-state/configs/<config_id>/rag.config.yaml.

        *context* is passed verbatim as template variables; callers are
        responsible for supplying absolute source paths so the toolkit resolves
        files correctly regardless of working directory.
        """
        from jinja2 import Environment, FileSystemLoader

        cfg_dir = self.config_dir(config_id)
        cfg_dir.mkdir(parents=True, exist_ok=True)

        env = Environment(
            loader=FileSystemLoader(str(template_path.parent)),
            autoescape=False,
            keep_trailing_newline=True,
        )
        tmpl = env.get_template(template_path.name)
        rendered = tmpl.render(**context)

        out = self.config_path(config_id)
        out.write_text(rendered, encoding="utf-8")
        return out

    # ── Subprocess helpers ────────────────────────────────────────────────────

    def _uv_run(self, *args: str, timeout: int = 600) -> subprocess.CompletedProcess:
        cmd = [
            "uv", "run",
            "--project", str(self._rag_project_dir),
            "python", "-m", "rag",
            *args,
        ]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    # ── Public API ────────────────────────────────────────────────────────────

    def index(
        self,
        config_path: Path,
        collection: str | None = None,
        timeout: int = 600,
    ) -> IndexResult:
        """Run ``rag index`` and return timing + exit status."""
        config_id = config_path.parent.name

        extra: list[str] = []
        if collection:
            extra = ["--collection", collection]

        start = time.monotonic()
        result = self._uv_run("-c", str(config_path), "index", *extra, timeout=timeout)
        elapsed = time.monotonic() - start

        return IndexResult(
            config_id=config_id,
            collection=collection,
            wall_time_s=elapsed,
            returncode=result.returncode,
            stderr=result.stderr,
        )

    def search(
        self,
        config_path: Path,
        query: str,
        collection: str | None = None,
        top_k: int = 5,
        timeout: int = 60,
    ) -> list[SearchChunk]:
        """Run ``rag search`` and return parsed chunks.

        Raises :class:`RuntimeError` if the subprocess exits non-zero.
        """
        extra: list[str] = []
        if collection:
            extra = ["--collection", collection]

        result = self._uv_run(
            "-c", str(config_path),
            "search", query,
            "--top-k", str(top_k),
            *extra,
            timeout=timeout,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"rag search failed (rc={result.returncode}): {result.stderr.strip()}"
            )

        return self.parse_search_output(result.stdout, collection or "all")

    # ── Output parser (static — usable without a RagTarget instance) ──────────

    @staticmethod
    def parse_search_output(output: str, collection: str) -> list[SearchChunk]:
        """Parse ``format_results()`` markdown into :class:`SearchChunk` list.

        Handles nested code blocks inside chunk content by treating the first
        and last bare ``` lines as fence boundaries rather than the first pair.
        """
        stripped = output.strip()
        if not stripped or stripped.startswith("No results found"):
            return []

        blocks = re.split(r"\n(?=### Result \d+ —)", stripped)

        chunks: list[SearchChunk] = []
        for block in blocks:
            if not block.startswith("### Result"):
                continue
            chunk = _parse_result_block(block, collection)
            if chunk is not None:
                chunks.append(chunk)
        return chunks
