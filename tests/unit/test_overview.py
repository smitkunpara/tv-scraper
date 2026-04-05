from collections.abc import Iterator
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
import requests

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.market_data.overview import Overview


@pytest.fixture
def overview() -> Iterator[Overview]:
    """Create an Overview instance for testing."""
    yield Overview()


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


class TestOverviewInheritance:
    """Verify Overview inherits from BaseScraper."""

    def test_inherits_base_scraper(self) -> None:
        """Overview must be a subclass of BaseScraper."""
        assert issubclass(Overview, BaseScraper)


class TestGetOverviewSuccess:
    """Tests for successful overview retrieval."""

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("requests.get")
    def test_get_data_success(
        self, mock_get: MagicMock, mock_verify: MagicMock, overview: Overview
    ) -> None:
        """Get overview with default (all) fields returns success envelope."""
        mock_verify.return_value = True
        # Flat mock response as returned by GET /symbol endpoint
        mock_data = {
            "name": "AAPL",
            "close": 150.25,
            "market_cap_basic": 2500000000000,
        }
        mock_get.return_value = _mock_response(mock_data)

        result = overview.get_overview(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None
        assert result["error"] is None
        assert result["data"]["symbol"] == "NASDAQ:AAPL"
        assert result["data"]["name"] == "AAPL"
        assert result["data"]["close"] == 150.25
        mock_get.assert_called_once()

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("requests.get")
    def test_get_data_with_custom_fields(
        self, mock_get: MagicMock, mock_verify: MagicMock, overview: Overview
    ) -> None:
        """Custom fields are sent to the API and returned correctly."""
        mock_verify.return_value = True
        custom_fields = ["close", "volume", "market_cap_basic"]
        mock_data = {
            "close": 150.25,
            "volume": 1000000,
            "market_cap_basic": 2500000000000,
        }
        mock_get.return_value = _mock_response(mock_data)

        result = overview.get_overview(
            exchange="NASDAQ", symbol="AAPL", fields=custom_fields
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"]["close"] == 150.25
        assert result["data"]["volume"] == 1000000
        assert result["data"]["market_cap_basic"] == 2500000000000

        # Verify correct params sent to API
        call_kwargs = mock_get.call_args[1]
        params = call_kwargs["params"]
        assert params["symbol"] == "NASDAQ:AAPL"
        assert params["fields"] == ",".join(custom_fields)


class TestGetOverviewErrors:
    """Tests for error handling — returns error responses, never raises."""

    def test_get_data_invalid_exchange(self, overview: Overview) -> None:
        """Invalid exchange returns error response, does not raise."""
        result = overview.get_overview(exchange="INVALID_EXCHANGE", symbol="AAPL")
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Invalid exchange" in result["error"]

    def test_get_data_empty_symbol(self, overview: Overview) -> None:
        """Empty symbol returns error response."""
        result = overview.get_overview(exchange="NASDAQ", symbol="")
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    @patch("requests.get")
    def test_get_data_network_error(
        self, mock_get: MagicMock, overview: Overview
    ) -> None:
        """Network error returns error response, does not raise."""
        mock_get.side_effect = requests.RequestException("Connection refused")

        result = overview.get_overview(exchange="NASDAQ", symbol="AAPL")
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Connection refused" in result["error"]

    def test_get_data_empty_fields_list(self, overview: Overview) -> None:
        """Empty fields list returns error response."""
        result = overview.get_overview(exchange="NASDAQ", symbol="AAPL", fields=[])
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "fields" in result["error"].lower()


class TestCategoryMethods:
    """Tests for convenience category methods."""

    def test_get_profile_returns_profile_fields(self, overview: Overview) -> None:
        """get_profile passes BASIC_FIELDS to get_data."""
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

    @patch("requests.get")
    def test_response_has_standard_envelope(
        self, mock_get: MagicMock, overview: Overview
    ) -> None:
        """Response contains exactly status/data/metadata/error keys."""
        mock_data = {"close": 150.25}
        mock_get.return_value = _mock_response(mock_data)
        result = overview.get_overview(
            exchange="NASDAQ", symbol="AAPL", fields=["close"]
        )
        assert set(result.keys()) == {"status", "data", "metadata", "error"}
        assert result["metadata"]["exchange"] == "NASDAQ"
        assert result["metadata"]["symbol"] == "AAPL"

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("requests.get")
    def test_combines_exchange_symbol_for_api(
        self, mock_get: MagicMock, mock_verify: MagicMock, overview: Overview
    ) -> None:
        """Verify EXCHANGE:SYMBOL is combined internally for the API call."""
        mock_verify.return_value = True
        mock_data = {"close": 150.25}
        mock_get.return_value = _mock_response(mock_data)
        overview.get_overview(exchange="NASDAQ", symbol="AAPL", fields=["close"])

        call_kwargs = mock_get.call_args[1]
        params = call_kwargs["params"]
        assert params["symbol"] == "NASDAQ:AAPL"
