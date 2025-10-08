from pathlib import Path

import pytest

from realmoon.config import AppConfig, CurrencyThreshold, load_config


def test_default_config():
    config = load_config(None)
    assert config.base_currency == "CNY"
    assert set(config.currencies) == {"USD", "AUD", "JPY"}
    assert config.interval_seconds == 900
    assert config.thresholds == {}


def test_load_config(tmp_path: Path):
    content = """
base_currency: cny
currencies:
  - usd
interval_seconds: 120
thresholds:
  usd:
    lower: 0.1
    upper: 0.2
"""
    path = tmp_path / "config.yml"
    path.write_text(content, encoding="utf-8")

    config = load_config(path)
    assert config.base_currency == "CNY"
    assert list(config.currencies) == ["USD"]
    assert config.interval_seconds == 120
    assert config.thresholds["USD"] == CurrencyThreshold(currency="USD", lower=0.1, upper=0.2)


def test_invalid_threshold(tmp_path: Path):
    path = tmp_path / "config.yml"
    path.write_text(
        """
thresholds:
  usd:
    lower: 0.3
    upper: 0.2
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_config(path)


def test_invalid_interval(tmp_path: Path):
    path = tmp_path / "config.yml"
    path.write_text("interval_seconds: 0\n", encoding="utf-8")

    with pytest.raises(ValueError):
        load_config(path)
