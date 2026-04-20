"""CorpusLoader — enumerate and hash files that the toolkit RAG would index."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class CorpusFile:
    path: str
    sha256: str
    size_bytes: int


class CorpusLoader:
    """Enumerate source files from a ``rag.config.yaml`` and compute SHA-256 hashes.

    Used during bench run init to snapshot the corpus for drift detection.
    """

    def __init__(self, target_path: Path) -> None:
        self.target_path = Path(target_path).resolve()

    # ── File enumeration ──────────────────────────────────────────────────────

    def _glob_source(
        self, source_path: Path, patterns: list[str], recursive: bool
    ) -> list[Path]:
        files: list[Path] = []
        for pattern in patterns:
            if recursive:
                files.extend(source_path.rglob(pattern))
            else:
                files.extend(source_path.glob(pattern))
        return files

    def enumerate_from_config(self, config_yaml_path: Path) -> list[CorpusFile]:
        """Return all files that would be indexed given *config_yaml_path*.

        Paths in the config are resolved relative to the config file's
        directory (matching RagConfig.resolve_path behaviour in the toolkit).
        """
        config_yaml_path = Path(config_yaml_path).resolve()
        with config_yaml_path.open(encoding="utf-8") as fh:
            config = yaml.safe_load(fh)

        config_dir = config_yaml_path.parent
        seen: set[Path] = set()
        files: list[Path] = []

        for col_data in (config.get("collections") or {}).values():
            for source in col_data.get("sources") or []:
                raw_path = source.get("path", "")
                source_path = Path(raw_path)
                if not source_path.is_absolute():
                    source_path = config_dir / source_path
                source_path = source_path.resolve()

                if not source_path.exists():
                    continue

                patterns = source.get("patterns") or ["*.md"]
                recursive = source.get("recursive", True)

                for f in self._glob_source(source_path, patterns, recursive):
                    resolved = f.resolve()
                    if resolved.is_file() and resolved not in seen:
                        seen.add(resolved)
                        files.append(resolved)

        return [self._make_corpus_file(f) for f in sorted(files)]

    def _make_corpus_file(self, path: Path) -> CorpusFile:
        data = path.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        try:
            rel = str(path.relative_to(self.target_path))
        except ValueError:
            rel = str(path)
        return CorpusFile(path=rel, sha256=sha, size_bytes=len(data))

    # ── Snapshot ──────────────────────────────────────────────────────────────

    def snapshot(self, config_yaml_path: Path) -> dict:
        """Build the corpus section of ``manifest.json``.

        Returns ``{files: [...], hash: str, total_files: int}`` where *hash*
        is a 16-hex-char digest over all (path, sha256) pairs — changes when
        any file is added, removed, or modified.
        """
        files = self.enumerate_from_config(config_yaml_path)
        combined = "|".join(f"{f.path}:{f.sha256}" for f in files).encode()
        corpus_hash = hashlib.sha256(combined).hexdigest()[:16]
        return {
            "files": [
                {"path": f.path, "sha256": f.sha256, "size_bytes": f.size_bytes}
                for f in files
            ],
            "hash": corpus_hash,
            "total_files": len(files),
        }
