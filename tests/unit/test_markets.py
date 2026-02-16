"""Tests for Markets scraper module."""

from typing import Any, Dict, Iterator, List
from unittest import mock
from unittest.mock import MagicMock

import pytest

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.core.exceptions import NetworkError
from tv_scraper.scrapers.market_data.markets import Markets


@pytest.fixture
def markets() -> Iterator[Markets]:
    """Create a Markets instance for testing."""
    yield Markets()


def _mock_response(data: Dict[str, Any]) -> MagicMock:
    """Create a mock requests.Response with a .json() method."""
    response = MagicMock()
    response.json.return_value = data
    response.status_code = 200
    return response


# ---------------------------------------------------------------------------
# Sample API data
# ---------------------------------------------------------------------------
SAMPLE_API_RESPONSE: Dict[str, Any] = {
    "data": [
        {
            "s": "NASDAQ:AAPL",
            "d": [
                "AAPL", 150.25, 2.5, 3.75, 50000000,
                0.8, 2500000000000, 25.5, 6.0, "Technology",
                "Consumer Electronics",
            ],
        },
        {
            "s": "NASDAQ:MSFT",
            "d": [
                "MSFT", 380.00, 1.8, 6.80, 30000000,
                0.7, 2800000000000, 30.0, 12.5, "Technology",
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
    """Tests for successful get_top_stocks calls."""

    def test_get_top_stocks_success(self, markets: Markets) -> None:
        """Default params return success envelope with mapped data."""
        mock_resp = _mock_response(SAMPLE_API_RESPONSE)
        with mock.patch.object(markets, "_make_request", return_value=mock_resp):
            result = markets.get_top_stocks()

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

    def test_get_top_stocks_custom_fields(self, markets: Markets) -> None:
        """Custom fields list is sent in the request and mapped correctly."""
        custom_fields = ["name", "close", "volume"]
        api_resp: Dict[str, Any] = {
            "data": [
                {"s": "NYSE:GE", "d": ["GE", 120.0, 8000000]},
            ],
            "totalCount": 100,
        }
        mock_resp = _mock_response(api_resp)

        with mock.patch.object(
            markets, "_make_request", return_value=mock_resp
        ) as mock_req:
            result = markets.get_top_stocks(fields=custom_fields)

        assert result["status"] == STATUS_SUCCESS
        assert result["data"][0]["name"] == "GE"
        assert result["data"][0]["close"] == 120.0
        assert result["data"][0]["volume"] == 8000000

        # Verify the request body used custom fields
        call_kwargs = mock_req.call_args[1]
        payload = call_kwargs["json_data"]
        assert payload["columns"] == custom_fields

    def test_get_top_stocks_custom_sort(self, markets: Markets) -> None:
        """sort_by parameter maps to the correct scanner sort field."""
        mock_resp = _mock_response(SAMPLE_API_RESPONSE)

        with mock.patch.object(
            markets, "_make_request", return_value=mock_resp
        ) as mock_req:
            result = markets.get_top_stocks(sort_by="volume")

        assert result["status"] == STATUS_SUCCESS
        call_kwargs = mock_req.call_args[1]
        payload = call_kwargs["json_data"]
        assert payload["sort"]["sortBy"] == "volume"

    def test_get_top_stocks_sort_order(self, markets: Markets) -> None:
        """sort_order parameter (asc/desc) is forwarded to API."""
        mock_resp = _mock_response(SAMPLE_API_RESPONSE)

        with mock.patch.object(
            markets, "_make_request", return_value=mock_resp
        ) as mock_req:
            result = markets.get_top_stocks(sort_order="asc")

        assert result["status"] == STATUS_SUCCESS
        call_kwargs = mock_req.call_args[1]
        payload = call_kwargs["json_data"]
        assert payload["sort"]["sortOrder"] == "asc"

    def test_get_top_stocks_with_limit(self, markets: Markets) -> None:
        """limit param is used in the range field of the payload."""
        mock_resp = _mock_response(SAMPLE_API_RESPONSE)

        with mock.patch.object(
            markets, "_make_request", return_value=mock_resp
        ) as mock_req:
            result = markets.get_top_stocks(limit=10)

        assert result["status"] == STATUS_SUCCESS
        call_kwargs = mock_req.call_args[1]
        payload = call_kwargs["json_data"]
        assert payload["range"] == [0, 10]


class TestGetTopStocksErrors:
    """Tests for error handling — returns error responses, never raises."""

    def test_get_top_stocks_invalid_market(self, markets: Markets) -> None:
        """Invalid market returns error response, does not raise."""
        result = markets.get_top_stocks(market="narnia")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "market" in result["error"].lower()

    def test_get_top_stocks_invalid_sort_by(self, markets: Markets) -> None:
        """Invalid sort_by returns error response, does not raise."""
        result = markets.get_top_stocks(sort_by="invalid_sort")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "sort" in result["error"].lower()

    def test_get_top_stocks_network_error(self, markets: Markets) -> None:
        """Network error returns error response, does not raise."""
        with mock.patch.object(
            markets,
            "_make_request",
            side_effect=NetworkError("Connection refused"),
        ):
            result = markets.get_top_stocks()

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Connection refused" in result["error"]


class TestResponseFormat:
    """Tests for response envelope structure."""

    def test_response_has_standard_envelope(self, markets: Markets) -> None:
        """Success response contains exactly status/data/metadata/error keys."""
        mock_resp = _mock_response(SAMPLE_API_RESPONSE)
        with mock.patch.object(markets, "_make_request", return_value=mock_resp):
            result = markets.get_top_stocks()

        assert set(result.keys()) == {"status", "data", "metadata", "error"}

    def test_error_response_has_standard_envelope(self, markets: Markets) -> None:
        """Error response also has standard envelope keys."""
        result = markets.get_top_stocks(market="invalid")
        assert set(result.keys()) == {"status", "data", "metadata", "error"}


class TestUsesMapScannerRows:
    """Verify Markets delegates row mapping to BaseScraper._map_scanner_rows."""

    def test_uses_map_scanner_rows(self, markets: Markets) -> None:
        """get_top_stocks must call _map_scanner_rows for data mapping."""
        mock_resp = _mock_response(SAMPLE_API_RESPONSE)
        with mock.patch.object(markets, "_make_request", return_value=mock_resp), \
             mock.patch.object(
                 markets, "_map_scanner_rows", wraps=markets._map_scanner_rows
             ) as spy:
            result = markets.get_top_stocks()

        spy.assert_called_once()
        assert result["status"] == STATUS_SUCCESS
