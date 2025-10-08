import json
from unittest.mock import MagicMock, patch

import pytest

from realmoon.fetcher import ExchangeRateError, ExchangeRateFetcher


@patch("realmoon.fetcher.urlopen")
def test_fetch_rates_success(mock_urlopen: MagicMock):
    response = MagicMock()
    response.read.return_value = json.dumps(
        {"success": True, "rates": {"USD": 0.14, "AUD": 0.21}}
    ).encode("utf-8")
    response.__enter__.return_value = response
    mock_urlopen.return_value = response

    fetcher = ExchangeRateFetcher(api_url="https://example.com")
    rates = fetcher.fetch_rates("CNY", ["USD", "AUD"])

    mock_urlopen.assert_called_once()
    assert rates == {"AUD": 0.21, "USD": 0.14}


@patch("realmoon.fetcher.urlopen")
def test_fetch_rates_failure_status(mock_urlopen: MagicMock):
    error = Exception("boom")
    mock_urlopen.side_effect = error

    fetcher = ExchangeRateFetcher(api_url="https://example.com")
    with pytest.raises(ExchangeRateError):
        fetcher.fetch_rates("CNY", ["USD"])


@patch("realmoon.fetcher.urlopen")
def test_fetch_rates_missing_symbol(mock_urlopen: MagicMock):
    response = MagicMock()
    response.read.return_value = json.dumps({"success": True, "rates": {}}).encode("utf-8")
    response.__enter__.return_value = response
    mock_urlopen.return_value = response

    fetcher = ExchangeRateFetcher(api_url="https://example.com")
    with pytest.raises(ExchangeRateError):
        fetcher.fetch_rates("CNY", ["USD"])
