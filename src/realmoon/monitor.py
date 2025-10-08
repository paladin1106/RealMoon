"""Monitoring and alerting utilities for exchange rates."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List

from .config import AppConfig, CurrencyThreshold

LOGGER = logging.getLogger(__name__)


@dataclass
class RateObservation:
    currency: str
    rate: float
    timestamp: datetime


@dataclass
class Alert:
    currency: str
    rate: float
    threshold: float
    direction: str
    timestamp: datetime

    def to_message(self) -> str:
        return (
            f"[{self.timestamp.isoformat()}] {self.currency} rate {self.rate:.6f} "
            f"crossed {self.direction} threshold {self.threshold:.6f}"
        )


class ThresholdMonitor:
    """Apply configured thresholds to exchange rates and produce alerts."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def evaluate(self, observations: Iterable[RateObservation]) -> List[Alert]:
        alerts: List[Alert] = []
        thresholds: Dict[str, CurrencyThreshold] = self._config.thresholds
        for observation in observations:
            threshold = thresholds.get(observation.currency)
            if not threshold:
                continue

            if threshold.lower is not None and observation.rate < threshold.lower:
                alerts.append(
                    Alert(
                        currency=observation.currency,
                        rate=observation.rate,
                        threshold=threshold.lower,
                        direction="lower",
                        timestamp=observation.timestamp,
                    )
                )

            if threshold.upper is not None and observation.rate > threshold.upper:
                alerts.append(
                    Alert(
                        currency=observation.currency,
                        rate=observation.rate,
                        threshold=threshold.upper,
                        direction="upper",
                        timestamp=observation.timestamp,
                    )
                )
        if alerts:
            LOGGER.warning("Alerts triggered: %s", ", ".join(a.to_message() for a in alerts))
        else:
            LOGGER.debug("No alerts triggered for current observations")
        return alerts
