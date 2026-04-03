from collections.abc import Iterator
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
import requests

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.screening.symbol_markets import SymbolMarkets


@pytest.fixture
def symbol_markets() -> Iterator[SymbolMarkets]:
    """Create a SymbolMarkets instance for testing."""
    yield SymbolMarkets()


def _mock_response(data: dict, status_code: int = 200) -> MagicMock:
    """Create a mock requests.Response with a .json() method."""
    response = MagicMock()
    response.json.return_value = data
    response.status_code = status_code
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(
            f"Error {status_code}"
        )
    else:
        response.raise_for_status.return_value = None
    return response


class TestInheritance:
    """Verify SymbolMarkets inherits from BaseScraper."""

    def test_inherits_base_scraper(self) -> None:
        """SymbolMarkets must be a subclass of BaseScraper."""
        assert issubclass(SymbolMarkets, BaseScraper)


class TestScrapeSuccess:
    """Tests for successful scraping scenarios."""

    @patch("requests.post")
    def test_get_data_success(
        self, mock_post: MagicMock, symbol_markets: SymbolMarkets
    ) -> None:
        """Default params return success envelope with data list."""
        mock_post.return_value = _mock_response(
            {
                "data": [
                    {
                        "s": "NASDAQ:AAPL",
                        "d": [
                            "AAPL",
                            150.25,
                            2.5,
                            3.75,
                            50000000,
                            "NASDAQ",
                            "stock",
                            "Apple Inc.",
                            "USD",
                            2500000000000,
                        ],
                    },
                    {
                        "s": "GPW:AAPL",
                        "d": [
                            "AAPL",
                            148.50,
                            1.2,
                            1.80,
                            1000000,
                            "GPW",
                            "stock",
                            "Apple Inc.",
                            "PLN",
                            2500000000000,
                        ],
                    },
                ],
                "totalCount": 2,
            }
        )
        result = symbol_markets.get_symbol_markets(symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 2
        assert result["data"][0]["symbol"] == "NASDAQ:AAPL"
        assert result["data"][0]["name"] == "AAPL"
        assert result["data"][0]["close"] == 150.25
        assert result["data"][1]["symbol"] == "GPW:AAPL"
        assert result["error"] is None
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_get_data_custom_fields(
        self, mock_post: MagicMock, symbol_markets: SymbolMarkets
    ) -> None:
        """Custom fields list is used instead of defaults."""
        custom_fields = ["name", "close", "volume", "exchange"]
        mock_post.return_value = _mock_response(
            {
                "data": [
                    {"s": "NASDAQ:AAPL", "d": ["AAPL", 150.0, 50000000, "NASDAQ"]},
                ],
                "totalCount": 1,
            }
        )
        result = symbol_markets.get_symbol_markets(symbol="AAPL", fields=custom_fields)

        assert result["status"] == STATUS_SUCCESS
        assert result["data"][0]["name"] == "AAPL"
        assert result["data"][0]["close"] == 150.0
        assert result["data"][0]["volume"] == 50000000
        assert result["data"][0]["exchange"] == "NASDAQ"

        # Verify the payload sent to the API used custom fields
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["columns"] == custom_fields

    @patch("requests.post")
    def test_get_data_custom_scanner(
        self, mock_post: MagicMock, symbol_markets: SymbolMarkets
    ) -> None:
        """Custom scanner is used in the URL."""
        mock_post.return_value = _mock_response(
            {
                "data": [
                    {
                        "s": "BINANCE:BTCUSD",
                        "d": [
                            "BTCUSD",
                            50000.0,
                            5.0,
                            2500.0,
                            1000000,
                            "BINANCE",
                            "crypto",
                            "Bitcoin / USD",
                            "USD",
                            900000000000,
                        ],
                    },
                ],
                "totalCount": 1,
            }
        )
        result = symbol_markets.get_symbol_markets(symbol="BTCUSD", scanner="crypto")

        assert result["status"] == STATUS_SUCCESS
        # Verify the scanner-specific URL was used
        call_args = mock_post.call_args
        url = call_args[0][0]
        assert "crypto" in url

    @patch("requests.post")
    def test_get_data_with_limit(
        self, mock_post: MagicMock, symbol_markets: SymbolMarkets
    ) -> None:
        """Limit param controls the range in the API payload."""
        mock_post.return_value = _mock_response(
            {
                "data": [
                    {
                        "s": "NASDAQ:AAPL",
                        "d": [
                            "AAPL",
                            150.0,
                            2.5,
                            3.75,
                            50000000,
                            "NASDAQ",
                            "stock",
                            "Apple Inc.",
                            "USD",
                            2500000000000,
                        ],
                    },
                ],
                "totalCount": 100,
            }
        )
        result = symbol_markets.get_symbol_markets(symbol="AAPL", limit=25)

        assert result["status"] == STATUS_SUCCESS
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["range"] == [0, 25]


class TestScrapeErrors:
    """Tests for error handling — returns error responses, never raises."""

    def test_get_data_invalid_scanner(self, symbol_markets: SymbolMarkets) -> None:
        """Invalid scanner returns error response, does not raise."""
        result = symbol_markets.get_symbol_markets(
            symbol="AAPL", scanner="invalid-scanner"
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "scanner" in result["error"].lower()

    def test_get_data_empty_symbol(self, symbol_markets: SymbolMarkets) -> None:
        """Empty symbol returns error response, does not raise."""
        result = symbol_markets.get_symbol_markets(symbol="")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "symbol" in result["error"].lower()

    @patch("requests.post")
    def test_get_data_network_error(
        self, mock_post: MagicMock, symbol_markets: SymbolMarkets
    ) -> None:
        """Network error returns error response, does not raise."""
        mock_post.side_effect = requests.RequestException("Connection refused")
        result = symbol_markets.get_symbol_markets(symbol="AAPL")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Connection refused" in result["error"]


class TestResponseFormat:
    """Tests for response envelope structure."""

    @patch("requests.post")
    def test_response_has_standard_envelope(
        self, mock_post: MagicMock, symbol_markets: SymbolMarkets
    ) -> None:
        """Success response contains exactly status/data/metadata/error keys."""
        mock_post.return_value = _mock_response(
            {
                "data": [
                    {
                        "s": "NASDAQ:AAPL",
                        "d": [
                            "AAPL",
                            150.0,
                            2.5,
                            3.75,
                            50000000,
                            "NASDAQ",
                            "stock",
                            "Apple Inc.",
                            "USD",
                            2500000000000,
                        ],
                    },
                ],
                "totalCount": 50,
            }
        )
        result = symbol_markets.get_symbol_markets(symbol="AAPL")

        assert set(result.keys()) == {"status", "data", "metadata", "error"}
        assert result["metadata"]["total"] == 1
        assert "total_available" in result["metadata"]
        assert result["metadata"]["scanner"] == "global"

    def test_error_response_has_standard_envelope(
        self, symbol_markets: SymbolMarkets
    ) -> None:
        """Error response has same envelope keys as success."""
        result = symbol_markets.get_symbol_markets(symbol="AAPL", scanner="invalid")
        assert set(result.keys()) == {"status", "data", "metadata", "error"}
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None


class TestUsesMapScannerRows:
    """Verify SymbolMarkets delegates row mapping to _map_scanner_rows."""

    @patch("requests.post")
    def test_uses_map_scanner_rows(
        self, mock_post: MagicMock, symbol_markets: SymbolMarkets
    ) -> None:
        """get_data() calls _map_scanner_rows to transform API data."""
        raw_items = [
            {
                "s": "NASDAQ:AAPL",
                "d": [
                    "AAPL",
                    150.0,
                    2.5,
                    3.75,
                    50000000,
                    "NASDAQ",
                    "stock",
                    "Apple Inc.",
                    "USD",
                    2500000000000,
                ],
            },
        ]
        mock_post.return_value = _mock_response(
            {
                "data": raw_items,
                "totalCount": 1,
            }
        )
        with mock.patch.object(
            symbol_markets,
            "_map_scanner_rows",
            wraps=symbol_markets._map_scanner_rows,
        ) as mock_map:
            result = symbol_markets.get_symbol_markets(symbol="AAPL")

        mock_map.assert_called_once_with(raw_items, symbol_markets.DEFAULT_FIELDS)
        assert result["status"] == STATUS_SUCCESS
        assert result["data"][0]["symbol"] == "NASDAQ:AAPL"
        assert result["data"][0]["name"] == "AAPL"
