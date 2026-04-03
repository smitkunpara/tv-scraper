"""Tests for Screener scraper module."""

from collections.abc import Iterator
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
import requests

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.screening.screener import Screener


@pytest.fixture
def screener() -> Iterator[Screener]:
    """Create a Screener instance for testing."""
    yield Screener()


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


class TestScreenerInheritance:
    """Verify Screener inherits from BaseScraper."""

    def test_inherits_base_scraper(self) -> None:
        """Screener must be a subclass of BaseScraper."""
        assert issubclass(Screener, BaseScraper)


class TestScreenSuccess:
    """Tests for successful screening scenarios."""

    @patch("requests.post")
    def test_get_data_success(self, mock_post: MagicMock, screener: Screener) -> None:
        """Default params return success envelope with data list."""
        mock_post.return_value = _mock_response(
            {
                "data": [
                    {
                        "s": "NASDAQ:AAPL",
                        "d": [
                            "Apple Inc.",
                            150.25,
                            2.5,
                            3.75,
                            50000000,
                            0.8,
                            2500000000000,
                            25.5,
                            6.0,
                        ],
                    },
                    {
                        "s": "NASDAQ:GOOGL",
                        "d": [
                            "Alphabet Inc.",
                            2800.0,
                            1.8,
                            50.0,
                            30000000,
                            0.7,
                            1800000000000,
                            28.0,
                            100.0,
                        ],
                    },
                ],
                "totalCount": 500,
            }
        )
        result = screener.get_screener(market="america", limit=10)

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 2
        assert result["data"][0]["symbol"] == "NASDAQ:AAPL"
        assert result["data"][0]["name"] == "Apple Inc."
        assert result["data"][0]["close"] == 150.25
        assert result["error"] is None
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_get_data_custom_fields(
        self, mock_post: MagicMock, screener: Screener
    ) -> None:
        """Custom fields list is used instead of defaults."""
        custom_fields = ["name", "close", "volume"]
        mock_post.return_value = _mock_response(
            {
                "data": [
                    {"s": "NASDAQ:AAPL", "d": ["Apple Inc.", 150.0, 50000000]},
                ],
                "totalCount": 1,
            }
        )
        result = screener.get_screener(market="america", fields=custom_fields, limit=5)

        assert result["status"] == STATUS_SUCCESS
        assert result["data"][0]["name"] == "Apple Inc."
        assert result["data"][0]["close"] == 150.0
        assert result["data"][0]["volume"] == 50000000

        # Verify the payload sent to the API used custom fields
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["columns"] == custom_fields

    @patch("requests.post")
    def test_get_data_with_filters(
        self, mock_post: MagicMock, screener: Screener
    ) -> None:
        """Filter objects are included in the API payload."""
        filters = [
            {"left": "close", "operation": "greater", "right": 100},
            {"left": "volume", "operation": "greater", "right": 1000000},
        ]
        mock_post.return_value = _mock_response(
            {
                "data": [
                    {
                        "s": "NASDAQ:AAPL",
                        "d": [
                            "Apple Inc.",
                            150.0,
                            2.5,
                            3.75,
                            50000000,
                            0.8,
                            2500000000000,
                            25.5,
                            6.0,
                        ],
                    },
                ],
                "totalCount": 1,
            }
        )
        result = screener.get_screener(market="america", filters=filters)

        assert result["status"] == STATUS_SUCCESS
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["filter"] == filters

    @patch("requests.post")
    def test_get_data_with_sort(self, mock_post: MagicMock, screener: Screener) -> None:
        """sort_by and sort_order are included in the API payload."""
        mock_post.return_value = _mock_response(
            {
                "data": [
                    {
                        "s": "NASDAQ:AAPL",
                        "d": [
                            "Apple Inc.",
                            150.0,
                            2.5,
                            3.75,
                            50000000,
                            0.8,
                            2500000000000,
                            25.5,
                            6.0,
                        ],
                    },
                ],
                "totalCount": 1,
            }
        )
        result = screener.get_screener(
            market="america", sort_by="volume", sort_order="asc"
        )

        assert result["status"] == STATUS_SUCCESS
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["sort"]["sortBy"] == "volume"
        assert payload["sort"]["sortOrder"] == "asc"

    @patch("requests.post")
    def test_markets_auto_derived_from_market(
        self, mock_post: MagicMock, screener: Screener
    ) -> None:
        """markets is always set to [market] regardless of input."""
        mock_post.return_value = _mock_response({"data": [], "totalCount": 0})

        screener.get_screener(market="uk")

        payload = mock_post.call_args[1]["json"]
        assert payload["markets"] == ["uk"]

    @patch("requests.post")
    def test_get_data_with_symbols_markets_and_filter2(
        self, mock_post: MagicMock, screener: Screener
    ) -> None:
        """New passthrough payload keys are included when provided."""
        mock_post.return_value = _mock_response({"data": [], "totalCount": 0})
        symbols = {"tickers": ["NASDAQ:AAPL", "NASDAQ:MSFT"]}
        filter2 = {
            "operator": "and",
            "operands": [
                {
                    "expression": {
                        "left": "type",
                        "operation": "equal",
                        "right": "stock",
                    }
                }
            ],
        }

        result = screener.get_screener(
            market="america",
            symbols=symbols,
            filter2=filter2,
        )

        assert result["status"] == STATUS_SUCCESS
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["symbols"] == symbols
        assert payload["markets"] == ["america"]
        assert payload["filter2"] == filter2

    @patch("requests.post")
    def test_get_data_with_limit(
        self, mock_post: MagicMock, screener: Screener
    ) -> None:
        """Limit param controls the range in the API payload."""
        mock_post.return_value = _mock_response(
            {
                "data": [
                    {
                        "s": "NASDAQ:AAPL",
                        "d": [
                            "Apple",
                            150.0,
                            2.5,
                            3.75,
                            50000000,
                            0.8,
                            2500000000000,
                            25.5,
                            6.0,
                        ],
                    },
                ],
                "totalCount": 100,
            }
        )
        result = screener.get_screener(market="america", limit=25)

        assert result["status"] == STATUS_SUCCESS
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["range"] == [0, 25]


