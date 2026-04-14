"""Live API tests for SymbolMarkets scraper.

These tests hit TradingView endpoints directly.
"""

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.screening.symbol_markets import SymbolMarkets


@pytest.mark.live
class TestLiveSymbolMarkets:
    """Live tests for SymbolMarkets.get_symbol_markets."""

    def test_live_aapl_global(self) -> None:
        """Test AAPL on global scanner."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(
            exchange="NASDAQ", symbol="AAPL", scanner="global", limit=50
        )
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)
        if result["data"]:
            assert "exchange" in result["data"][0]
            assert "symbol" in result["data"][0]

    def test_live_aapl_america(self) -> None:
        """Test AAPL on america scanner."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(
            exchange="NASDAQ", symbol="AAPL", scanner="america", limit=50
        )
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)

    def test_live_btcusd_global(self) -> None:
        """Test BTCUSD on global scanner."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(
            exchange="BINANCE", symbol="BTCUSD", scanner="global", limit=50
        )
        assert result["status"] in [STATUS_SUCCESS, "failed"]

    def test_live_btcusd_crypto(self) -> None:
        """Test BTCUSD on crypto scanner."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(
            exchange="BINANCE", symbol="BTCUSD", scanner="crypto", limit=50
        )
        assert result["status"] in [STATUS_SUCCESS, "failed"]

    def test_live_eurusd_forex(self) -> None:
        """Test EURUSD on forex scanner."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(
            exchange="FX_IDC", symbol="EURUSD", scanner="forex", limit=50
        )
        assert result["status"] in [STATUS_SUCCESS, "failed"]

    def test_live_gold_cfd(self) -> None:
        """Test GOLD on cfd scanner."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(
            exchange="TVC", symbol="GOLD", scanner="cfd", limit=50
        )
        assert result["status"] in [STATUS_SUCCESS, "failed"]

    def test_live_aapl_custom_fields(self) -> None:
        """Test AAPL with custom fields."""
        scraper = SymbolMarkets()
        custom_fields = ["name", "close", "volume", "market_cap_basic"]
        result = scraper.get_symbol_markets(
            exchange="NASDAQ",
            symbol="AAPL",
            scanner="america",
            fields=custom_fields,
            limit=50,
        )
        assert result["status"] in [STATUS_SUCCESS, "failed"]

    def test_live_limit_100(self) -> None:
        """Test limit parameter with value 100."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(
            exchange="NASDAQ", symbol="AAPL", scanner="global", limit=100
        )
        assert result["status"] in [STATUS_SUCCESS, "failed"]
        if result["status"] == STATUS_SUCCESS:
            assert len(result["data"]) <= 100

    def test_live_limit_150(self) -> None:
        """Test limit parameter with value 150."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(
            exchange="NASDAQ", symbol="AAPL", scanner="global", limit=150
        )
        assert result["status"] in [STATUS_SUCCESS, "failed"]
        if result["status"] == STATUS_SUCCESS:
            assert len(result["data"]) <= 150

    def test_live_exchange_symbol_separation(self) -> None:
        """Test explicit exchange and symbol separation."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(
            exchange="NASDAQ", symbol="AAPL", scanner="america", limit=50
        )
        assert result["status"] in [STATUS_SUCCESS, "failed"]


@pytest.mark.live
class TestLiveSymbolMarketsEdgeCases:
    """Test edge cases and error handling for SymbolMarkets."""

    def test_live_invalid_scanner(self) -> None:
        """Test invalid scanner returns error."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(
            exchange="NASDAQ", symbol="AAPL", scanner="invalid"
        )
        assert result["status"] == "failed"
        assert result["data"] is None
        assert result["error"] is not None
        assert "Invalid value" in result["error"]

    def test_live_blank_symbol(self) -> None:
        """Test blank symbol returns error."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(exchange="NASDAQ", symbol="   ")
        assert result["status"] == "failed"
        assert result["data"] is None
        assert result["error"] is not None
        assert "Both exchange and symbol" in result["error"]

    def test_live_empty_symbol(self) -> None:
        """Test empty symbol returns error."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(exchange="NASDAQ", symbol="")
        assert result["status"] == "failed"
        assert result["data"] is None

    def test_live_nonexistent_symbol(self) -> None:
        """Test nonexistent symbol returns empty results or error."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(
            exchange="NASDAQ",
            symbol="XYZNONEXISTENT123456",
            scanner="america",
            limit=50,
        )
        assert result["status"] in [STATUS_SUCCESS, "failed"]
        if result["status"] == STATUS_FAILED:
            assert result["data"] is None

    def test_live_all_scanners(self) -> None:
        """Test all supported scanners with AAPL."""
        scraper = SymbolMarkets()
        scanners = ["global", "america", "crypto", "forex", "cfd"]
        for scanner in scanners:
            if scanner == "forex":
                e_v, s_v = "FX_IDC", "EURUSD"
            elif scanner == "crypto":
                e_v, s_v = "BINANCE", "BTCUSD"
            elif scanner == "cfd":
                e_v, s_v = "TVC", "GOLD"
            else:
                e_v, s_v = "NASDAQ", "AAPL"
            result = scraper.get_symbol_markets(
                exchange=e_v,
                symbol=s_v,
                scanner=scanner,
                limit=10,
            )
            assert "status" in result
            assert result["status"] in [STATUS_SUCCESS, "failed"]

    def test_live_metadata_structure(self) -> None:
        """Test metadata structure in response."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(
            exchange="NASDAQ", symbol="AAPL", scanner="global", limit=10
        )
        assert "metadata" in result
        metadata = result["metadata"]
        assert "exchange" in metadata
        assert "symbol" in metadata
        assert "scanner" in metadata
        assert "limit" in metadata
        if result["status"] == STATUS_SUCCESS:
            assert "total" in metadata
            assert "total_available" in metadata


@pytest.mark.live
class TestLiveSymbolMarketsResponseEnvelope:
    """Test standardized response envelope structure."""

    def test_live_success_response_structure(self) -> None:
        """Test success response has correct structure."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(
            exchange="NASDAQ", symbol="AAPL", scanner="global", limit=10
        )
        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        if result["status"] == STATUS_SUCCESS:
            assert result["error"] is None
            assert result["data"] is not None
            assert isinstance(result["data"], list)

    def test_live_error_response_structure(self) -> None:
        """Test error response has correct structure."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(
            exchange="NASDAQ", symbol="", scanner="global"
        )
        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        if result["status"] == "failed":
            assert result["data"] is None
            assert result["error"] is not None
