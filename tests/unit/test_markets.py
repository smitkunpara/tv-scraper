from collections.abc import Iterator
from typing import Any
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
import requests

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.market_data.markets import Markets


@pytest.fixture
def markets() -> Iterator[Markets]:
    """Create a Markets instance for testing."""
    yield Markets()


def _mock_response(data: dict[str, Any], status_code: int = 200) -> MagicMock:
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


# ---------------------------------------------------------------------------
# Sample API data
# ---------------------------------------------------------------------------
SAMPLE_API_RESPONSE: dict[str, Any] = {
    "data": [
        {
            "s": "NASDAQ:AAPL",
            "d": [
                "AAPL",
                150.25,
                2.5,
                3.75,
                50000000,
                0.8,
                2500000000000,
                25.5,
                6.0,
                "Technology",
                "Consumer Electronics",
            ],
        },
        {
            "s": "NASDAQ:MSFT",
            "d": [
                "MSFT",
                380.00,
                1.8,
                6.80,
                30000000,
                0.7,
                2800000000000,
                30.0,
                12.5,
                "Technology",
                "Software",
            ],
        },
    ],
    "totalCount": 5000,
}


class TestInheritance:
    """Verify Markets inherits from BaseScraper."""

    def test_inherits_base_scraper(self) -> None:
        """Markets must be a subclass of BaseScraper."""
        assert issubclass(Markets, BaseScraper)


class TestGetTopStocksSuccess:
    """Tests for successful get_data calls."""

    @patch("requests.post")
    def test_get_data_success(self, mock_post: MagicMock, markets: Markets) -> None:
        """Default params return success envelope with mapped data."""
        mock_post.return_value = _mock_response(SAMPLE_API_RESPONSE)
        result = markets.get_markets()

        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 2

        # Each row should have 'symbol' plus the default field names
        first = result["data"][0]
        assert first["symbol"] == "NASDAQ:AAPL"
        assert first["name"] == "AAPL"
        assert first["close"] == 150.25
        assert first["market_cap_basic"] == 2500000000000

        # Metadata
        assert result["metadata"]["market"] == "america"
        assert result["metadata"]["sort_by"] == "market_cap"
        assert result["metadata"]["total"] == 2
        assert result["metadata"]["total_count"] == 5000
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_get_data_custom_fields(
        self, mock_post: MagicMock, markets: Markets
    ) -> None:
        """Custom fields list is sent in the request and mapped correctly."""
        custom_fields = ["name", "close", "volume"]
        api_resp: dict[str, Any] = {
            "data": [
                {"s": "NYSE:GE", "d": ["GE", 120.0, 8000000]},
            ],
            "totalCount": 100,
        }
        mock_post.return_value = _mock_response(api_resp)

        result = markets.get_markets(fields=custom_fields)

        assert result["status"] == STATUS_SUCCESS
        assert result["data"][0]["name"] == "GE"
        assert result["data"][0]["close"] == 120.0
        assert result["data"][0]["volume"] == 8000000

        # Verify the request body used custom fields
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["columns"] == custom_fields

    @patch("requests.post")
    def test_get_data_custom_sort(self, mock_post: MagicMock, markets: Markets) -> None:
        """sort_by parameter maps to the correct scanner sort field."""
        mock_post.return_value = _mock_response(SAMPLE_API_RESPONSE)

        result = markets.get_markets(sort_by="volume")

        assert result["status"] == STATUS_SUCCESS
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["sort"]["sortBy"] == "volume"

    @patch("requests.post")
    def test_get_data_sort_order(self, mock_post: MagicMock, markets: Markets) -> None:
        """sort_order parameter (asc/desc) is forwarded to API."""
        mock_post.return_value = _mock_response(SAMPLE_API_RESPONSE)

        result = markets.get_markets(sort_order="asc")

        assert result["status"] == STATUS_SUCCESS
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["sort"]["sortOrder"] == "asc"

    @patch("requests.post")
    def test_get_data_with_limit(self, mock_post: MagicMock, markets: Markets) -> None:
        """limit param is used in the range field of the payload."""
        mock_post.return_value = _mock_response(SAMPLE_API_RESPONSE)

        result = markets.get_markets(limit=10)

        assert result["status"] == STATUS_SUCCESS
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["range"] == [0, 10]


class TestGetTopStocksErrors:
    """Tests for error handling — returns error responses, never raises."""

    def test_get_data_invalid_market(self, markets: Markets) -> None:
        """Invalid market returns error response, does not raise."""
        result = markets.get_markets(market="narnia")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "market" in result["error"].lower()

    def test_get_data_invalid_sort_by(self, markets: Markets) -> None:
        """Invalid sort_by returns error response, does not raise."""
        result = markets.get_markets(sort_by="invalid_sort")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "sort" in result["error"].lower()

    @patch("requests.post")
    def test_get_data_network_error(
        self, mock_post: MagicMock, markets: Markets
    ) -> None:
        """Network error returns error response, does not raise."""
        mock_post.side_effect = requests.RequestException("Connection refused")
        result = markets.get_markets()

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Connection refused" in result["error"]


class TestResponseFormat:
    """Tests for response envelope structure."""

    @patch("requests.post")
    def test_response_has_standard_envelope(
        self, mock_post: MagicMock, markets: Markets
    ) -> None:
        """Success response contains exactly status/data/metadata/error keys."""
        mock_post.return_value = _mock_response(SAMPLE_API_RESPONSE)
        result = markets.get_markets()

        assert set(result.keys()) == {"status", "data", "metadata", "error"}

    def test_error_response_has_standard_envelope(self, markets: Markets) -> None:
        """Error response also has standard envelope keys."""
        result = markets.get_markets(market="invalid")
        assert set(result.keys()) == {"status", "data", "metadata", "error"}


class TestUsesMapScannerRows:
    """Verify Markets delegates row mapping to BaseScraper._map_scanner_rows."""

    @patch("requests.post")
    def test_uses_map_scanner_rows(
        self, mock_post: MagicMock, markets: Markets
    ) -> None:
        """get_data must call _map_scanner_rows for data mapping."""
        mock_post.return_value = _mock_response(SAMPLE_API_RESPONSE)
        with mock.patch.object(
            markets, "_map_scanner_rows", wraps=markets._map_scanner_rows
        ) as spy:
            result = markets.get_markets()

        spy.assert_called_once()
        assert result["status"] == STATUS_SUCCESS
