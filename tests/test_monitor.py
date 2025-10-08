from datetime import datetime

from realmoon.config import AppConfig, CurrencyThreshold
from realmoon.monitor import RateObservation, ThresholdMonitor


def test_monitor_generates_alerts():
    config = AppConfig(
        thresholds={
            "USD": CurrencyThreshold(currency="USD", lower=0.12, upper=0.15),
            "JPY": CurrencyThreshold(currency="JPY", lower=20.0, upper=22.0),
        }
    )
    monitor = ThresholdMonitor(config)
    timestamp = datetime(2024, 1, 1)

    alerts = monitor.evaluate(
        [
            RateObservation(currency="USD", rate=0.11, timestamp=timestamp),
            RateObservation(currency="USD", rate=0.16, timestamp=timestamp),
            RateObservation(currency="JPY", rate=23.0, timestamp=timestamp),
        ]
    )

    assert len(alerts) == 3
    directions = {alert.direction for alert in alerts}
    assert directions == {"lower", "upper"}


def test_monitor_without_thresholds():
    config = AppConfig(thresholds={})
    monitor = ThresholdMonitor(config)
    timestamp = datetime.utcnow()
    alerts = monitor.evaluate(
        [RateObservation(currency="USD", rate=0.14, timestamp=timestamp)]
    )
    assert alerts == []
