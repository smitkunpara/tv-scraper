"""Live API tests for minds scraper.

Tests real HTTP connections to TradingView minds endpoint.
"""

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.social.minds import Minds


@pytest.mark.live
class TestLiveMinds:
    """Test minds scraper with real API calls."""

    def test_live_get_minds_basic(self) -> None:
        """Verify basic minds fetching works."""
        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")
        assert result["status"] == STATUS_SUCCESS

    def test_live_get_minds_with_limit(self) -> None:
        """Verify limit parameter works correctly."""
        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL", limit=5)
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) <= 5

    def test_live_get_minds_pagination(self) -> None:
        """Verify multi-page pagination works."""
        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL", limit=20)
        assert result["status"] == STATUS_SUCCESS

    def test_live_get_minds_no_data(self) -> None:
        """Verify empty results handling."""
        scraper = Minds()
        result = scraper.get_minds(exchange="BINANCE", symbol="UNKNOWNCOIN")
        assert "status" in result

    def test_live_get_minds_stock_symbol(self) -> None:
        """Verify minds for stock symbols."""
        scraper = Minds()
        result = scraper.get_minds(exchange="NYSE", symbol="JPM")
        assert result["status"] == STATUS_SUCCESS

    def test_live_get_minds_crypto_symbol(self) -> None:
        """Verify minds for crypto symbols."""
        scraper = Minds()
        result = scraper.get_minds(exchange="BINANCE", symbol="BTCUSDT")
        assert "status" in result

    def test_live_get_minds_invalid_exchange(self) -> None:
        """Verify handling of invalid exchange."""
        scraper = Minds()
        result = scraper.get_minds(exchange="INVALID_EXCHANGE", symbol="AAPL")
        assert result["status"] == "failed"
        assert result["error"] is not None

    def test_live_get_minds_invalid_symbol(self) -> None:
        """Verify handling of invalid symbol."""
        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="INVALID_SYMBOL_XYZ")
        assert "status" in result


@pytest.mark.live
class TestLiveMindsEdgeCases:
    """Test edge cases for minds scraper."""

    def test_live_get_minds_network_error(self) -> None:
        """Verify network error handling."""
        from unittest.mock import patch

        import requests

        scraper = Minds()
        with patch.object(
            requests, "request", side_effect=requests.RequestException("Network error")
        ):
            result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")
            assert result["status"] == "failed"
            assert result["error"] is not None

    def test_live_get_minds_timeout(self) -> None:
        """Verify timeout handling."""
        from unittest.mock import patch

        import requests

        scraper = Minds()
        with patch.object(requests, "request", side_effect=requests.Timeout("Timeout")):
            result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")
            assert result["status"] == "failed"

    def test_live_get_minds_rate_limiting(self) -> None:
        """Verify rate limiting behavior."""
        import time

        scraper = Minds()
        start = time.time()
        for _ in range(2):
            result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL", limit=3)
            assert result["status"] == STATUS_SUCCESS
            time.sleep(1)
        elapsed = time.time() - start
        assert elapsed > 0
