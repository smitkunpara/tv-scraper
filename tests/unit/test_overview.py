"""Tests for Overview scraper module."""

from collections.abc import Iterator
from unittest import mock
from unittest.mock import MagicMock

import pytest

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.core.exceptions import NetworkError
from tv_scraper.scrapers.market_data.overview import Overview


@pytest.fixture
def overview() -> Iterator[Overview]:
    """Create an Overview instance for testing."""
    yield Overview()


def _mock_response(data: dict) -> MagicMock:
    """Create a mock requests.Response with a .json() method."""
    response = MagicMock()
    response.json.return_value = data
    response.status_code = 200
    return response


class TestOverviewInheritance:
    """Verify Overview inherits from BaseScraper."""

    def test_inherits_base_scraper(self) -> None:
        """Overview must be a subclass of BaseScraper."""
        assert issubclass(Overview, BaseScraper)


class TestGetOverviewSuccess:
    """Tests for successful overview retrieval."""

    def test_get_overview_success(self, overview: Overview) -> None:
        """Get overview with default (all) fields returns success envelope."""
        # Flat mock response as returned by GET /symbol endpoint
        mock_data = {
            "name": "AAPL",
            "close": 150.25,
            "market_cap_basic": 2500000000000,
        }
        mock_resp = _mock_response(mock_data)

        with mock.patch.object(overview, "_make_request", return_value=mock_resp):
            result = overview.get_overview(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None
        assert result["error"] is None
        assert result["data"]["symbol"] == "NASDAQ:AAPL"
        assert result["data"]["name"] == "AAPL"
        assert result["data"]["close"] == 150.25

    def test_get_overview_with_custom_fields(self, overview: Overview) -> None:
        """Custom fields are sent to the API and returned correctly."""
        custom_fields = ["close", "volume", "market_cap_basic"]
        mock_data = {
            "close": 150.25,
            "volume": 1000000,
            "market_cap_basic": 2500000000000,
        }
        mock_resp = _mock_response(mock_data)

        with mock.patch.object(
            overview, "_make_request", return_value=mock_resp
        ) as mock_req:
            result = overview.get_overview(
                exchange="NASDAQ", symbol="AAPL", fields=custom_fields
            )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"]["close"] == 150.25
        assert result["data"]["volume"] == 1000000
        assert result["data"]["market_cap_basic"] == 2500000000000

        # Verify correct params sent to API (GET uses params, not json_data)
        call_kwargs = mock_req.call_args[1]
        params = call_kwargs["params"]
        assert params["symbol"] == "NASDAQ:AAPL"
        assert params["fields"] == ",".join(custom_fields)


class TestGetOverviewErrors:
    """Tests for error handling — returns error responses, never raises."""

    def test_get_overview_invalid_exchange(self, overview: Overview) -> None:
        """Invalid exchange returns error response, does not raise."""
        result = overview.get_overview(exchange="INVALID_EXCHANGE", symbol="AAPL")
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Invalid exchange" in result["error"]

    def test_get_overview_empty_symbol(self, overview: Overview) -> None:
        """Empty symbol returns error response."""
        result = overview.get_overview(exchange="NASDAQ", symbol="")
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    def test_get_overview_network_error(self, overview: Overview) -> None:
        """Network error returns error response, does not raise."""
        with mock.patch.object(
            overview,
            "_make_request",
            side_effect=NetworkError("Connection refused"),
        ):
            result = overview.get_overview(exchange="NASDAQ", symbol="AAPL")
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Connection refused" in result["error"]


class TestCategoryMethods:
    """Tests for convenience category methods."""

    def test_get_profile_returns_profile_fields(self, overview: Overview) -> None:
        """get_profile passes BASIC_FIELDS to get_overview."""
        with mock.patch.object(overview, "get_overview") as mock_get:
            mock_get.return_value = overview._success_response(
                {"name": "AAPL"}, exchange="NASDAQ", symbol="AAPL"
            )
            result = overview.get_profile(exchange="NASDAQ", symbol="AAPL")

        mock_get.assert_called_once_with(
            exchange="NASDAQ", symbol="AAPL", fields=Overview.BASIC_FIELDS
        )
        assert result["status"] == STATUS_SUCCESS

    def test_get_statistics_returns_stats_fields(self, overview: Overview) -> None:
        """get_statistics passes correct combined fields."""
        expected_fields = (
            Overview.MARKET_FIELDS
            + Overview.VALUATION_FIELDS
            + Overview.DIVIDEND_FIELDS
        )
        with mock.patch.object(overview, "get_overview") as mock_get:
            mock_get.return_value = overview._success_response(
                {"market_cap_basic": 2500000000000},
                exchange="NASDAQ",
                symbol="AAPL",
            )
            result = overview.get_statistics(exchange="NASDAQ", symbol="AAPL")

        mock_get.assert_called_once_with(
            exchange="NASDAQ", symbol="AAPL", fields=expected_fields
        )
        assert result["status"] == STATUS_SUCCESS

    def test_get_financials_returns_financial_fields(self, overview: Overview) -> None:
        """get_financials passes FINANCIAL_FIELDS."""
        with mock.patch.object(overview, "get_overview") as mock_get:
            mock_get.return_value = overview._success_response(
                {"total_revenue": 400000000000},
                exchange="NASDAQ",
                symbol="AAPL",
            )
            result = overview.get_financials(exchange="NASDAQ", symbol="AAPL")

        mock_get.assert_called_once_with(
            exchange="NASDAQ", symbol="AAPL", fields=Overview.FINANCIAL_FIELDS
        )
        assert result["status"] == STATUS_SUCCESS

    def test_get_performance_returns_performance_fields(
        self, overview: Overview
    ) -> None:
        """get_performance passes PERFORMANCE_FIELDS."""
        with mock.patch.object(overview, "get_overview") as mock_get:
            mock_get.return_value = overview._success_response(
                {"Perf.W": 1.5}, exchange="NASDAQ", symbol="AAPL"
            )
            result = overview.get_performance(exchange="NASDAQ", symbol="AAPL")

        mock_get.assert_called_once_with(
            exchange="NASDAQ", symbol="AAPL", fields=Overview.PERFORMANCE_FIELDS
        )
        assert result["status"] == STATUS_SUCCESS

    def test_get_technicals_returns_technical_fields(self, overview: Overview) -> None:
        """get_technicals passes TECHNICAL_FIELDS + VOLATILITY_FIELDS."""
        expected_fields = Overview.TECHNICAL_FIELDS + Overview.VOLATILITY_FIELDS
        with mock.patch.object(overview, "get_overview") as mock_get:
            mock_get.return_value = overview._success_response(
                {"RSI": 55.0}, exchange="NASDAQ", symbol="AAPL"
            )
            result = overview.get_technicals(exchange="NASDAQ", symbol="AAPL")

        mock_get.assert_called_once_with(
            exchange="NASDAQ", symbol="AAPL", fields=expected_fields
        )
        assert result["status"] == STATUS_SUCCESS


class TestResponseFormat:
    """Tests for response envelope structure."""

    def test_response_has_standard_envelope(self, overview: Overview) -> None:
        """Response contains exactly status/data/metadata/error keys."""
        mock_data = {"close": 150.25}
        mock_resp = _mock_response(mock_data)
        with mock.patch.object(overview, "_make_request", return_value=mock_resp):
            result = overview.get_overview(
                exchange="NASDAQ", symbol="AAPL", fields=["close"]
            )
        assert set(result.keys()) == {"status", "data", "metadata", "error"}
        assert result["metadata"]["exchange"] == "NASDAQ"
        assert result["metadata"]["symbol"] == "AAPL"

    def test_combines_exchange_symbol_for_api(self, overview: Overview) -> None:
        """Verify EXCHANGE:SYMBOL is combined internally for the API call."""
        mock_data = {"close": 150.25}
        mock_resp = _mock_response(mock_data)
        with mock.patch.object(
            overview, "_make_request", return_value=mock_resp
        ) as mock_req:
            overview.get_overview(exchange="NASDAQ", symbol="AAPL", fields=["close"])

        call_kwargs = mock_req.call_args[1]
        params = call_kwargs["params"]
        assert params["symbol"] == "NASDAQ:AAPL"
