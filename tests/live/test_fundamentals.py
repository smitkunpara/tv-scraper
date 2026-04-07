"""Live API tests for Fundamentals scraper.

Tests real HTTP connections to TradingView fundamentals endpoint.
"""

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.market_data.fundamentals import Fundamentals


@pytest.mark.live
class TestLiveFundamentals:
    """Test fundamentals with real API calls."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset validator singleton before each test."""

        yield

    def test_live_get_fundamentals_aapl_nasdaq(self) -> None:
        """Verify AAPL fundamentals from NASDAQ."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None
        assert result["metadata"]["exchange"] == "NASDAQ"
        assert result["metadata"]["symbol"] == "AAPL"

    def test_live_get_fundamentals_msft_nasdaq(self) -> None:
        """Verify MSFT fundamentals from NASDAQ."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(exchange="NASDAQ", symbol="MSFT")

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None
        assert result["metadata"]["symbol"] == "MSFT"

    def test_live_get_fundamentals_jpm_nyse(self) -> None:
        """Verify JPM fundamentals from NYSE."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(exchange="NYSE", symbol="JPM")

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None
        assert result["metadata"]["exchange"] == "NYSE"
        assert result["metadata"]["symbol"] == "JPM"

    def test_live_get_fundamentals_income_fields(self) -> None:
        """Verify income statement fields only."""
        scraper = Fundamentals()
        fields = ["total_revenue", "net_income", "gross_profit", "operating_income"]
        result = scraper.get_fundamentals(
            exchange="NASDAQ", symbol="AAPL", fields=fields
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None

    def test_live_get_fundamentals_valuation_fields(self) -> None:
        """Verify valuation fields only."""
        scraper = Fundamentals()
        fields = [
            "market_cap_basic",
            "price_earnings_ttm",
            "price_book_fq",
            "price_sales_ttm",
        ]
        result = scraper.get_fundamentals(
            exchange="NASDAQ", symbol="AAPL", fields=fields
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None

    def test_live_get_fundamentals_dividend_fields(self) -> None:
        """Verify dividend fields only."""
        scraper = Fundamentals()
        fields = [
            "dividends_yield",
            "dividends_per_share_fq",
            "dividend_payout_ratio_ttm",
        ]
        result = scraper.get_fundamentals(exchange="NYSE", symbol="JPM", fields=fields)

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None

    def test_live_get_fundamentals_margin_fields(self) -> None:
        """Verify margin fields only."""
        scraper = Fundamentals()
        fields = [
            "gross_margin",
            "operating_margin",
            "net_margin",
            "EBITDA_margin",
        ]
        result = scraper.get_fundamentals(
            exchange="NASDAQ", symbol="MSFT", fields=fields
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None

    def test_live_get_fundamentals_profitability_fields(self) -> None:
        """Verify profitability fields only."""
        scraper = Fundamentals()
        fields = [
            "return_on_equity",
            "return_on_equity_fq",
            "return_on_assets",
            "return_on_investment_ttm",
        ]
        result = scraper.get_fundamentals(
            exchange="NASDAQ", symbol="MSFT", fields=fields
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None

    def test_live_get_fundamentals_liquidity_fields(self) -> None:
        """Verify liquidity fields only."""
        scraper = Fundamentals()
        fields = ["current_ratio", "current_ratio_fq", "quick_ratio", "quick_ratio_fq"]
        result = scraper.get_fundamentals(exchange="NYSE", symbol="JPM", fields=fields)

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None

    def test_live_get_fundamentals_leverage_fields(self) -> None:
        """Verify leverage fields only."""
        scraper = Fundamentals()
        fields = ["debt_to_equity", "debt_to_equity_fq", "debt_to_assets"]
        result = scraper.get_fundamentals(exchange="NYSE", symbol="JPM", fields=fields)

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None

    def test_live_get_fundamentals_balance_sheet_fields(self) -> None:
        """Verify balance sheet fields only."""
        scraper = Fundamentals()
        fields = [
            "total_assets",
            "cash_n_short_term_invest",
            "total_debt",
            "stockholders_equity",
            "book_value_per_share_fq",
        ]
        result = scraper.get_fundamentals(
            exchange="NASDAQ", symbol="AAPL", fields=fields
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None

    def test_live_get_fundamentals_cash_flow_fields(self) -> None:
        """Verify cash flow fields only."""
        scraper = Fundamentals()
        fields = [
            "cash_f_operating_activities",
            "cash_f_investing_activities",
            "cash_f_financing_activities",
            "free_cash_flow",
        ]
        result = scraper.get_fundamentals(
            exchange="NASDAQ", symbol="AAPL", fields=fields
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None

    def test_live_get_fundamentals_multiple_symbols(self) -> None:
        """Verify multiple symbols can be fetched sequentially."""
        scraper = Fundamentals()
        symbols = [
            ("NASDAQ", "AAPL"),
            ("NASDAQ", "MSFT"),
            ("NYSE", "JPM"),
        ]

        for exchange, symbol in symbols:
            result = scraper.get_fundamentals(exchange=exchange, symbol=symbol)
            assert result["status"] == STATUS_SUCCESS
            assert result["metadata"]["exchange"] == exchange
            assert result["metadata"]["symbol"] == symbol


@pytest.mark.live
class TestLiveFundamentalsEdgeCases:
    """Test edge cases for fundamentals."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset validator singleton before each test."""

        yield

    def test_live_get_fundamentals_invalid_exchange(self) -> None:
        """Verify invalid exchange returns error."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(exchange="INVALID_EXCHANGE", symbol="AAPL")
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "Invalid exchange" in result["error"]

    def test_live_get_fundamentals_nonexistent_symbol(self) -> None:
        """Verify nonexistent symbol returns error."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(exchange="NASDAQ", symbol="NONEXIST123456")
        assert result["status"] == "failed"
        assert result["error"] is not None

    def test_live_get_fundamentals_invalid_fields(self) -> None:
        """Verify invalid field names return error."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(
            exchange="NASDAQ",
            symbol="AAPL",
            fields=["invalid_field_xyz", "another_invalid"],
        )
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "Invalid field" in result["error"]

    def test_live_get_fundamentals_empty_fields_list(self) -> None:
        """Verify empty fields list returns success with default fields."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(exchange="NASDAQ", symbol="AAPL", fields=[])
        assert result["status"] == STATUS_SUCCESS
        assert "symbol" in result["data"]
        assert len(result["data"]) > 0

    def test_live_get_fundamentals_non_list_fields(self) -> None:
        """Verify non-list fields parameter returns error."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(
            exchange="NASDAQ", symbol="AAPL", fields="total_revenue"
        )
        assert result["status"] == "failed"
        assert "Fields must be a list" in result["error"]

    def test_live_get_fundamentals_wrong_exchange_for_symbol(self) -> None:
        """Verify wrong exchange:symbol combination returns error."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(exchange="NYSE", symbol="AAPL")
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert (
            "not found" in result["error"].lower()
            or "invalid" in result["error"].lower()
        )


