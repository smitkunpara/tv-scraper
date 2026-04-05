"""Live API tests for news scraper.

Tests real HTTP connections to TradingView news endpoints.
"""

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.social.news import News


@pytest.mark.live
class TestLiveNewsHeadlines:
    """Test news headlines with real API calls."""

    def test_live_get_news_headlines_basic(self) -> None:
        """Verify basic news headlines fetching works."""
        scraper = News()
        result = scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL")
        assert result["status"] == STATUS_SUCCESS
        assert "data" in result

    def test_live_get_news_headlines_with_provider(self) -> None:
        """Verify provider filter works."""
        scraper = News()
        result = scraper.get_news_headlines(
            exchange="NASDAQ", symbol="AAPL", provider="reuters"
        )
        assert "status" in result

    def test_live_get_news_headlines_with_area(self) -> None:
        """Verify area filter works."""
        scraper = News()
        result = scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL", area="us")
        assert "status" in result

    def test_live_get_news_headlines_with_language(self) -> None:
        """Verify language filter works."""
        scraper = News()
        result = scraper.get_news_headlines(
            exchange="NASDAQ", symbol="AAPL", language="en"
        )
        assert result["status"] == STATUS_SUCCESS

    def test_live_get_news_headlines_sort_latest(self) -> None:
        """Verify latest sorting works."""
        scraper = News()
        result = scraper.get_news_headlines(
            exchange="NASDAQ", symbol="AAPL", sort_by="latest"
        )
        assert result["status"] == STATUS_SUCCESS

    def test_live_get_news_headlines_sort_oldest(self) -> None:
        """Verify oldest sorting works."""
        scraper = News()
        result = scraper.get_news_headlines(
            exchange="NASDAQ", symbol="AAPL", sort_by="oldest"
        )
        assert result["status"] == STATUS_SUCCESS

    def test_live_get_news_headlines_sort_most_urgent(self) -> None:
        """Verify most urgent sorting works."""
        scraper = News()
        result = scraper.get_news_headlines(
            exchange="NASDAQ", symbol="AAPL", sort_by="most_urgent"
        )
        assert result["status"] == STATUS_SUCCESS

    def test_live_get_news_headlines_sort_least_urgent(self) -> None:
        """Verify least urgent sorting works."""
        scraper = News()
        result = scraper.get_news_headlines(
            exchange="NASDAQ", symbol="AAPL", sort_by="least_urgent"
        )
        assert result["status"] == STATUS_SUCCESS

    def test_live_get_news_headlines_crypto_symbol(self) -> None:
        """Verify news for crypto symbols."""
        scraper = News()
        result = scraper.get_news_headlines(exchange="BINANCE", symbol="BTCUSDT")
        assert "status" in result

    def test_live_get_news_headlines_stock_symbol(self) -> None:
        """Verify news for stock symbols."""
        scraper = News()
        result = scraper.get_news_headlines(exchange="NYSE", symbol="JPM")
        assert result["status"] == STATUS_SUCCESS


@pytest.mark.live
class TestLiveNewsContent:
    """Test news content scraping with real API calls."""

    def test_live_get_news_content_basic(self) -> None:
        """Verify basic news content fetching works."""
        scraper = News()
        headlines = scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL")

        if headlines["data"] and len(headlines["data"]) > 0:
            story_id = headlines["data"][0]["id"]
            result = scraper.get_news_content(story_id=story_id)
            assert "status" in result

    def test_live_get_news_content_invalid_story_id(self) -> None:
        """Verify handling of invalid story ID."""
        scraper = News()
        result = scraper.get_news_content(story_id="invalid_story_id_xyz")
        assert "status" in result

    def test_live_get_news_content_empty_story_id(self) -> None:
        """Verify handling of empty story ID."""
        scraper = News()
        result = scraper.get_news_content(story_id="")
        assert result["status"] == "failed"
        assert result["error"] is not None


@pytest.mark.live
class TestLiveNewsEdgeCases:
    """Test edge cases for news scraper."""

    def test_live_news_network_error(self) -> None:
        """Verify network error handling."""
        from unittest.mock import patch

        import requests

        scraper = News()
        with patch.object(
            requests, "get", side_effect=requests.RequestException("Network error")
        ):
            result = scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL")
            assert result["status"] == "failed"
            assert result["error"] is not None

    def test_live_news_timeout(self) -> None:
        """Verify timeout handling."""
        from unittest.mock import patch

        import requests

        scraper = News()
        with patch.object(requests, "get", side_effect=requests.Timeout("Timeout")):
            result = scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL")
            assert result["status"] == "failed"

    def test_live_news_invalid_section(self) -> None:
        """Verify invalid section validation."""
        scraper = News()
        result = scraper.get_news_headlines(
            exchange="NASDAQ", symbol="AAPL", section="invalid_section"
        )
        assert result["status"] == "failed"
        assert result["error"] is not None

    def test_live_news_invalid_sort(self) -> None:
        """Verify invalid sort validation."""
        scraper = News()
        result = scraper.get_news_headlines(
            exchange="NASDAQ", symbol="AAPL", sort_by="invalid_sort"
        )
        assert result["status"] == "failed"
        assert result["error"] is not None
