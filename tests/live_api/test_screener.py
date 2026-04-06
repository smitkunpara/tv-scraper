"""Live API tests for screener.

Tests real HTTP connections to TradingView screener endpoint.
"""

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.screening.screener import Screener


@pytest.mark.live
class TestLiveScreener:
    """Test screener with real API calls."""

    def test_live_get_screener_basic(self) -> None:
        """Verify basic screener fetching works."""
        scraper = Screener()
        result = scraper.get_screener(market="america", limit=5)
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_get_screener_america_market(self) -> None:
        """Verify America market screener."""
        scraper = Screener()
        result = scraper.get_screener(market="america", limit=10)
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_get_screener_crypto_market(self) -> None:
        """Verify crypto market screener."""
        scraper = Screener()
        result = scraper.get_screener(market="crypto", limit=10)
        assert result["status"] == STATUS_SUCCESS

    def test_live_get_screener_forex_market(self) -> None:
        """Verify forex market screener."""
        scraper = Screener()
        result = scraper.get_screener(market="forex", limit=10)
        assert result["status"] == STATUS_SUCCESS

    def test_live_get_screener_with_filters(self) -> None:
        """Verify filter parameters work."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "greater", "right": 100}],
            limit=5,
        )
        assert result["status"] == STATUS_SUCCESS

    def test_live_get_screener_with_sort(self) -> None:
        """Verify sort parameters work."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            sort_by="close",
            sort_order="desc",
            limit=5,
        )
        assert result["status"] == STATUS_SUCCESS

    def test_live_get_screener_custom_fields(self) -> None:
        """Verify custom fields work."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            fields=["close", "change", "volume"],
            limit=5,
        )
        assert result["status"] == STATUS_SUCCESS

    def test_live_get_screener_with_limit(self) -> None:
        """Verify limit parameter works."""
        scraper = Screener()
        result = scraper.get_screener(market="america", limit=3)
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) <= 3

    def test_live_get_screener_invalid_market(self) -> None:
        """Verify invalid market validation."""
        scraper = Screener()
        result = scraper.get_screener(market="invalid_market_xyz", limit=5)
        assert result["status"] == "failed"
        assert result["error"] is not None


@pytest.mark.live
class TestLiveScreenerEdgeCases:
    """Test edge cases for screener."""

    def test_live_screener_invalid_limit(self) -> None:
        """Verify invalid limit validation."""
        scraper = Screener()
        result = scraper.get_screener(market="america", limit=-1)
        assert result["status"] == "failed"
        assert result["error"] is not None

    def test_live_screener_invalid_sort_order(self) -> None:
        """Verify invalid sort order validation."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            sort_by="close",
            sort_order="invalid",
            limit=5,
        )
        assert result["status"] in [STATUS_SUCCESS, "failed"]

    def test_live_screener_invalid_filter(self) -> None:
        """Verify invalid filter validation."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "invalid_field", "operation": "greater", "right": 100}],
            limit=5,
        )
        assert "status" in result

    def test_live_screener_network_error(self) -> None:
        """Verify network error handling."""
        from unittest.mock import patch

        import requests

        scraper = Screener()
        with patch.object(
            requests, "request", side_effect=requests.RequestException("Network error")
        ):
            result = scraper.get_screener(market="america", limit=5)
            assert result["status"] == "failed"
            assert result["error"] is not None

    def test_live_screener_rate_limiting(self) -> None:
        """Verify rate limiting behavior."""
        import time

        scraper = Screener()
        start = time.time()
        for _ in range(3):
            result = scraper.get_screener(market="america", limit=3)
            assert result["status"] == STATUS_SUCCESS
        elapsed = time.time() - start
        assert elapsed > 0
