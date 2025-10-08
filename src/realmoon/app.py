"""Application entry points for the RealMoon monitoring service."""

from __future__ import annotations

import logging
import signal
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator, Optional

from .config import AppConfig, load_config
from .fetcher import ExchangeRateError, ExchangeRateFetcher
from .monitor import Alert, RateObservation, ThresholdMonitor

LOGGER = logging.getLogger(__name__)


@contextmanager
def _graceful_interrupt() -> Iterator[None]:
    """Context manager to gracefully handle ``SIGINT`` during monitoring."""

    received = {"flag": False}

    def handler(signum, frame):  # type: ignore[override]
        LOGGER.info("Received interrupt signal, shutting down after current iteration")
        received["flag"] = True

    original_handler = signal.signal(signal.SIGINT, handler)
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, original_handler)
        if received["flag"]:
            raise KeyboardInterrupt


def run_once(config: AppConfig, fetcher: ExchangeRateFetcher, monitor: ThresholdMonitor) -> Iterable[Alert]:
    """Fetch the latest rates and evaluate thresholds once."""

    LOGGER.debug("Starting single monitoring iteration")
    try:
        rates = fetcher.fetch_rates(config.base_currency, config.currencies)
    except ExchangeRateError as exc:
        LOGGER.error("Failed to fetch exchange rates: %s", exc)
        return []

    timestamp = datetime.utcnow()
    observations = [
        RateObservation(currency=currency, rate=rate, timestamp=timestamp)
        for currency, rate in rates.items()
    ]
    alerts = monitor.evaluate(observations)

    for observation in observations:
        LOGGER.info(
            "[%s] %s/%s = %.6f",
            observation.timestamp.isoformat(),
            config.base_currency,
            observation.currency,
            observation.rate,
        )
    for alert in alerts:
        LOGGER.warning(alert.to_message())

    return alerts


def run_monitoring(config_path: Optional[Path] = None) -> None:
    """Run the monitoring loop until interrupted."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = load_config(config_path)
    fetcher = ExchangeRateFetcher(api_url=config.api_url)
    monitor = ThresholdMonitor(config=config)

    LOGGER.info(
        "Starting RealMoon monitor for %s against %s with interval %ss",
        ", ".join(config.currencies),
        config.base_currency,
        config.interval_seconds,
    )

    try:
        with _graceful_interrupt():
            while True:
                run_once(config, fetcher, monitor)
                time.sleep(config.interval_seconds)
    except KeyboardInterrupt:
        LOGGER.info("Monitoring stopped by user")
    except Exception:
        LOGGER.exception("Monitoring stopped due to unexpected error")
        raise


def main(argv: Optional[Iterable[str]] = None) -> int:
    """CLI entry point."""

    import argparse

    parser = argparse.ArgumentParser(description="RealMoon exchange rate monitor")
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to YAML configuration file with thresholds and interval",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Fetch rates once and print alerts without entering monitoring loop",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = load_config(args.config)
    fetcher = ExchangeRateFetcher(api_url=config.api_url)
    monitor = ThresholdMonitor(config=config)

    if args.once:
        run_once(config, fetcher, monitor)
        return 0

    try:
        run_monitoring(args.config)
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    sys.exit(main())
