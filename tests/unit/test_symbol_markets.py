"""Tests for SymbolMarkets scraper module."""

from typing import Dict, Iterator
from unittest import mock
from unittest.mock import MagicMock

import pytest

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.core.exceptions import NetworkError
from tv_scraper.scrapers.screening.symbol_markets import SymbolMarkets


@pytest.fixture
def symbol_markets() -> Iterator[SymbolMarkets]:
    """Create a SymbolMarkets instance for testing."""
    yield SymbolMarkets()


def _mock_response(data: Dict) -> MagicMock:
    """Create a mock requests.Response with a .json() method."""
    response = MagicMock()
    response.json.return_value = data
    response.status_code = 200
    return response


class TestInheritance:
    """Verify SymbolMarkets inherits from BaseScraper."""

    def test_inherits_base_scraper(self) -> None:
        """SymbolMarkets must be a subclass of BaseScraper."""
        assert issubclass(SymbolMarkets, BaseScraper)


class TestScrapeSuccess:
    """Tests for successful scraping scenarios."""

    def test_scrape_success(self, symbol_markets: SymbolMarkets) -> None:
        """Default params return success envelope with data list."""
        mock_resp = _mock_response({
            "data": [
                {
                    "s": "NASDAQ:AAPL",
                    "d": [
                        "AAPL", 150.25, 2.5, 3.75, 50000000,
                        "NASDAQ", "stock", "Apple Inc.", "USD", 2500000000000,
                    ],
                },
                {
                    "s": "GPW:AAPL",
                    "d": [
                        "AAPL", 148.50, 1.2, 1.80, 1000000,
                        "GPW", "stock", "Apple Inc.", "PLN", 2500000000000,
                    ],
                },
            ],
            "totalCount": 2,
        })
        with mock.patch.object(symbol_markets, "_make_request", return_value=mock_resp):
            result = symbol_markets.scrape(symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 2
        assert result["data"][0]["symbol"] == "NASDAQ:AAPL"
        assert result["data"][0]["name"] == "AAPL"
        assert result["data"][0]["close"] == 150.25
        assert result["data"][1]["symbol"] == "GPW:AAPL"
        assert result["error"] is None

    def test_scrape_custom_fields(self, symbol_markets: SymbolMarkets) -> None:
        """Custom fields list is used instead of defaults."""
        custom_fields = ["name", "close", "volume", "exchange"]
        mock_resp = _mock_response({
            "data": [
                {"s": "NASDAQ:AAPL", "d": ["AAPL", 150.0, 50000000, "NASDAQ"]},
            ],
            "totalCount": 1,
        })
        with mock.patch.object(
            symbol_markets, "_make_request", return_value=mock_resp
        ) as mock_req:
            result = symbol_markets.scrape(symbol="AAPL", fields=custom_fields)

        assert result["status"] == STATUS_SUCCESS
        assert result["data"][0]["name"] == "AAPL"
        assert result["data"][0]["close"] == 150.0
        assert result["data"][0]["volume"] == 50000000
        assert result["data"][0]["exchange"] == "NASDAQ"

        # Verify the payload sent to the API used custom fields
        call_kwargs = mock_req.call_args[1]
        payload = call_kwargs["json_data"]
        assert payload["columns"] == custom_fields

    def test_scrape_custom_scanner(self, symbol_markets: SymbolMarkets) -> None:
        """Custom scanner is used in the URL."""
        mock_resp = _mock_response({
            "data": [
                {"s": "BINANCE:BTCUSD", "d": [
                    "BTCUSD", 50000.0, 5.0, 2500.0, 1000000,
                    "BINANCE", "crypto", "Bitcoin / USD", "USD", 900000000000,
                ]},
            ],
            "totalCount": 1,
        })
        with mock.patch.object(
            symbol_markets, "_make_request", return_value=mock_resp
        ) as mock_req:
            result = symbol_markets.scrape(symbol="BTCUSD", scanner="crypto")

        assert result["status"] == STATUS_SUCCESS
        # Verify the scanner-specific URL was used
        call_args = mock_req.call_args
        url = call_args[0][0]
        assert "crypto" in url

    def test_scrape_with_limit(self, symbol_markets: SymbolMarkets) -> None:
        """Limit param controls the range in the API payload."""
        mock_resp = _mock_response({
            "data": [
                {"s": "NASDAQ:AAPL", "d": [
                    "AAPL", 150.0, 2.5, 3.75, 50000000,
                    "NASDAQ", "stock", "Apple Inc.", "USD", 2500000000000,
                ]},
            ],
            "totalCount": 100,
        })
        with mock.patch.object(
            symbol_markets, "_make_request", return_value=mock_resp
        ) as mock_req:
            result = symbol_markets.scrape(symbol="AAPL", limit=25)

        assert result["status"] == STATUS_SUCCESS
        call_kwargs = mock_req.call_args[1]
        payload = call_kwargs["json_data"]
        assert payload["range"] == [0, 25]


class TestScrapeErrors:
    """Tests for error handling — returns error responses, never raises."""

    def test_scrape_invalid_scanner(self, symbol_markets: SymbolMarkets) -> None:
        """Invalid scanner returns error response, does not raise."""
        result = symbol_markets.scrape(symbol="AAPL", scanner="invalid-scanner")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "scanner" in result["error"].lower()

    def test_scrape_empty_symbol(self, symbol_markets: SymbolMarkets) -> None:
        """Empty symbol returns error response, does not raise."""
        result = symbol_markets.scrape(symbol="")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "symbol" in result["error"].lower()

    def test_scrape_network_error(self, symbol_markets: SymbolMarkets) -> None:
        """Network error returns error response, does not raise."""
        with mock.patch.object(
            symbol_markets,
            "_make_request",
            side_effect=NetworkError("Connection refused"),
        ):
            result = symbol_markets.scrape(symbol="AAPL")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Connection refused" in result["error"]


class TestResponseFormat:
    """Tests for response envelope structure."""

    def test_response_has_standard_envelope(self, symbol_markets: SymbolMarkets) -> None:
        """Success response contains exactly status/data/metadata/error keys."""
        mock_resp = _mock_response({
            "data": [
                {"s": "NASDAQ:AAPL", "d": [
                    "AAPL", 150.0, 2.5, 3.75, 50000000,
                    "NASDAQ", "stock", "Apple Inc.", "USD", 2500000000000,
                ]},
            ],
            "totalCount": 50,
        })
        with mock.patch.object(symbol_markets, "_make_request", return_value=mock_resp):
            result = symbol_markets.scrape(symbol="AAPL")

        assert set(result.keys()) == {"status", "data", "metadata", "error"}
        assert result["metadata"]["total"] == 1
        assert "total_available" in result["metadata"]
        assert result["metadata"]["scanner"] == "global"

    def test_error_response_has_standard_envelope(
        self, symbol_markets: SymbolMarkets
    ) -> None:
        """Error response has same envelope keys as success."""
        result = symbol_markets.scrape(symbol="AAPL", scanner="invalid")
        assert set(result.keys()) == {"status", "data", "metadata", "error"}
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None


class TestUsesMapScannerRows:
    """Verify SymbolMarkets delegates row mapping to _map_scanner_rows."""

    def test_uses_map_scanner_rows(self, symbol_markets: SymbolMarkets) -> None:
        """scrape() calls _map_scanner_rows to transform API data."""
        raw_items = [
            {"s": "NASDAQ:AAPL", "d": [
                "AAPL", 150.0, 2.5, 3.75, 50000000,
                "NASDAQ", "stock", "Apple Inc.", "USD", 2500000000000,
            ]},
        ]
        mock_resp = _mock_response({
            "data": raw_items,
            "totalCount": 1,
        })
        with mock.patch.object(symbol_markets, "_make_request", return_value=mock_resp):
            with mock.patch.object(
                symbol_markets,
                "_map_scanner_rows",
                wraps=symbol_markets._map_scanner_rows,
            ) as mock_map:
                result = symbol_markets.scrape(symbol="AAPL")

        mock_map.assert_called_once_with(raw_items, symbol_markets.DEFAULT_FIELDS)
        assert result["status"] == STATUS_SUCCESS
        assert result["data"][0]["symbol"] == "NASDAQ:AAPL"
        assert result["data"][0]["name"] == "AAPL"
