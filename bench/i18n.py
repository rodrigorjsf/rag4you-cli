from __future__ import annotations

import os
import warnings
from pathlib import Path

import yaml

_locale_cache: dict[str, dict] = {}
_active_locale: str = os.environ.get("RAG4YOU_LANG", "en")
_locales_dir = Path(__file__).parent / "locales"


def set_locale(code: str) -> None:
    global _active_locale
    _active_locale = code


def get_active_locale() -> str:
    return _active_locale


def _load(code: str) -> dict:
    if code not in _locale_cache:
        path = _locales_dir / f"{code}.yaml"
        if not path.exists():
            warnings.warn(
                f"Locale file not found: {path}; falling back to 'en'",
                stacklevel=3,
            )
            _locale_cache[code] = _load("en")
        else:
            with open(path) as f:
                _locale_cache[code] = yaml.safe_load(f) or {}
    return _locale_cache[code]


def _get_nested(data: dict, keys: list[str]) -> str | None:
    current: object = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current if isinstance(current, str) else None


def t(key: str, **vars: object) -> str:
    """Resolve a dotted locale key and interpolate variables.

    Precedence for locale selection: set_locale() > RAG4YOU_LANG env > "en".
    The env var is applied at module import time; set_locale() overrides it.
    Missing key: returns key string verbatim + emits warning. Never raises.
    """
    parts = key.split(".")
    locale_data = _load(_active_locale)
    value = _get_nested(locale_data, parts)

    if value is None and _active_locale != "en":
        value = _get_nested(_load("en"), parts)

    if value is None:
        warnings.warn(f"Missing locale key: {key!r}", stacklevel=2)
        return key

    if vars:
        try:
            return value.format(**vars)
        except KeyError as exc:
            warnings.warn(
                f"Missing interpolation var {exc} for locale key {key!r}",
                stacklevel=2,
            )
    return value
