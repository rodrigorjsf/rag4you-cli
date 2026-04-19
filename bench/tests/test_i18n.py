from __future__ import annotations

import warnings
from pathlib import Path

import pytest
import yaml

LOCALES_DIR = Path(__file__).parent.parent / "locales"


def _load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _collect_keys(data: dict, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    for k, v in data.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys |= _collect_keys(v, full_key)
        else:
            keys.add(full_key)
    return keys


@pytest.fixture(autouse=True)
def reset_locale():
    from bench.i18n import set_locale

    set_locale("en")
    yield
    set_locale("en")


def test_locale_parity():
    """Every key in en.yaml must exist in pt.yaml and vice versa."""
    en = _load_yaml(LOCALES_DIR / "en.yaml")
    pt = _load_yaml(LOCALES_DIR / "pt.yaml")
    en_keys = _collect_keys(en)
    pt_keys = _collect_keys(pt)
    missing_in_pt = en_keys - pt_keys
    missing_in_en = pt_keys - en_keys
    assert not missing_in_pt, f"Keys in en.yaml but not pt.yaml: {sorted(missing_in_pt)}"
    assert not missing_in_en, f"Keys in pt.yaml but not en.yaml: {sorted(missing_in_en)}"


def test_missing_key_returns_key_string():
    from bench.i18n import t

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = t("definitely.missing.key.xyz.abc")
    assert result == "definitely.missing.key.xyz.abc"
    assert any("missing" in str(warning.message).lower() for warning in w)


def test_t_returns_nonempty_string_for_known_key():
    from bench.i18n import t

    result = t("cli.run.aborted")
    assert isinstance(result, str)
    assert len(result) > 0


def test_t_interpolates_vars():
    from bench.i18n import t

    result = t("cli.run.starting", run_id="test-run-001")
    assert "test-run-001" in result


def test_t_pt_locale_returns_nonempty_string():
    from bench.i18n import set_locale, t

    set_locale("pt")
    result = t("cli.run.aborted")
    assert isinstance(result, str)
    assert len(result) > 0


def test_t_pt_locale_differs_from_en():
    from bench.i18n import set_locale, t

    set_locale("en")
    en_result = t("cli.run.aborted")
    set_locale("pt")
    pt_result = t("cli.run.aborted")
    assert en_result != pt_result


def test_t_unknown_locale_falls_back_to_en():
    from bench.i18n import set_locale, t

    set_locale("xx")
    result = t("cli.run.aborted")
    assert isinstance(result, str)
    assert len(result) > 0


def test_t_missing_interpolation_var_returns_template():
    from bench.i18n import t

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        result = t("cli.run.starting")
    assert isinstance(result, str)
    assert len(result) > 0
