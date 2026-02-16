"""Tests for Fundamentals scraper module."""

from collections.abc import Iterator
from typing import Any
from unittest import mock
from unittest.mock import MagicMock

import pytest

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.core.exceptions import NetworkError
from tv_scraper.scrapers.market_data.fundamentals import Fundamentals


@pytest.fixture
def fundamentals() -> Iterator[Fundamentals]:
    """Create a Fundamentals instance for testing."""
    yield Fundamentals()


def _mock_response(data: dict[str, Any]) -> MagicMock:
    """Create a mock requests.Response with a .json() method."""
    response = MagicMock()
    response.json.return_value = data
    response.status_code = 200
    return response


class TestInheritance:
    """Verify Fundamentals inherits from BaseScraper."""

    def test_inherits_base_scraper(self) -> None:
        """Fundamentals must be a subclass of BaseScraper."""
        assert issubclass(Fundamentals, BaseScraper)


class TestGetFundamentalsSuccess:
    """Tests for successful fundamentals retrieval."""

    def test_get_fundamentals_success(self, fundamentals: Fundamentals) -> None:
        """Get fundamentals with default (all) fields returns success envelope."""
        # Flat mock response as returned by GET /symbol endpoint
        mock_data: dict[str, Any] = {
            "total_revenue": 394000000000,
            "EBITDA": 130000000000,
            "market_cap_basic": 2800000000000,
        }
        mock_resp = _mock_response(mock_data)

        with mock.patch.object(fundamentals, "_make_request", return_value=mock_resp):
            result = fundamentals.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None
        assert result["error"] is None
        assert result["data"]["symbol"] == "NASDAQ:AAPL"
        assert result["data"]["total_revenue"] == 394000000000
        assert result["data"]["EBITDA"] == 130000000000

    def test_get_fundamentals_with_custom_fields(
        self, fundamentals: Fundamentals
    ) -> None:
        """Custom fields are sent to the API and returned correctly."""
        custom_fields = ["total_revenue", "net_income", "EBITDA"]
        mock_data: dict[str, Any] = {
            "total_revenue": 394000000000,
            "net_income": 100000000000,
            "EBITDA": 130000000000,
        }
        mock_resp = _mock_response(mock_data)

        with mock.patch.object(
            fundamentals, "_make_request", return_value=mock_resp
        ) as mock_req:
            result = fundamentals.get_fundamentals(
                exchange="NASDAQ", symbol="AAPL", fields=custom_fields
            )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"]["total_revenue"] == 394000000000
        assert result["data"]["net_income"] == 100000000000
        assert result["data"]["EBITDA"] == 130000000000

        # Verify correct params sent to API (GET uses params, not json_data)
        call_kwargs = mock_req.call_args[1]
        params = call_kwargs["params"]
        assert params["symbol"] == "NASDAQ:AAPL"
        assert params["fields"] == ",".join(custom_fields)


class TestGetFundamentalsErrors:
    """Tests for error handling — returns error responses, never raises."""

    def test_get_fundamentals_invalid_exchange(
        self, fundamentals: Fundamentals
    ) -> None:
        """Invalid exchange returns error response, does not raise."""
        result = fundamentals.get_fundamentals(
            exchange="INVALID_EXCHANGE", symbol="AAPL"
        )
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Invalid exchange" in result["error"]

    def test_get_fundamentals_empty_symbol(self, fundamentals: Fundamentals) -> None:
        """Empty symbol returns error response."""
        result = fundamentals.get_fundamentals(exchange="NASDAQ", symbol="")
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    def test_get_fundamentals_network_error(self, fundamentals: Fundamentals) -> None:
        """Network error returns error response, does not raise."""
        with mock.patch.object(
            fundamentals,
            "_make_request",
            side_effect=NetworkError("Connection refused"),
        ):
            result = fundamentals.get_fundamentals(exchange="NASDAQ", symbol="AAPL")
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Connection refused" in result["error"]


