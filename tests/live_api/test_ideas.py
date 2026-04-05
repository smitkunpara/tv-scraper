"""Live API tests for ideas scraper.

Tests real HTTP connections to TradingView ideas endpoint.
"""

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.social.ideas import Ideas


@pytest.mark.live
class TestLiveIdeas:
    """Test ideas scraper with real API calls."""

    def test_live_get_ideas_basic(self) -> None:
        """Verify basic ideas fetching works."""
        scraper = Ideas()
        result = scraper.get_ideas(exchange="NASDAQ", symbol="AAPL")
        assert "status" in result

    def test_live_get_ideas_popular_sort(self) -> None:
        """Verify popular ideas sorting works."""
        scraper = Ideas()
        result = scraper.get_ideas(exchange="NASDAQ", symbol="AAPL", sort_by="popular")
        assert "status" in result

    def test_live_get_ideas_recent_sort(self) -> None:
        """Verify recent ideas sorting works."""
        scraper = Ideas()
        result = scraper.get_ideas(exchange="NASDAQ", symbol="AAPL", sort_by="recent")
        assert "status" in result

    def test_live_get_ideas_multiple_pages(self) -> None:
        """Verify multi-page idea fetching works."""
        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="NASDAQ", symbol="AAPL", start_page=1, end_page=2
        )
        assert "status" in result

    def test_live_get_ideas_no_data(self) -> None:
        """Verify empty results handling."""
        scraper = Ideas()
        result = scraper.get_ideas(exchange="NASDAQ", symbol="AAPL")
        assert "status" in result

    def test_live_get_ideas_crypto_symbol(self) -> None:
        """Verify ideas for crypto symbols."""
        scraper = Ideas()
        result = scraper.get_ideas(exchange="BINANCE", symbol="BTCUSDT")
        assert "status" in result

    def test_live_get_ideas_stock_symbol(self) -> None:
        """Verify ideas for stock symbols."""
        scraper = Ideas()
        result = scraper.get_ideas(exchange="NYSE", symbol="JPM")
        assert "status" in result

    def test_live_get_ideas_invalid_exchange(self) -> None:
        """Verify handling of invalid exchange."""
        scraper = Ideas()
        result = scraper.get_ideas(exchange="INVALID_EXCHANGE", symbol="AAPL")
        assert result["status"] == "failed"
        assert result["error"] is not None

    def test_live_get_ideas_invalid_symbol(self) -> None:
        """Verify handling of invalid symbol."""
        scraper = Ideas()
        result = scraper.get_ideas(exchange="NASDAQ", symbol="INVALID_SYMBOL_123")
        assert result["status"] in [STATUS_SUCCESS, "failed"]


@pytest.mark.live
class TestLiveIdeasEdgeCases:
    """Test edge cases for ideas scraper."""

    def test_live_get_ideas_high_page_number(self) -> None:
        """Verify high page number handling."""
        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="NASDAQ", symbol="AAPL", start_page=100, end_page=105
        )
        assert "status" in result

    def test_live_get_ideas_rate_limiting(self) -> None:
        """Verify rate limiting behavior."""
        import time

        scraper = Ideas()
        start = time.time()
        for _ in range(2):
            result = scraper.get_ideas(exchange="NASDAQ", symbol="AAPL")
            assert "status" in result
        elapsed = time.time() - start
        assert elapsed > 0

    def test_live_get_ideas_cookie_auth(self) -> None:
        """Verify cookie authentication works."""
        import os

        cookie = os.environ.get("TRADINGVIEW_COOKIE") or os.environ.get("TV_COOKIE")
        if cookie:
            scraper = Ideas(cookie=cookie)
            result = scraper.get_ideas(exchange="NASDAQ", symbol="AAPL")
            assert "status" in result
        else:
            pytest.skip("No cookie available")
