"""Live API tests for market movers.

Tests real HTTP connections to TradingView market movers endpoint.
"""

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.screening.market_movers import MarketMovers


@pytest.mark.live
class TestLiveMarketMovers:
    """Test market movers with real API calls."""

    def test_live_get_market_movers_gainers(self) -> None:
        """Verify gainers category works."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=5
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_get_market_movers_losers(self) -> None:
        """Verify losers category works."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="losers", limit=5
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_get_market_movers_most_active(self) -> None:
        """Verify most active category works."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="most-active", limit=5
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_get_market_movers_stocks_usa(self) -> None:
        """Verify stocks-usa market works."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=5
        )
        assert result["status"] == STATUS_SUCCESS

    def test_live_get_market_movers_crypto(self) -> None:
        """Verify crypto market works."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(market="crypto", category="gainers", limit=5)
        assert result["status"] == STATUS_SUCCESS

    def test_live_get_market_movers_with_custom_fields(self) -> None:
        """Verify custom fields parameter works."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=5, fields=["close", "change"]
        )
        assert result["status"] == STATUS_SUCCESS

    def test_live_get_market_movers_with_limit(self) -> None:
        """Verify limit parameter works."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=3
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) <= 3


@pytest.mark.live
class TestLiveMarketMoversEdgeCases:
    """Test edge cases for market movers."""

    def test_live_market_movers_invalid_market(self) -> None:
        """Verify invalid market validation."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="invalid_market_xyz", category="gainers", limit=5
        )
        assert result["status"] == "failed"
        assert result["error"] is not None

    def test_live_market_movers_invalid_category(self) -> None:
        """Verify invalid category validation."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="invalid_category", limit=5
        )
        assert result["status"] == "failed"
        assert result["error"] is not None

    def test_live_market_movers_invalid_limit(self) -> None:
        """Verify invalid limit validation."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=-1
        )
        assert result["status"] == "failed"
        assert result["error"] is not None

    def test_live_market_movers_invalid_language(self) -> None:
        """Verify invalid language validation."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=5, language="invalid_lang"
        )
        assert result["status"] == "failed"
        assert result["error"] is not None

    def test_live_market_movers_network_error(self) -> None:
        """Verify network error handling."""
        from unittest.mock import patch

        import requests

        scraper = MarketMovers()
        with patch.object(
            requests, "post", side_effect=requests.RequestException("Network error")
        ):
            result = scraper.get_market_movers(
                market="stocks-usa", category="gainers", limit=5
            )
            assert result["status"] == "failed"
            assert result["error"] is not None