class TestCategoryMethods:
    """Tests for convenience category methods."""

    def test_get_income_statement(self, fundamentals: Fundamentals) -> None:
        """get_income_statement passes INCOME_STATEMENT_FIELDS."""
        with mock.patch.object(fundamentals, "get_fundamentals") as mock_get:
            mock_get.return_value = fundamentals._success_response(
                {"total_revenue": 394000000000},
                exchange="NASDAQ",
                symbol="AAPL",
            )
            result = fundamentals.get_income_statement(exchange="NASDAQ", symbol="AAPL")

        mock_get.assert_called_once_with(
            exchange="NASDAQ",
            symbol="AAPL",
            fields=Fundamentals.INCOME_STATEMENT_FIELDS,
        )
        assert result["status"] == STATUS_SUCCESS

    def test_get_balance_sheet(self, fundamentals: Fundamentals) -> None:
        """get_balance_sheet passes BALANCE_SHEET_FIELDS."""
        with mock.patch.object(fundamentals, "get_fundamentals") as mock_get:
            mock_get.return_value = fundamentals._success_response(
                {"total_assets": 350000000000},
                exchange="NASDAQ",
                symbol="AAPL",
            )
            result = fundamentals.get_balance_sheet(exchange="NASDAQ", symbol="AAPL")

        mock_get.assert_called_once_with(
            exchange="NASDAQ",
            symbol="AAPL",
            fields=Fundamentals.BALANCE_SHEET_FIELDS,
        )
        assert result["status"] == STATUS_SUCCESS

    def test_get_cash_flow(self, fundamentals: Fundamentals) -> None:
        """get_cash_flow passes CASH_FLOW_FIELDS."""
        with mock.patch.object(fundamentals, "get_fundamentals") as mock_get:
            mock_get.return_value = fundamentals._success_response(
                {"free_cash_flow": 85000000000},
                exchange="NASDAQ",
                symbol="AAPL",
            )
            result = fundamentals.get_cash_flow(exchange="NASDAQ", symbol="AAPL")

        mock_get.assert_called_once_with(
            exchange="NASDAQ",
            symbol="AAPL",
            fields=Fundamentals.CASH_FLOW_FIELDS,
        )
        assert result["status"] == STATUS_SUCCESS

    def test_get_statistics(self, fundamentals: Fundamentals) -> None:
        """get_statistics passes combined liquidity + leverage + valuation fields."""
        expected_fields = (
            Fundamentals.LIQUIDITY_FIELDS
            + Fundamentals.LEVERAGE_FIELDS
            + Fundamentals.VALUATION_FIELDS
        )
        with mock.patch.object(fundamentals, "get_fundamentals") as mock_get:
            mock_get.return_value = fundamentals._success_response(
                {"current_ratio": 1.1},
                exchange="NASDAQ",
                symbol="AAPL",
            )
            result = fundamentals.get_statistics(exchange="NASDAQ", symbol="AAPL")

        mock_get.assert_called_once_with(
            exchange="NASDAQ",
            symbol="AAPL",
            fields=expected_fields,
        )
        assert result["status"] == STATUS_SUCCESS

    def test_get_dividends(self, fundamentals: Fundamentals) -> None:
        """get_dividends passes DIVIDEND_FIELDS."""
        with mock.patch.object(fundamentals, "get_fundamentals") as mock_get:
            mock_get.return_value = fundamentals._success_response(
                {"dividends_yield": 0.65},
                exchange="NASDAQ",
                symbol="AAPL",
            )
            result = fundamentals.get_dividends(exchange="NASDAQ", symbol="AAPL")

        mock_get.assert_called_once_with(
            exchange="NASDAQ",
            symbol="AAPL",
            fields=Fundamentals.DIVIDEND_FIELDS,
        )
        assert result["status"] == STATUS_SUCCESS

    def test_get_profitability(self, fundamentals: Fundamentals) -> None:
        """get_profitability passes PROFITABILITY_FIELDS."""
        with mock.patch.object(fundamentals, "get_fundamentals") as mock_get:
            mock_get.return_value = fundamentals._success_response(
                {"return_on_equity": 150.0},
                exchange="NASDAQ",
                symbol="AAPL",
            )
            result = fundamentals.get_profitability(exchange="NASDAQ", symbol="AAPL")

        mock_get.assert_called_once_with(
            exchange="NASDAQ",
            symbol="AAPL",
            fields=Fundamentals.PROFITABILITY_FIELDS,
        )
        assert result["status"] == STATUS_SUCCESS

    def test_get_margins(self, fundamentals: Fundamentals) -> None:
        """get_margins passes MARGIN_FIELDS."""
        with mock.patch.object(fundamentals, "get_fundamentals") as mock_get:
            mock_get.return_value = fundamentals._success_response(
                {"gross_margin": 43.0},
                exchange="NASDAQ",
                symbol="AAPL",
            )
            result = fundamentals.get_margins(exchange="NASDAQ", symbol="AAPL")

        mock_get.assert_called_once_with(
            exchange="NASDAQ",
            symbol="AAPL",
            fields=Fundamentals.MARGIN_FIELDS,
        )
        assert result["status"] == STATUS_SUCCESS


class TestCompareFundamentals:
    """Tests for multi-symbol comparison."""

    def test_compare_fundamentals_success(self, fundamentals: Fundamentals) -> None:
        """compare_fundamentals with valid symbols returns comparison data."""
        symbols: list[dict[str, str]] = [
            {"exchange": "NASDAQ", "symbol": "AAPL"},
            {"exchange": "NASDAQ", "symbol": "MSFT"},
        ]
        custom_fields = ["total_revenue", "net_income", "market_cap_basic"]

        # Flat mock responses
        aapl_resp = _mock_response(
            {
                "total_revenue": 394000000000,
                "net_income": 100000000000,
                "market_cap_basic": 2800000000000,
            }
        )
        msft_resp = _mock_response(
            {
                "total_revenue": 200000000000,
                "net_income": 70000000000,
                "market_cap_basic": 2400000000000,
            }
        )

        with mock.patch.object(
            fundamentals, "_make_request", side_effect=[aapl_resp, msft_resp]
        ):
            result = fundamentals.compare_fundamentals(
                symbols=symbols, fields=custom_fields
            )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None
        assert result["error"] is None

        # Check comparison structure in data
        data = result["data"]
        assert "items" in data
        assert "comparison" in data
        assert len(data["items"]) == 2
        assert "total_revenue" in data["comparison"]

    def test_compare_fundamentals_empty_list(self, fundamentals: Fundamentals) -> None:
        """Empty symbols list returns error response."""
        result = fundamentals.compare_fundamentals(symbols=[], fields=["total_revenue"])
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None


class TestResponseFormat:
    """Tests for response envelope structure."""

    def test_response_has_standard_envelope(self, fundamentals: Fundamentals) -> None:
        """Response contains exactly status/data/metadata/error keys."""
        mock_resp = _mock_response({"total_revenue": 394000000000})
        with mock.patch.object(fundamentals, "_make_request", return_value=mock_resp):
            result = fundamentals.get_fundamentals(
                exchange="NASDAQ", symbol="AAPL", fields=["total_revenue"]
            )
        assert set(result.keys()) == {"status", "data", "metadata", "error"}
        assert result["metadata"]["exchange"] == "NASDAQ"
        assert result["metadata"]["symbol"] == "AAPL"
