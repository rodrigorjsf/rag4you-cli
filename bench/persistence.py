from __future__ import annotations

import json
import os
from pathlib import Path


def append_jsonl(path: Path, record: dict) -> None:
    """Append one JSON record to a JSONL file, fsyncing before return."""
    path = Path(path)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        line = (json.dumps(record, ensure_ascii=False) + "\n").encode()
        os.write(fd, line)
        os.fsync(fd)
    finally:
        os.close(fd)


def write_json_atomic(path: Path, data: dict) -> None:
    """Write JSON atomically via tmp-file + rename; fsyncs data and parent dir."""
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    raw = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode()

    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        os.write(fd, raw)
        os.fsync(fd)
    finally:
        os.close(fd)

    os.rename(str(tmp), str(path))

    parent_fd = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)


def read_jsonl(path: Path) -> list[dict]:
    """Read all records from a JSONL file. Returns empty list if file missing."""
    path = Path(path)
    if not path.exists():
        return []
    records = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def read_json(path: Path) -> dict:
    """Read a JSON file and return its contents."""
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)