@pytest.mark.live
class TestLiveFundamentalsExport:
    """Test export functionality with real API calls."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset validator singleton before each test."""

        yield

    def test_live_get_fundamentals_with_json_export(self) -> None:
        """Verify JSON export works."""
        scraper = Fundamentals(export_result=True, export_type="json")
        result = scraper.get_fundamentals(exchange="NASDAQ", symbol="AAPL")
        assert result["status"] == STATUS_SUCCESS

    def test_live_get_fundamentals_with_csv_export(self) -> None:
        """Verify CSV export works (requires pandas)."""
        pytest.importorskip("pandas", reason="pandas required for CSV export")
        scraper = Fundamentals(export_result=True, export_type="csv")
        result = scraper.get_fundamentals(exchange="NASDAQ", symbol="AAPL")
        assert result["status"] == STATUS_SUCCESS


@pytest.mark.live
class TestLiveFundamentalsResponseEnvelope:
    """Test standardized response envelope structure."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset validator singleton before each test."""

        yield

    def test_live_success_response_structure(self) -> None:
        """Verify success response has all required keys."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["error"] is None
        assert result["metadata"]["exchange"] == "NASDAQ"
        assert result["metadata"]["symbol"] == "AAPL"

    def test_live_error_response_structure(self) -> None:
        """Verify error response has all required keys."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(exchange="INVALID_EXCHANGE", symbol="AAPL")

        assert result["status"] == "failed"
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["data"] is None
        assert result["error"] is not None
        assert "metadata" in result

    def test_live_data_contains_symbol(self) -> None:
        """Verify data contains symbol key."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert "symbol" in result["data"]
        assert "NASDAQ:AAPL" in result["data"]["symbol"]