class TestScreenErrors:
    """Tests for error handling — returns error responses, never raises."""

    def test_get_data_invalid_market(self, screener: Screener) -> None:
        """Invalid market returns error response, does not raise."""
        result = screener.get_screener(market="invalid_market")
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "market" in result["error"].lower()

    @patch("requests.post")
    def test_get_data_network_error(
        self, mock_post: MagicMock, screener: Screener
    ) -> None:
        """Network error returns error response, does not raise."""
        mock_post.side_effect = requests.RequestException("Connection refused")
        result = screener.get_screener(market="america")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Connection refused" in result["error"]


class TestResponseFormat:
    """Tests for response envelope structure."""

    @patch("requests.post")
    def test_response_has_standard_envelope(
        self, mock_post: MagicMock, screener: Screener
    ) -> None:
        """Success response contains exactly status/data/metadata/error keys."""
        mock_post.return_value = _mock_response(
            {
                "data": [
                    {
                        "s": "NASDAQ:AAPL",
                        "d": [
                            "Apple",
                            150.0,
                            2.5,
                            3.75,
                            50000000,
                            0.8,
                            2500000000000,
                            25.5,
                            6.0,
                        ],
                    },
                ],
                "totalCount": 1,
            }
        )
        result = screener.get_screener(market="america")

        assert set(result.keys()) == {"status", "data", "metadata", "error"}
        assert result["metadata"]["market"] == "america"
        assert result["metadata"]["total"] == 1
        assert "total_available" in result["metadata"]

    def test_error_response_has_standard_envelope(self, screener: Screener) -> None:
        """Error response has same envelope keys as success."""
        result = screener.get_screener(market="invalid_market")
        assert set(result.keys()) == {"status", "data", "metadata", "error"}
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None


class TestUsesMapScannerRows:
    """Verify Screener delegates row mapping to _map_scanner_rows."""

    @patch("requests.post")
    def test_uses_map_scanner_rows(
        self, mock_post: MagicMock, screener: Screener
    ) -> None:
        """get_data() calls _map_scanner_rows to transform API data."""
        raw_items = [
            {"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]},
        ]
        mock_post.return_value = _mock_response(
            {
                "data": raw_items,
                "totalCount": 1,
            }
        )
        fields = ["name", "close"]
        with mock.patch.object(
            screener,
            "_map_scanner_rows",
            wraps=screener._map_scanner_rows,
        ) as mock_map:
            result = screener.get_screener(market="america", fields=fields)

        mock_map.assert_called_once_with(raw_items, fields)
        assert result["status"] == STATUS_SUCCESS
        assert result["data"][0]["symbol"] == "NASDAQ:AAPL"
        assert result["data"][0]["name"] == "Apple"


class TestDefaultFields:
    """Tests for market-specific default fields."""

    @patch("requests.post")
    def test_crypto_default_fields(
        self, mock_post: MagicMock, screener: Screener
    ) -> None:
        """Crypto market uses crypto-specific default fields."""
        mock_post.return_value = _mock_response(
            {
                "data": [
                    {
                        "s": "BINANCE:BTCUSD",
                        "d": [
                            "Bitcoin",
                            50000.0,
                            5.0,
                            2500.0,
                            1000000,
                            900000000000,
                            0.9,
                        ],
                    },
                ],
                "totalCount": 1,
            }
        )
        screener.get_screener(market="crypto")

        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert "market_cap_calc" in payload["columns"]

    @patch("requests.post")
    def test_forex_default_fields(
        self, mock_post: MagicMock, screener: Screener
    ) -> None:
        """Forex market uses forex-specific default fields."""
        mock_post.return_value = _mock_response(
            {
                "data": [
                    {"s": "FX:EURUSD", "d": ["EUR/USD", 1.10, 0.5, 0.005, 0.7]},
                ],
                "totalCount": 1,
            }
        )
        screener.get_screener(market="forex")

        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert "Recommend.All" in payload["columns"]
        # Forex defaults should NOT have volume
        assert "volume" not in payload["columns"]
