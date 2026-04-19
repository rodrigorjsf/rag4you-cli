from __future__ import annotations

from pathlib import Path

import yaml

from .schema import GoldenQuery

_DATASET_PATH = Path(__file__).parent / "dataset.yaml"


def load_golden_queries() -> list[GoldenQuery]:
    with open(_DATASET_PATH) as f:
        data = yaml.safe_load(f) or []
    return [GoldenQuery.model_validate(item) for item in data]
