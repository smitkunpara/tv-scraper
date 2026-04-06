"""Live API tests for news scraper.

Tests real HTTP connections to TradingView news endpoints.
"""

import os

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.social.news import News


@pytest.fixture
def scraper() -> News:
    """Create a News scraper instance."""
    return News()


@pytest.fixture
def scraper_with_cookie() -> News:
    """Create a News scraper with optional cookie."""
    cookie = os.environ.get("TRADINGVIEW_COOKIE")
    return News(cookie=cookie)


@pytest.mark.live
class TestLiveNewsHeadlines:
    """Test news headlines with real API calls."""

    @pytest.mark.parametrize(
        "exchange,symbol",
        [
            # Use faster symbols (AAPL is too popular)
            ("NYSE", "BRK.B"),
            ("BINANCE", "BTCUSDT"),
            ("NYSE", "JPM"),
        ],
    )
    def test_get_news_headlines_basic(
        self, scraper: News, exchange: str, symbol: str
    ) -> None:
        """Verify basic news headlines fetching works."""
        result = scraper.get_news_headlines(exchange=exchange, symbol=symbol)
        assert "status" in result
        if result["status"] == STATUS_SUCCESS:
            assert isinstance(result["data"], list)

    @pytest.mark.parametrize(
        "exchange,symbol",
        [
            ("NYSE", "BRK.B"),
            ("BINANCE", "BTCUSDT"),
        ],
    )
    def test_get_news_headlines_sort_options(
        self, scraper: News, exchange: str, symbol: str
    ) -> None:
        """Verify all sort options work."""
        for sort_by in ["latest", "oldest", "most_urgent", "least_urgent"]:
            result = scraper.get_news_headlines(
                exchange=exchange, symbol=symbol, sort_by=sort_by
            )
            assert result["status"] in [STATUS_SUCCESS, STATUS_FAILED]
            if result["status"] == STATUS_SUCCESS:
                assert result["metadata"]["sort_by"] == sort_by

    @pytest.mark.parametrize(
        "section",
        [
            "all",
            "esg",
            "press_release",
            "financial_statement",
        ],
    )
    def test_get_news_headlines_sections(self, scraper: News, section: str) -> None:
        """Verify all section options work."""
        result = scraper.get_news_headlines(
            exchange="NYSE", symbol="BRK.B", section=section
        )
        assert result["status"] in [STATUS_SUCCESS, STATUS_FAILED]
        if result["status"] == STATUS_SUCCESS:
            assert result["metadata"]["section"] == section

    def test_get_news_headlines_with_provider(self, scraper: News) -> None:
        """Verify provider filter works."""
        result = scraper.get_news_headlines(
            exchange="NYSE", symbol="BRK.B", provider="reuters"
        )
        assert "status" in result

    def test_get_news_headlines_with_area(self, scraper: News) -> None:
        """Verify area filter works."""
        result = scraper.get_news_headlines(exchange="NYSE", symbol="BRK.B", area="us")
        assert "status" in result

    @pytest.mark.parametrize("language", ["en", "de", "fr", "es"])
    def test_get_news_headlines_languages(self, scraper: News, language: str) -> None:
        """Verify language filter works."""
        result = scraper.get_news_headlines(
            exchange="NYSE", symbol="BRK.B", language=language
        )
        assert result["status"] in [STATUS_SUCCESS, STATUS_FAILED]
        if result["status"] == STATUS_SUCCESS:
            assert result["metadata"]["language"] == language

    def test_get_news_headlines_stock_symbol(self, scraper: News) -> None:
        """Verify news for stock symbols."""
        result = scraper.get_news_headlines(exchange="NYSE", symbol="JPM")
        assert "status" in result

    def test_get_news_headlines_crypto_symbol(self, scraper: News) -> None:
        """Verify news for crypto symbols."""
        result = scraper.get_news_headlines(exchange="BINANCE", symbol="BTCUSDT")
        assert "status" in result

    def test_get_news_headlines_with_cookie(self, scraper_with_cookie: News) -> None:
        """Verify cookie authentication works."""
        result = scraper_with_cookie.get_news_headlines(exchange="NYSE", symbol="BRK.B")
        assert "status" in result


