"""Live API tests for Technicals scraper.

These tests hit TradingView endpoints directly with no mocks.
"""

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.market_data.technicals import Technicals


@pytest.mark.live
class TestLiveTechnicals:
    """Live tests for Technicals.get_technicals."""

    def test_live_nasdaq_aapl_rsi(self) -> None:
        """Test NASDAQ:AAPL with RSI indicator."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert isinstance(result["data"], dict)
        assert "RSI" in result["data"]

    def test_live_binance_btcusdt_rsi(self) -> None:
        """Test BINANCE:BTCUSDT with RSI indicator."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="BINANCE",
            symbol="BTCUSDT",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert isinstance(result["data"], dict)
        assert "RSI" in result["data"]

    def test_live_nasdaq_aapl_rsi_macd(self) -> None:
        """Test NASDAQ:AAPL with RSI and MACD indicators."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI", "MACD.macd"],
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert "RSI" in result["data"]
        assert "MACD.macd" in result["data"]

    def test_live_binance_btcusdt_rsi_macd(self) -> None:
        """Test BINANCE:BTCUSDT with RSI and MACD indicators."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="BINANCE",
            symbol="BTCUSDT",
            technical_indicators=["RSI", "MACD.macd"],
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert "RSI" in result["data"]
        assert "MACD.macd" in result["data"]

    def test_live_all_indicators(self) -> None:
        """Test fetching all indicators."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            all_indicators=True,
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert isinstance(result["data"], dict)
        assert len(result["data"]) > 20


@pytest.mark.live
class TestLiveTechnicalsTimeframes:
    """Test various timeframes with real API."""

    def test_live_timeframe_1m(self) -> None:
        """Test timeframe 1m."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="1m",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert result["metadata"]["timeframe"] == "1m"

    def test_live_timeframe_5m(self) -> None:
        """Test timeframe 5m."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="5m",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert result["metadata"]["timeframe"] == "5m"

    def test_live_timeframe_15m(self) -> None:
        """Test timeframe 15m."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="15m",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert result["metadata"]["timeframe"] == "15m"

    def test_live_timeframe_30m(self) -> None:
        """Test timeframe 30m."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="30m",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert result["metadata"]["timeframe"] == "30m"

    def test_live_timeframe_1h(self) -> None:
        """Test timeframe 1h."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="1h",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert result["metadata"]["timeframe"] == "1h"

    def test_live_timeframe_4h(self) -> None:
        """Test timeframe 4h."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="4h",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert result["metadata"]["timeframe"] == "4h"

    def test_live_timeframe_1d(self) -> None:
        """Test timeframe 1d."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="1d",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert result["metadata"]["timeframe"] == "1d"

    def test_live_timeframe_1w(self) -> None:
        """Test timeframe 1w."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="1w",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert result["metadata"]["timeframe"] == "1w"

    def test_live_timeframe_1m_monthly(self) -> None:
        """Test timeframe 1M (monthly)."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="1M",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert result["metadata"]["timeframe"] == "1M"


@pytest.mark.live
class TestLiveTechnicalsCombinations:
    """Test various parameter combinations."""

    def test_live_nasdaq_aapl_all_timeframes(self):
        """Test NASDAQ:AAPL across all timeframes."""
        scraper = Technicals()
        timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"]

        for tf in timeframes:
            result = scraper.get_technicals(
                exchange="NASDAQ",
                symbol="AAPL",
                timeframe=tf,
                technical_indicators=["RSI"],
            )
            assert result["status"] == STATUS_SUCCESS, (
                f"Failed for {tf}: {result.get('error')}"
            )
            assert result["metadata"]["timeframe"] == tf

    def test_live_binance_btcusdt_all_timeframes(self):
        """Test BINANCE:BTCUSDT across all timeframes."""
        scraper = Technicals()
        timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"]

        for tf in timeframes:
            result = scraper.get_technicals(
                exchange="BINANCE",
                symbol="BTCUSDT",
                timeframe=tf,
                technical_indicators=["RSI"],
            )
            assert result["status"] == STATUS_SUCCESS, (
                f"Failed for {tf}: {result.get('error')}"
            )
            assert result["metadata"]["timeframe"] == tf

    def test_live_nasdaq_aapl_multiple_indicators(self):
        """Test NASDAQ:AAPL with multiple indicators."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI", "MACD.macd", "Stoch.K", "CCI20"],
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert "RSI" in result["data"]
        assert "MACD.macd" in result["data"]
        assert "Stoch.K" in result["data"]
        assert "CCI20" in result["data"]


@pytest.mark.live
class TestLiveTechnicalsErrorHandling:
    """Test error handling with real API."""

    def test_live_invalid_indicator(self):
        """Test invalid indicator returns error."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["INVALID_INDICATOR_XYZ"],
        )

        assert result["status"] == "failed"
        assert result["data"] is None
        assert result["error"] is not None

    def test_live_invalid_timeframe(self):
        """Test invalid timeframe returns error."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="13h",  # type: ignore[arg-type]
            technical_indicators=["RSI"],
        )

        assert result["status"] == "failed"
        assert result["data"] is None
        assert result["error"] is not None

    def test_live_no_indicators_provided(self):
        """Test no indicators provided returns error."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=None,
            all_indicators=False,
        )

        assert result["status"] == "failed"
        assert result["data"] is None
        assert "No indicators provided" in result["error"]

    def test_live_empty_indicators_list(self):
        """Test empty indicators list returns error."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=[],
        )

        assert result["status"] == "failed"
        assert result["data"] is None


@pytest.mark.live
class TestLiveTechnicalsFieldsFiltering:
    """Test fields filtering with real API."""

    def test_live_fields_filtering(self):
        """Test fields parameter filters output."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI", "MACD.macd", "Stoch.K"],
            fields=["RSI", "MACD.macd"],
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert "RSI" in result["data"]
        assert "MACD.macd" in result["data"]


@pytest.mark.live
class TestLiveTechnicalsMetadata:
    """Test metadata in live responses."""

    def test_live_metadata_contains_all_params(self):
        """Test metadata contains all input parameters."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="4h",
            technical_indicators=["RSI", "MACD.macd"],
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        meta = result["metadata"]
        assert meta["exchange"] == "NASDAQ"
        assert meta["symbol"] == "AAPL"
        assert meta["timeframe"] == "4h"
        assert meta["all_indicators"] is False
        assert meta["technical_indicators"] == ["RSI", "MACD.macd"]

    def test_live_metadata_all_indicators_mode(self):
        """Test metadata for all_indicators mode."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            all_indicators=True,
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        meta = result["metadata"]
        assert meta["all_indicators"] is True
        assert "technical_indicators" not in meta


@pytest.mark.live
class TestLiveTechnicalsResponseEnvelope:
    """Test standardized response envelope with real API."""

    def test_live_success_has_all_keys(self):
        """Test success response has required keys."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI"],
        )

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None

    def test_live_error_has_all_keys(self):
        """Test error response has required keys."""
        scraper = Technicals()
        result = scraper.get_technicals(
            exchange="INVALID_EXCHANGE",
            symbol="INVALID",
            technical_indicators=["RSI"],
        )

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == "failed"
        assert result["data"] is None
        assert result["error"] is not None
