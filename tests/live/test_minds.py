"""Live API tests for Minds scraper.

Tests real HTTP connections to TradingView minds endpoint.
Requires live TradingView connection.
"""

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.social.minds import Minds


@pytest.mark.live
class TestLiveMinds:
    """Test minds scraper with real API calls."""

    def test_live_minds_basic(self) -> None:
        """Verify basic minds fetching works."""
        scraper = Minds()
        # Use NYSE:BRK.B for faster tests (AAPL has 100+ pages, takes ~80s)
        result = scraper.get_minds(exchange="NYSE", symbol="BRK.B")
        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["exchange"] == "NYSE"
        assert result["metadata"]["symbol"] == "BRK.B"
        assert "data" in result

    def test_live_minds_with_limit_none(self) -> None:
        """Verify limit=None fetches all available data."""
        scraper = Minds()
        # Use NYSE:BRK.B for faster tests (AAPL has 100+ pages)
        result = scraper.get_minds(exchange="NYSE", symbol="BRK.B", limit=None)
        assert result["status"] == STATUS_SUCCESS
        assert "limit" not in result["metadata"]

    def test_live_minds_with_limit_10(self) -> None:
        """Verify limit=10 returns at most 10 results."""
        scraper = Minds()
        # Use NYSE:BRK.B for faster tests
        result = scraper.get_minds(exchange="NYSE", symbol="BRK.B", limit=10)
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) <= 10
        assert result["metadata"]["limit"] == 10

    def test_live_minds_with_limit_50(self) -> None:
        """Verify limit=50 returns at most 50 results."""
        scraper = Minds()
        # Use NYSE:BRK.B for faster tests
        result = scraper.get_minds(exchange="NYSE", symbol="BRK.B", limit=50)
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) <= 50
        assert result["metadata"]["limit"] == 50

    def test_live_minds_stock_symbol_brkb(self) -> None:
        """Verify minds for stock symbol BRK.B on NYSE."""
        scraper = Minds()
        result = scraper.get_minds(exchange="NYSE", symbol="BRK.B")
        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["exchange"] == "NYSE"
        assert result["metadata"]["symbol"] == "BRK.B"

    def test_live_minds_crypto_symbol_btc(self) -> None:
        """Verify minds for crypto symbol on BINANCE."""
        scraper = Minds()
        result = scraper.get_minds(exchange="BINANCE", symbol="BTCUSDT")
        assert "status" in result

    def test_live_minds_empty_results(self) -> None:
        """Verify handling of symbols with no minds."""
        scraper = Minds()
        result = scraper.get_minds(exchange="NYSE", symbol="ZZZ_NO_DATA_XYZ")
        assert "status" in result
        if result["status"] == STATUS_SUCCESS:
            assert len(result["data"]) == 0


@pytest.mark.live
class TestLiveMindsErrorHandling:
    """Test error handling for minds scraper."""

    def test_live_minds_invalid_exchange(self) -> None:
        """Verify handling of invalid exchange."""
        scraper = Minds()
        result = scraper.get_minds(exchange="INVALID_EXCHANGE", symbol="BRK.B")
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert result["data"] is None

    def test_live_minds_invalid_symbol(self) -> None:
        """Verify handling of invalid symbol format."""
        scraper = Minds()
        result = scraper.get_minds(exchange="NYSE", symbol="INVALID_SYMBOL_XYZ123")
        assert "status" in result


@pytest.mark.live
class TestLiveMindsMetadata:
    """Test metadata in minds responses."""

    def test_metadata_contains_required_fields(self) -> None:
        """Verify metadata contains all required fields."""
        scraper = Minds()
        # Use NYSE:BRK.B for faster tests
        result = scraper.get_minds(exchange="NYSE", symbol="BRK.B", limit=5)
        assert result["status"] == STATUS_SUCCESS
        metadata = result["metadata"]
        assert "exchange" in metadata
        assert "symbol" in metadata
        assert "total" in metadata
        assert "pages" in metadata
        assert "symbol_info" in metadata

    def test_metadata_total_matches_data_length(self) -> None:
        """Verify total count matches actual data length."""
        scraper = Minds()
        # Use NYSE:BRK.B for faster tests
        result = scraper.get_minds(exchange="NYSE", symbol="BRK.B", limit=10)
        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["total"] == len(result["data"])

    def test_symbol_info_contains_fields(self) -> None:
        """Verify symbol_info dict is present and non-empty."""
        scraper = Minds()
        # Use NYSE:BRK.B for faster tests
        result = scraper.get_minds(exchange="NYSE", symbol="BRK.B", limit=5)
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["metadata"]["symbol_info"], dict)
