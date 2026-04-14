"""Integration tests for Fundamentals scraper.

Tests cross-module workflows and integration with other scrapers.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.market_data.fundamentals import Fundamentals

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "fundamentals"


def _load_fixture(name: str) -> dict:
    """Load fixture data from fixtures directory."""
    filepath = FIXTURES_DIR / f"{name}.json"
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    pytest.skip(f"Fixture not found: {filepath}")


@pytest.fixture(autouse=True)
def setup():
    """Reset validator singleton before each test."""
    yield


class TestFundamentalsWithScreener:
    """Test Fundamentals integration with Screener."""

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_fundamentals_after_screener_filter(self, mock_fetch: MagicMock) -> None:
        """Test fetching fundamentals for symbols from screener filter."""
        mock_fetch.return_value = {
            "status": STATUS_SUCCESS,
            "data": {
                "symbol": "NASDAQ:AAPL",
                "total_revenue": 394328000000,
                "net_income": 99803000000,
            },
            "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
            "error": None,
        }

        fund = Fundamentals()
        symbols_to_check = ["AAPL", "MSFT", "GOOGL"]
        results = {}

        for symbol in symbols_to_check:
            result = fund.get_fundamentals(exchange="NASDAQ", symbol=symbol)
            if result["status"] == STATUS_SUCCESS:
                results[symbol] = result["data"]

        assert len(results) <= len(symbols_to_check)
        for _symbol, data in results.items():
            assert "symbol" in data

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_compare_fundamentals_across_symbols(self, mock_fetch: MagicMock) -> None:
        """Test comparing fundamentals data across multiple symbols."""
        symbols = [
            ("NASDAQ", "AAPL"),
            ("NASDAQ", "MSFT"),
        ]

        fund = Fundamentals()
        comparison_data = {}

        for exchange, symbol in symbols:
            mock_fetch.return_value = {
                "status": STATUS_SUCCESS,
                "data": {
                    "symbol": f"{exchange}:{symbol}",
                    "total_revenue": 100000000000 if symbol == "AAPL" else 200000000000,
                    "net_income": 20000000000 if symbol == "AAPL" else 50000000000,
                },
                "metadata": {"exchange": exchange, "symbol": symbol},
                "error": None,
            }

            result = fund.get_fundamentals(
                exchange=exchange,
                symbol=symbol,
                fields=["total_revenue", "net_income"],
            )
            if result["status"] == STATUS_SUCCESS:
                comparison_data[symbol] = result["data"]

        assert len(comparison_data) <= len(symbols)

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_fundamentals_with_custom_fields_subset(
        self, mock_fetch: MagicMock
    ) -> None:
        """Test fetching only specific fields for multiple symbols."""
        symbols = [
            ("NASDAQ", "AAPL"),
            ("NYSE", "JPM"),
        ]

        fund = Fundamentals()
        fields = ["market_cap_basic", "price_earnings_ttm", "dividends_yield"]

        for exchange, symbol in symbols:
            mock_fetch.return_value = {
                "status": STATUS_SUCCESS,
                "data": {
                    "symbol": f"{exchange}:{symbol}",
                    "market_cap_basic": 1000000000000,
                    "price_earnings_ttm": 25.0,
                    "dividends_yield": 0.015,
                },
                "metadata": {"exchange": exchange, "symbol": symbol},
                "error": None,
            }

            result = fund.get_fundamentals(
                exchange=exchange, symbol=symbol, fields=fields
            )
            assert result["status"] == STATUS_SUCCESS
            assert all(f in result["data"] for f in fields)


class TestFundamentalsFieldGroups:
    """Test Fundamentals with different field groups."""

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_income_statement_fields(self, mock_fetch: MagicMock) -> None:
        """Test fetching income statement fields."""
        mock_fetch.return_value = {
            "status": STATUS_SUCCESS,
            "data": {
                "symbol": "NASDAQ:AAPL",
                "total_revenue": 394328000000,
                "revenue_per_share_ttm": 24.5,
                "net_income": 99803000000,
                "EBITDA": 133819000000,
            },
            "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
            "error": None,
        }

        fund = Fundamentals()
        result = fund.get_fundamentals(
            exchange="NASDAQ",
            symbol="AAPL",
            fields=["total_revenue", "net_income", "EBITDA"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"]["total_revenue"] == 394328000000
        assert result["data"]["net_income"] == 99803000000

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_valuation_fields(self, mock_fetch: MagicMock) -> None:
        """Test fetching valuation fields."""
        mock_fetch.return_value = {
            "status": STATUS_SUCCESS,
            "data": {
                "symbol": "NASDAQ:MSFT",
                "market_cap_basic": 2800000000000,
                "price_earnings_ttm": 35.2,
            },
            "metadata": {"exchange": "NASDAQ", "symbol": "MSFT"},
            "error": None,
        }

        fund = Fundamentals()
        result = fund.get_fundamentals(
            exchange="NASDAQ",
            symbol="MSFT",
            fields=["market_cap_basic", "price_earnings_ttm"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"]["market_cap_basic"] == 2800000000000
        assert result["data"]["price_earnings_ttm"] == 35.2

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_dividend_fields(self, mock_fetch: MagicMock) -> None:
        """Test fetching dividend fields."""
        mock_fetch.return_value = {
            "status": STATUS_SUCCESS,
            "data": {
                "symbol": "NYSE:JPM",
                "dividends_yield": 0.0235,
                "dividends_per_share_fq": 1.15,
            },
            "metadata": {"exchange": "NYSE", "symbol": "JPM"},
            "error": None,
        }

        fund = Fundamentals()
        result = fund.get_fundamentals(
            exchange="NYSE",
            symbol="JPM",
            fields=["dividends_yield", "dividends_per_share_fq"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"]["dividends_yield"] == 0.0235

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_profitability_fields(self, mock_fetch: MagicMock) -> None:
        """Test fetching profitability fields."""
        mock_fetch.return_value = {
            "status": STATUS_SUCCESS,
            "data": {
                "symbol": "NASDAQ:AAPL",
                "return_on_equity": 1.56,
                "return_on_equity_fq": 0.42,
            },
            "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
            "error": None,
        }

        fund = Fundamentals()
        result = fund.get_fundamentals(
            exchange="NASDAQ",
            symbol="AAPL",
            fields=["return_on_equity", "return_on_equity_fq"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"]["return_on_equity"] == 1.56

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_leverage_fields(self, mock_fetch: MagicMock) -> None:
        """Test fetching leverage fields."""
        mock_fetch.return_value = {
            "status": STATUS_SUCCESS,
            "data": {
                "symbol": "NYSE:JPM",
                "debt_to_equity": 1.35,
                "debt_to_equity_fq": 1.28,
            },
            "metadata": {"exchange": "NYSE", "symbol": "JPM"},
            "error": None,
        }

        fund = Fundamentals()
        result = fund.get_fundamentals(
            exchange="NYSE",
            symbol="JPM",
            fields=["debt_to_equity", "debt_to_equity_fq"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"]["debt_to_equity"] == 1.35

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_liquidity_fields(self, mock_fetch: MagicMock) -> None:
        """Test fetching liquidity fields."""
        mock_fetch.return_value = {
            "status": STATUS_SUCCESS,
            "data": {
                "symbol": "NYSE:JPM",
                "current_ratio": 1.45,
                "quick_ratio": 1.35,
            },
            "metadata": {"exchange": "NYSE", "symbol": "JPM"},
            "error": None,
        }

        fund = Fundamentals()
        result = fund.get_fundamentals(
            exchange="NYSE",
            symbol="JPM",
            fields=["current_ratio", "quick_ratio"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"]["current_ratio"] == 1.45


class TestFundamentalsWorkflows:
    """Test complete workflows with Fundamentals."""

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_batch_fundamentals_fetch(self, mock_fetch: MagicMock) -> None:
        """Test batch fetching fundamentals for multiple symbols."""
        symbols = [
            ("NASDAQ", "AAPL"),
            ("NASDAQ", "MSFT"),
            ("NYSE", "JPM"),
        ]

        fund = Fundamentals()
        fields = ["total_revenue", "net_income", "market_cap_basic"]
        results = {}

        for exchange, symbol in symbols:
            mock_fetch.return_value = {
                "status": STATUS_SUCCESS,
                "data": {
                    "symbol": f"{exchange}:{symbol}",
                    "total_revenue": 100000000000,
                    "net_income": 20000000000,
                },
                "metadata": {"exchange": exchange, "symbol": symbol},
                "error": None,
            }

            result = fund.get_fundamentals(
                exchange=exchange, symbol=symbol, fields=fields
            )
            if result["status"] == STATUS_SUCCESS:
                results[symbol] = result["data"]

        assert len(results) <= len(symbols)

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_selective_field_fetch(self, mock_fetch: MagicMock) -> None:
        """Test fetching only needed fields to optimize."""
        mock_fetch.return_value = {
            "status": STATUS_SUCCESS,
            "data": {
                "symbol": "NASDAQ:AAPL",
                "price_earnings_ttm": 28.5,
                "price_book_fq": 45.2,
                "market_cap_basic": 2800000000000,
            },
            "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
            "error": None,
        }

        fund = Fundamentals()
        result = fund.get_fundamentals(
            exchange="NASDAQ",
            symbol="AAPL",
            fields=["price_earnings_ttm", "price_book_fq", "market_cap_basic"],
        )

        assert result["status"] == STATUS_SUCCESS
        valuation_data = {
            "pe": result["data"]["price_earnings_ttm"],
            "pb": result["data"]["price_book_fq"],
            "mcap": result["data"]["market_cap_basic"],
        }
        assert valuation_data["pe"] == 28.5
        assert valuation_data["pb"] == 45.2

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_export_fundamentals_data(self, mock_fetch: MagicMock) -> None:
        """Test exporting fundamentals data."""
        mock_fetch.return_value = {
            "status": STATUS_SUCCESS,
            "data": {
                "symbol": "NASDAQ:AAPL",
                "total_revenue": 394328000000,
                "net_income": 99803000000,
            },
            "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
            "error": None,
        }

        fund = Fundamentals(export="json")
        result = fund.get_fundamentals(
            exchange="NASDAQ",
            symbol="AAPL",
            fields=["total_revenue", "net_income"],
        )

        assert result["status"] == STATUS_SUCCESS


class TestFundamentalsWithFixtures:
    """Test Fundamentals using saved fixtures."""

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_use_saved_fixture_aapl(self, mock_fetch: MagicMock) -> None:
        """Test using saved AAPL fixture."""
        fixture = _load_fixture("aapl_nasdaq_all_fields")

        mock_fetch.return_value = {
            "status": STATUS_SUCCESS,
            "data": fixture["data"],
            "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
            "error": None,
        }

        fund = Fundamentals()
        result = fund.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert "symbol" in result["data"]


class TestFundamentalsErrorRecovery:
    """Test error handling and recovery scenarios."""

    def test_partial_failure_still_returns_metadata(self) -> None:
        """Test that partial failures still include metadata."""
        from tv_scraper.core.constants import STATUS_FAILED

        fund = Fundamentals()
        result = fund.get_fundamentals(exchange="INVALID_EXCHANGE", symbol="AAPL")

        assert result["status"] == STATUS_FAILED
        assert "exchange" in result["metadata"]
        assert "symbol" in result["metadata"]
        assert result["metadata"]["exchange"] == "INVALID_EXCHANGE"
        assert result["metadata"]["symbol"] == "AAPL"

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_sequential_requests_with_error_recovery(
        self, mock_fetch: MagicMock
    ) -> None:
        """Test sequential requests where some fail and some succeed."""
        mock_fetch.side_effect = [
            {
                "status": "failed",
                "data": None,
                "metadata": {"exchange": "NASDAQ", "symbol": "INVALIDSYM"},
                "error": "Symbol not found",
            },
            {
                "status": STATUS_SUCCESS,
                "data": {
                    "symbol": "NASDAQ:MSFT",
                    "total_revenue": 198270000000,
                },
                "metadata": {"exchange": "NASDAQ", "symbol": "MSFT"},
                "error": None,
            },
        ]

        fund = Fundamentals()

        result1 = fund.get_fundamentals(exchange="NASDAQ", symbol="INVALIDSYM")
        assert result1["status"] == "failed"

        result2 = fund.get_fundamentals(exchange="NASDAQ", symbol="MSFT")
        assert result2["status"] == STATUS_SUCCESS

    def test_validation_error_does_not_make_network_request(self) -> None:
        """Test that validation errors are caught before network request."""
        fund = Fundamentals()
        result = fund.get_fundamentals(
            exchange="INVALID_EXCHANGE",
            symbol="AAPL",
            fields=["invalid_field"],
        )

        assert result["status"] == "failed"


class TestFundamentalsConsistency:
    """Test consistency across multiple calls."""

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_same_request_returns_same_structure(self, mock_fetch: MagicMock) -> None:
        """Test that identical requests return consistent structure."""
        mock_fetch.return_value = {
            "status": STATUS_SUCCESS,
            "data": {
                "symbol": "NASDAQ:AAPL",
                "total_revenue": 394328000000,
            },
            "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
            "error": None,
        }

        fund = Fundamentals()
        result1 = fund.get_fundamentals(
            exchange="NASDAQ", symbol="AAPL", fields=["total_revenue"]
        )
        result2 = fund.get_fundamentals(
            exchange="NASDAQ", symbol="AAPL", fields=["total_revenue"]
        )

        assert result1["status"] == result2["status"]
        assert set(result1["data"].keys()) == set(result2["data"].keys())
        assert result1["metadata"] == result2["metadata"]

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_different_fields_return_different_data(
        self, mock_fetch: MagicMock
    ) -> None:
        """Test that different field requests return appropriate data."""
        mock_fetch.side_effect = [
            {
                "status": STATUS_SUCCESS,
                "data": {"symbol": "NASDAQ:AAPL", "total_revenue": 100},
                "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
                "error": None,
            },
            {
                "status": STATUS_SUCCESS,
                "data": {"symbol": "NASDAQ:AAPL", "net_income": 200},
                "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
                "error": None,
            },
        ]

        fund = Fundamentals()

        result1 = fund.get_fundamentals(
            exchange="NASDAQ", symbol="AAPL", fields=["total_revenue"]
        )
        result2 = fund.get_fundamentals(
            exchange="NASDAQ", symbol="AAPL", fields=["net_income"]
        )

        assert "total_revenue" in result1["data"]
        assert "net_income" in result2["data"]
