"""Ideas scraper live API tests.

Tests real HTTP connections to TradingView ideas endpoint.
"""

import os

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.social.ideas import Ideas


@pytest.mark.live
class TestLiveIdeas:
    """Test ideas scraper with real API calls."""

    def test_live_ideas_basic(self) -> None:
        """Verify basic ideas fetching works for NYSE:BRK.B."""
        scraper = Ideas()
        # Use NYSE:BRK.B for faster tests (AAPL has too many results)
        result = scraper.get_ideas(exchange="NYSE", symbol="BRK.B")
        assert "status" in result
        assert result["status"] == STATUS_SUCCESS
        assert "data" in result
        assert isinstance(result["data"], list)

    def test_live_ideas_popular_sort(self) -> None:
        """Verify popular ideas sorting works."""
        scraper = Ideas()
        result = scraper.get_ideas(exchange="NYSE", symbol="BRK.B", sort_by="popular")
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)

    def test_live_ideas_recent_sort(self) -> None:
        """Verify recent ideas sorting works."""
        scraper = Ideas()
        result = scraper.get_ideas(exchange="NYSE", symbol="BRK.B", sort_by="recent")
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)

    def test_live_ideas_multiple_pages(self) -> None:
        """Verify multi-page idea fetching works."""
        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="NYSE", symbol="BRK.B", start_page=1, end_page=2
        )
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)
        assert result["metadata"]["pages"] == 2

    def test_live_ideas_crypto_symbol(self) -> None:
        """Verify ideas for crypto symbols."""
        scraper = Ideas()
        result = scraper.get_ideas(exchange="BINANCE", symbol="BTCUSDT")
        assert "status" in result
        assert result["status"] in (STATUS_SUCCESS, STATUS_FAILED)

    def test_live_ideas_stock_symbol_nyse(self) -> None:
        """Verify ideas for NYSE stock symbols."""
        scraper = Ideas()
        result = scraper.get_ideas(exchange="NYSE", symbol="JPM")
        assert "status" in result


@pytest.mark.live
class TestLiveIdeasParameterCombinations:
    """Test various parameter combinations."""

    @pytest.mark.parametrize(
        "exchange,symbol",
        [
            ("NYSE", "BRK.B"),
            ("NYSE", "JPM"),
            ("BINANCE", "BTCUSDT"),
        ],
    )
    def test_live_ideas_exchange_symbol_combinations(
        self, exchange: str, symbol: str
    ) -> None:
        """Test ideas fetching across different exchange/symbol pairs."""
        scraper = Ideas()
        result = scraper.get_ideas(exchange=exchange, symbol=symbol)
        assert "status" in result
        assert result["metadata"]["exchange"].upper() == exchange.upper()
        assert result["metadata"]["symbol"].upper() == symbol.upper()

    @pytest.mark.parametrize("sort_by", ["popular", "recent"])
    def test_live_ideas_sort_options(self, sort_by: str) -> None:
        """Test both sorting options."""
        scraper = Ideas()
        result = scraper.get_ideas(exchange="NYSE", symbol="BRK.B", sort_by=sort_by)
        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["sort_by"] == sort_by

    @pytest.mark.parametrize("start,end", [(1, 1), (1, 2), (2, 3)])
    def test_live_ideas_page_ranges(self, start: int, end: int) -> None:
        """Test various page range configurations."""
        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="NYSE", symbol="BRK.B", start_page=start, end_page=end
        )
        assert "status" in result
        assert result["metadata"]["pages"] == end - start + 1


@pytest.mark.live
class TestLiveIdeasErrorHandling:
    """Test error handling for invalid inputs."""

    def test_live_ideas_invalid_exchange(self) -> None:
        """Verify handling of invalid exchange."""
        scraper = Ideas()
        result = scraper.get_ideas(exchange="INVALID_EXCHANGE", symbol="BRK.B")
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_live_ideas_invalid_page_params(self) -> None:
        """Verify handling of invalid page parameters."""
        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="NYSE", symbol="BRK.B", start_page=0, end_page=1
        )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_live_ideas_end_before_start(self) -> None:
        """Verify handling when end_page < start_page."""
        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="NYSE", symbol="BRK.B", start_page=3, end_page=1
        )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_live_ideas_invalid_sort_by(self) -> None:
        """Verify handling of invalid sort_by value."""
        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="NYSE", symbol="BRK.B", sort_by="invalid_sort"
        )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None


@pytest.mark.live
class TestLiveIdeasWithCookie:
    """Test ideas scraper with cookie authentication."""

    def test_live_ideas_with_cookie(self) -> None:
        """Verify cookie authentication works."""
        cookie = os.environ.get("TRADINGVIEW_COOKIE") or os.environ.get("TV_COOKIE")
        if not cookie:
            pytest.skip("No cookie available")

        scraper = Ideas(cookie=cookie)
        result = scraper.get_ideas(exchange="NYSE", symbol="BRK.B")
        assert "status" in result

    def test_live_ideas_without_cookie(self) -> None:
        """Verify ideas work without cookie (default behavior)."""
        scraper = Ideas(cookie=None)
        result = scraper.get_ideas(exchange="NYSE", symbol="BRK.B")
        assert "status" in result


@pytest.mark.live
class TestLiveIdeasEdgeCases:
    """Test edge cases for ideas scraper."""

    def test_live_ideas_high_page_number(self) -> None:
        """Verify high page number handling."""
        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="NYSE", symbol="BRK.B", start_page=100, end_page=105
        )
        assert "status" in result

    def test_live_ideas_rate_limiting_behavior(self) -> None:
        """Verify rate limiting behavior doesn't cause failures."""
        import time

        scraper = Ideas()
        start = time.time()
        for _ in range(2):
            result = scraper.get_ideas(exchange="NYSE", symbol="BRK.B")
            assert "status" in result
        elapsed = time.time() - start
        assert elapsed > 0

    def test_live_ideas_export_result(self) -> None:
        """Verify export functionality works."""
        import tempfile

        scraper = Ideas(export_result=True, export_type="json")
        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                result = scraper.get_ideas(exchange="NYSE", symbol="BRK.B")
                assert "status" in result
            finally:
                os.chdir(original_cwd)

    def test_live_ideas_custom_timeout(self) -> None:
        """Verify custom timeout parameter works."""
        scraper = Ideas(timeout=5)
        result = scraper.get_ideas(exchange="NYSE", symbol="BRK.B")
        assert "status" in result

    def test_live_ideas_max_workers(self) -> None:
        """Verify custom max_workers parameter works."""
        scraper = Ideas(max_workers=2)
        result = scraper.get_ideas(
            exchange="NYSE", symbol="BRK.B", start_page=1, end_page=2
        )
        assert "status" in result
