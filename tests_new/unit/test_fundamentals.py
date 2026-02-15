"""Tests for Fundamentals scraper module."""

from typing import Any, Dict, Iterator, List
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


def _mock_response(data: Dict[str, Any]) -> MagicMock:
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
        mock_values: List[Any] = [
            394000000000,  # total_revenue
            26.5,          # revenue_per_share_ttm
            390000000000,  # total_revenue_fy
            170000000000,  # gross_profit
            168000000000,  # gross_profit_fy
            120000000000,  # operating_income
            118000000000,  # operating_income_fy
            100000000000,  # net_income
            99000000000,   # net_income_fy
            130000000000,  # EBITDA
            6.5,           # basic_eps_net_income
            6.3,           # earnings_per_share_basic_ttm
            6.2,           # earnings_per_share_diluted_ttm
            # balance sheet
            350000000000,  # total_assets
            345000000000,  # total_assets_fy
            60000000000,   # cash_n_short_term_invest
            58000000000,   # cash_n_short_term_invest_fy
            120000000000,  # total_debt
            118000000000,  # total_debt_fy
            50000000000,   # stockholders_equity
            48000000000,   # stockholders_equity_fy
            3.5,           # book_value_per_share_fq
            # cash flow
            110000000000,  # cash_f_operating_activities
            108000000000,  # cash_f_operating_activities_fy
            -20000000000,  # cash_f_investing_activities
            -18000000000,  # cash_f_investing_activities_fy
            -90000000000,  # cash_f_financing_activities
            -88000000000,  # cash_f_financing_activities_fy
            85000000000,   # free_cash_flow
            # margins
            43.0,          # gross_margin
            43.5,          # gross_margin_percent_ttm
            30.0,          # operating_margin
            30.5,          # operating_margin_ttm
            28.0,          # pretax_margin_percent_ttm
            25.0,          # net_margin
            25.5,          # net_margin_percent_ttm
            33.0,          # EBITDA_margin
            # profitability
            150.0,         # return_on_equity
            145.0,         # return_on_equity_fq
            30.0,          # return_on_assets
            28.0,          # return_on_assets_fq
            35.0,          # return_on_investment_ttm
            # liquidity
            1.1,           # current_ratio
            1.0,           # current_ratio_fq
            0.9,           # quick_ratio
            0.85,          # quick_ratio_fq
            # leverage
            2.4,           # debt_to_equity
            2.3,           # debt_to_equity_fq
            0.35,          # debt_to_assets
            # valuation
            2800000000000, # market_cap_basic
            2850000000000, # market_cap_calc
            2900000000000, # market_cap_diluted_calc
            2700000000000, # enterprise_value_fq
            28.5,          # price_earnings_ttm
            45.0,          # price_book_fq
            7.5,           # price_sales_ttm
            25.0,          # price_free_cash_flow_ttm
            # dividends
            0.65,          # dividends_yield
            0.24,          # dividends_per_share_fq
            15.0,          # dividend_payout_ratio_ttm
        ]
        mock_resp = _mock_response({
            "data": [{"s": "NASDAQ:AAPL", "d": mock_values}],
        })
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
        mock_resp = _mock_response({
            "data": [{"s": "NASDAQ:AAPL", "d": [394000000000, 100000000000, 130000000000]}],
        })
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

        # Verify correct fields sent to API
        call_kwargs = mock_req.call_args[1]
        json_body = call_kwargs["json_data"]
        assert json_body["columns"] == custom_fields


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

    def test_get_fundamentals_empty_symbol(
        self, fundamentals: Fundamentals
    ) -> None:
        """Empty symbol returns error response."""
        result = fundamentals.get_fundamentals(exchange="NASDAQ", symbol="")
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    def test_get_fundamentals_network_error(
        self, fundamentals: Fundamentals
    ) -> None:
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

    def test_compare_fundamentals_success(
        self, fundamentals: Fundamentals
    ) -> None:
        """compare_fundamentals with valid symbols returns comparison data."""
        symbols: List[Dict[str, str]] = [
            {"exchange": "NASDAQ", "symbol": "AAPL"},
            {"exchange": "NASDAQ", "symbol": "MSFT"},
        ]
        custom_fields = ["total_revenue", "net_income", "market_cap_basic"]

        # First call for AAPL, second call for MSFT
        aapl_resp = _mock_response({
            "data": [{"s": "NASDAQ:AAPL", "d": [394000000000, 100000000000, 2800000000000]}],
        })
        msft_resp = _mock_response({
            "data": [{"s": "NASDAQ:MSFT", "d": [200000000000, 70000000000, 2400000000000]}],
        })

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

    def test_compare_fundamentals_empty_list(
        self, fundamentals: Fundamentals
    ) -> None:
        """Empty symbols list returns error response."""
        result = fundamentals.compare_fundamentals(symbols=[], fields=["total_revenue"])
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None


class TestResponseFormat:
    """Tests for response envelope structure."""

    def test_response_has_standard_envelope(
        self, fundamentals: Fundamentals
    ) -> None:
        """Response contains exactly status/data/metadata/error keys."""
        mock_resp = _mock_response({
            "data": [{"s": "NASDAQ:AAPL", "d": [394000000000]}],
        })
        with mock.patch.object(fundamentals, "_make_request", return_value=mock_resp):
            result = fundamentals.get_fundamentals(
                exchange="NASDAQ", symbol="AAPL", fields=["total_revenue"]
            )
        assert set(result.keys()) == {"status", "data", "metadata", "error"}
        assert result["metadata"]["exchange"] == "NASDAQ"
        assert result["metadata"]["symbol"] == "AAPL"