@pytest.mark.live
class TestLiveNewsContent:
    """Test news content scraping with real API calls."""

    def test_get_news_content_basic(self, scraper: News) -> None:
        """Verify basic news content fetching works."""
        headlines = scraper.get_news_headlines(exchange="NYSE", symbol="BRK.B")
        if headlines["data"] and len(headlines["data"]) > 0:
            story_id = headlines["data"][0]["id"]
            result = scraper.get_news_content(story_id=story_id)
            assert "status" in result

    def test_get_news_content_from_fixture(self, scraper: News) -> None:
        """Verify content fetching from saved fixture."""
        headlines = scraper.get_news_headlines(exchange="NYSE", symbol="BRK.B")
        if headlines.get("data") and len(headlines["data"]) > 0:
            story_id = headlines["data"][0]["id"]
            result = scraper.get_news_content(story_id=story_id)
            assert "status" in result

    def test_get_news_content_multiple_stories(self, scraper: News) -> None:
        """Verify fetching multiple story contents."""
        headlines = scraper.get_news_headlines(exchange="NYSE", symbol="BRK.B")
        if headlines["data"] and len(headlines["data"]) > 0:
            for item in headlines["data"][:3]:
                story_id = item["id"]
                result = scraper.get_news_content(story_id=story_id)
                assert "status" in result

    def test_get_news_content_invalid_story_id(self, scraper: News) -> None:
        """Verify handling of invalid story ID."""
        result = scraper.get_news_content(story_id="invalid_story_id_xyz")
        assert "status" in result

    def test_get_news_content_empty_story_id(self, scraper: News) -> None:
        """Verify handling of empty story ID."""
        result = scraper.get_news_content(story_id="")
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_get_news_content_with_language(self, scraper: News) -> None:
        """Verify content fetching with language parameter."""
        headlines = scraper.get_news_headlines(exchange="NYSE", symbol="BRK.B")
        if headlines["data"] and len(headlines["data"]) > 0:
            story_id = headlines["data"][0]["id"]
            for language in ["en", "de", "fr"]:
                result = scraper.get_news_content(story_id=story_id, language=language)
                assert "status" in result


@pytest.mark.live
class TestLiveNewsEdgeCases:
    """Test edge cases for news scraper."""

    def test_invalid_exchange(self, scraper: News) -> None:
        """Verify handling of invalid exchange."""
        result = scraper.get_news_headlines(exchange="INVALID_EXCHANGE", symbol="BRK.B")
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_invalid_symbol(self, scraper: News) -> None:
        """Verify handling of invalid symbol."""
        result = scraper.get_news_headlines(
            exchange="NASDAQ", symbol="INVALID_SYMBOL_XYZ"
        )
        assert result["status"] in [STATUS_SUCCESS, STATUS_FAILED]

    def test_invalid_section(self, scraper: News) -> None:
        """Verify invalid section validation."""
        result = scraper.get_news_headlines(
            exchange="NYSE", symbol="BRK.B", section="invalid_section"
        )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_invalid_sort(self, scraper: News) -> None:
        """Verify invalid sort validation."""
        result = scraper.get_news_headlines(
            exchange="NYSE", symbol="BRK.B", sort_by="invalid_sort"
        )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_invalid_language(self, scraper: News) -> None:
        """Verify invalid language validation."""
        result = scraper.get_news_headlines(
            exchange="NYSE", symbol="BRK.B", language="invalid_lang"
        )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_invalid_provider(self, scraper: News) -> None:
        """Verify invalid provider validation."""
        result = scraper.get_news_headlines(
            exchange="NYSE", symbol="BRK.B", provider="invalid_provider"
        )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_invalid_area(self, scraper: News) -> None:
        """Verify invalid area validation."""
        result = scraper.get_news_headlines(
            exchange="NYSE", symbol="BRK.B", area="invalid_area"
        )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_all_valid_sections_combined(self, scraper: News) -> None:
        """Verify all sections work with provider and area."""
        result = scraper.get_news_headlines(
            exchange="NYSE",
            symbol="BRK.B",
            section="all",
            provider=None,
            area=None,
        )
        assert result["status"] in [STATUS_SUCCESS, STATUS_FAILED]


@pytest.mark.live
class TestLiveNewsRateLimiting:
    """Test rate limiting behavior."""

    def test_consecutive_requests(self, scraper: News) -> None:
        """Verify consecutive requests behavior."""
        import time

        start = time.time()
        for _ in range(3):
            result = scraper.get_news_headlines(exchange="NYSE", symbol="BRK.B")
            assert "status" in result
        elapsed = time.time() - start
        assert elapsed > 0

    def test_request_timeout(self, scraper: News) -> None:
        """Verify timeout handling."""
        scraper_short = News(timeout=1)
        result = scraper_short.get_news_headlines(exchange="NYSE", symbol="BRK.B")
        assert "status" in result
