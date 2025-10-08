"""Utilities for retrieving exchange rates from remote APIs."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Dict, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

LOGGER = logging.getLogger(__name__)


class ExchangeRateError(RuntimeError):
    """Raised when the exchange rate API returns an unexpected result."""


@dataclass
class ExchangeRateFetcher:
    """Fetch exchange rates using an HTTP based API."""

    api_url: str

    def fetch_rates(self, base_currency: str, symbols: Iterable[str]) -> Dict[str, float]:
        params = {
            "base": base_currency.upper(),
            "symbols": ",".join(sorted({s.upper() for s in symbols})),
        }
        query = urlencode(params)
        request = Request(f"{self.api_url}?{query}")
        LOGGER.debug("Requesting rates from %s", request.full_url)
        try:
            with urlopen(request, timeout=10) as response:  # nosec B310
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise ExchangeRateError(f"Exchange rate API returned {exc.code}") from exc
        except URLError as exc:
            raise ExchangeRateError("Failed to reach exchange rate API") from exc
        except json.JSONDecodeError as exc:
            raise ExchangeRateError("Exchange rate API returned invalid JSON") from exc
        except Exception as exc:  # pragma: no cover - defensive
            raise ExchangeRateError("Unexpected error contacting exchange rate API") from exc

        if not isinstance(payload, dict):
            raise ExchangeRateError("Exchange rate API returned malformed payload")
        if not payload.get("success", True):
            raise ExchangeRateError("Exchange rate API indicated failure")

        rates = payload.get("rates")
        if not isinstance(rates, dict):
            raise ExchangeRateError("Exchange rate API returned malformed rates")

        converted: Dict[str, float] = {}
        for symbol in symbols:
            key = symbol.upper()
            try:
                converted[key] = float(rates[key])
            except (KeyError, TypeError, ValueError) as exc:
                raise ExchangeRateError(f"Missing or invalid rate for {key}") from exc

        LOGGER.info("Fetched rates: %s", converted)
        return converted
