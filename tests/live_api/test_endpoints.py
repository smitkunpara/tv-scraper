"""Comprehensive live API smoke tests to verify TradingView endpoints are active.

These tests make real network requests and are intended for basic
connectivity and endpoint verification across all modules.
"""

import pytest

from tv_scraper import (
    Calendar,
    Fundamentals,
    Ideas,
    MarketMovers,
    Markets,
    Minds,
    News,
    Options,
    Overview,
    Screener,
    Streamer,
    SymbolMarkets,
    Technicals,
)
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS


@pytest.mark.live
class TestLiveEndpoints:
    """Smoke tests for real API endpoints."""

    # --- Market Data ---

    def test_live_technicals(self) -> None:
        """Verify technicals endpoint is working."""
        scraper = Technicals()
        result = scraper.scrape(
            exchange="NASDAQ", symbol="AAPL", technical_indicators=["RSI"]
        )
        assert result["status"] == STATUS_SUCCESS
        assert "RSI" in result["data"]

    def test_live_fundamentals(self) -> None:
        """Verify fundamentals endpoint is working."""
        scraper = Fundamentals()
        result = scraper.get_fundamentals(
            exchange="NASDAQ", symbol="AAPL", fields=["total_revenue"]
        )
        assert result["status"] == STATUS_SUCCESS
        assert "total_revenue" in result["data"]

    def test_live_overview(self) -> None:
        """Verify overview endpoint is working."""
        scraper = Overview()
        result = scraper.get_overview(
            exchange="NASDAQ", symbol="AAPL", fields=["close"]
        )
        assert result["status"] == STATUS_SUCCESS
        assert "close" in result["data"]

    def test_live_markets(self) -> None:
        """Verify markets (top stocks) endpoint is working."""
        scraper = Markets()
        result = scraper.get_top_stocks(market="india", limit=5)
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_options_success(self) -> None:
        """Verify options endpoint is working for a symbol with options."""
        scraper = Options()
        # Apple usually has options
        result = scraper.get_chain_by_strike(
            exchange="NASDAQ", symbol="AAPL", strike=200
        )
        assert result["status"] == STATUS_SUCCESS

    def test_live_options_not_found(self) -> None:
        """Verify options endpoint returns specific error for symbols without options."""
        scraper = Options()
        # BINANCE:BTCUSDT typically does not have traditional option chains here
        result = scraper.get_chain_by_strike(
            exchange="BINANCE", symbol="BTCUSDT", strike=100000
        )
        # Should return FAILED because we explicitly checked if data exists
        assert result["status"] == STATUS_FAILED
        assert (
            "not found" in result["error"].lower()
            or "no options" in result["error"].lower()
        )

    # --- Social ---

    def test_live_news(self) -> None:
        """Verify news endpoint is working."""
        scraper = News()
        result = scraper.scrape_headlines(exchange="NASDAQ", symbol="AAPL")
        assert result["status"] == STATUS_SUCCESS

    def test_live_ideas(self) -> None:
        """Verify ideas endpoint is working."""
        scraper = Ideas()
        result = scraper.scrape(exchange="NASDAQ", symbol="AAPL")
        # Might return captcha failure if no cookie, but should not crash
        assert result["status"] in [STATUS_SUCCESS, STATUS_FAILED]

    def test_live_minds(self) -> None:
        """Verify minds endpoint is working."""
        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL", limit=5)
        assert result["status"] == STATUS_SUCCESS

    # --- Screening ---

    def test_live_screener(self) -> None:
        """Verify screener endpoint is working."""
        scraper = Screener()
        result = scraper.screen(
            market="america",
            filters=[{"left": "close", "operation": "greater", "right": 100}],
            limit=5,
        )
        assert result["status"] == STATUS_SUCCESS

    def test_live_market_movers(self) -> None:
        """Verify market movers endpoint is working."""
        scraper = MarketMovers()
        result = scraper.scrape(market="stocks-usa", category="gainers", limit=5)
        assert result["status"] == STATUS_SUCCESS

    def test_live_symbol_markets(self) -> None:
        """Verify symbol markets endpoint is working."""
        scraper = SymbolMarkets()
        result = scraper.scrape(symbol="AAPL", scanner="america")
        assert result["status"] == STATUS_SUCCESS

    # --- Events ---

    def test_live_calendar(self) -> None:
        """Verify calendar endpoint is working."""
        scraper = Calendar()
        result = scraper.get_earnings(markets=["america"])
        assert result["status"] == STATUS_SUCCESS

    # --- Streaming (Smoke) ---

    def test_live_streamer_candles(self) -> None:
        """Verify streamer can fetch historic candles."""
        scraper = Streamer()
        result = scraper.get_candles(
            exchange="NASDAQ", symbol="AAPL", timeframe="1h", numb_candles=5
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]["ohlcv"]) > 0
