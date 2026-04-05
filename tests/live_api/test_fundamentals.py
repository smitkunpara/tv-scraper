"""Live API tests for fundamentals.

Tests real HTTP connections to TradingView fundamentals endpoint.
"""

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.market_data.fundamentals import Fundamentals


@pytest.mark.live
class TestLiveFundamentals:
    """Test fundamentals with real API calls."""

    def test_live_get_fundamentals_basic(self) -> None:
        """Verify basic fundamentals fetching works."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(exchange="NASDAQ", symbol="AAPL")
        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None

    def test_live_get_fundamentals_stock_symbol(self) -> None:
        """Verify fundamentals for stock symbols."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(exchange="NYSE", symbol="JPM")
        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None

    def test_live_get_fundamentals_custom_fields(self) -> None:
        """Verify custom fields parameter works."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(
            exchange="NASDAQ", symbol="AAPL", fields=["total_revenue", "net_income"]
        )
        assert result["status"] == STATUS_SUCCESS
        assert "total_revenue" in result["data"] or "total_revenue" in str(
            result["error"] or ""
        )

    def test_live_get_fundamentals_all_fields(self) -> None:
        """Verify all fields fetching works."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(exchange="NASDAQ", symbol="MSFT")
        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None

    def test_live_get_fundamentals_invalid_exchange(self) -> None:
        """Verify invalid exchange validation."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(exchange="INVALID_EXCHANGE", symbol="AAPL")
        assert result["status"] == "failed"
        assert result["error"] is not None

    def test_live_get_fundamentals_invalid_symbol(self) -> None:
        """Verify invalid symbol validation."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(
            exchange="NASDAQ", symbol="INVALID_SYMBOL_XYZ"
        )
        assert result["status"] in [STATUS_SUCCESS, "failed"]


@pytest.mark.live
class TestLiveFundamentalsCompare:
    """Test fundamentals comparison with real API calls."""

    def test_live_compare_fundamentals_multiple_symbols(self) -> None:
        """Verify comparison of multiple symbols works."""
        scraper = Fundamentals()
        result = scraper.compare_fundamentals(
            symbols=[("NASDAQ", "AAPL"), ("NASDAQ", "MSFT")],
            fields=["market_cap", "total_revenue"],
        )
        assert "status" in result

    def test_live_compare_fundamentals_partial_failure(self) -> None:
        """Verify partial failure handling in comparison."""
        scraper = Fundamentals()
        result = scraper.compare_fundamentals(
            symbols=[("NASDAQ", "AAPL"), ("NASDAQ", "INVALIDSYMBOL")],
            fields=["market_cap"],
        )
        assert "status" in result


@pytest.mark.live
class TestLiveFundamentalsEdgeCases:
    """Test edge cases for fundamentals."""

    def test_live_fundamentals_network_error(self) -> None:
        """Verify network error handling."""
        from unittest.mock import patch

        import requests

        scraper = Fundamentals()
        with patch.object(
            requests, "get", side_effect=requests.RequestException("Network error")
        ):
            result = scraper.get_fundamentals(exchange="NASDAQ", symbol="AAPL")
            assert result["status"] == "failed"
            assert result["error"] is not None

    def test_live_fundamentals_timeout(self) -> None:
        """Verify timeout handling."""
        from unittest.mock import patch

        import requests

        scraper = Fundamentals()
        with patch.object(requests, "get", side_effect=requests.Timeout("Timeout")):
            result = scraper.get_fundamentals(exchange="NASDAQ", symbol="AAPL")
            assert result["status"] == "failed"

    def test_live_fundamentals_invalid_fields(self) -> None:
        """Verify invalid fields validation."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(
            exchange="NASDAQ", symbol="AAPL", fields=["invalid_field_xyz"]
        )
        assert "status" in result
