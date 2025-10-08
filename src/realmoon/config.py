"""Configuration handling for the RealMoon monitoring application."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Optional

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback
    from . import _yaml as yaml


@dataclass
class CurrencyThreshold:
    """Threshold definition for a single currency pair.

    Attributes
    ----------
    currency: str
        The target currency code (e.g. ``"USD"``) relative to CNY.
    lower: Optional[float]
        Lower bound for the exchange rate. Alerts will be raised when the
        observed rate drops below this value.
    upper: Optional[float]
        Upper bound for the exchange rate. Alerts will be raised when the
        observed rate exceeds this value.
    """

    currency: str
    lower: Optional[float] = None
    upper: Optional[float] = None

    def validate(self) -> None:
        if self.lower is not None and self.upper is not None and self.lower > self.upper:
            raise ValueError(
                f"Lower threshold {self.lower} cannot be greater than upper threshold {self.upper} "
                f"for currency {self.currency}."
            )


@dataclass
class AppConfig:
    """Top-level application configuration."""

    base_currency: str = "CNY"
    currencies: Iterable[str] = field(default_factory=lambda: ["USD", "AUD", "JPY"])
    thresholds: Dict[str, CurrencyThreshold] = field(default_factory=dict)
    interval_seconds: int = 900
    api_url: str = "https://api.exchangerate.host/latest"

    def validate(self) -> None:
        if self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be a positive integer")
        for threshold in self.thresholds.values():
            threshold.validate()


def _load_yaml(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        content = handle.read()
    return yaml.safe_load(content) or {}


def load_config(path: Optional[Path]) -> AppConfig:
    """Load the application configuration from the provided YAML file.

    Parameters
    ----------
    path:
        Optional path to the YAML configuration file. When ``None`` a default
        configuration is returned.
    """

    if path is None:
        return AppConfig()

    data = _load_yaml(path)
    base_currency = data.get("base_currency", "CNY")
    currencies = data.get("currencies", ["USD", "AUD", "JPY"])
    interval_seconds = int(data.get("interval_seconds", 900))
    api_url = data.get("api_url", "https://api.exchangerate.host/latest")

    thresholds_config = data.get("thresholds", {})
    thresholds: Dict[str, CurrencyThreshold] = {}
    for currency, values in thresholds_config.items():
        thresholds[currency.upper()] = CurrencyThreshold(
            currency=currency.upper(),
            lower=values.get("lower"),
            upper=values.get("upper"),
        )

    config = AppConfig(
        base_currency=base_currency.upper(),
        currencies=[c.upper() for c in currencies],
        thresholds=thresholds,
        interval_seconds=interval_seconds,
        api_url=api_url,
    )
    config.validate()
    return config
