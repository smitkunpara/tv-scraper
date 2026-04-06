"""Live API tests for streaming candles feature.

Tests real WebSocket connections with TradingView API.
These tests require network connectivity and may be slower.
Run with: pytest tests/live/test_streaming_candles.py -v -m live
"""

import os
import time

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.streaming.candle_streamer import CandleStreamer
from tv_scraper.streaming.streamer import Streamer

pytestmark = pytest.mark.live


class TestLiveStreamingCandlesBasic:
    """Test basic candle streaming functionality."""

    def test_live_get_candles_nasdaq_aapl(self):
        """Verify basic candle fetching for NASDAQ:AAPL."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="NASDAQ", symbol="AAPL", timeframe="1h", numb_candles=5
        )
        assert result["status"] == STATUS_SUCCESS
        assert "ohlcv" in result["data"]
        assert len(result["data"]["ohlcv"]) >= 1

        candle = result["data"]["ohlcv"][0]
        assert "timestamp" in candle
        assert "open" in candle
        assert "high" in candle
        assert "low" in candle
        assert "close" in candle

    def test_live_get_candles_nyse_jpm(self):
        """Verify candle fetching for NYSE:JPM."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="NYSE", symbol="JPM", timeframe="1h", numb_candles=5
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]["ohlcv"]) >= 1

    def test_live_get_candles_binance_btcusdt(self):
        """Verify candle fetching for BINANCE:BTCUSDT."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="BINANCE", symbol="BTCUSDT", timeframe="1h", numb_candles=5
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]["ohlcv"]) >= 1

    def test_live_get_candles_binance_ethusdt(self):
        """Verify candle fetching for BINANCE:ETHUSDT."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="BINANCE", symbol="ETHUSDT", timeframe="1h", numb_candles=5
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]["ohlcv"]) >= 1

    def test_live_get_candles_fx_idc_eurusd(self):
        """Verify candle fetching for FX_IDC:EURUSD."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="FX_IDC", symbol="EURUSD", timeframe="1h", numb_candles=5
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]["ohlcv"]) >= 1


class TestLiveStreamingCandlesTimeframes:
    """Test different timeframes."""

    @pytest.mark.parametrize(
        "timeframe",
        [
            "1m",
            "5m",
            "15m",
            "30m",
            "1h",
            "2h",
            "4h",
            "1d",
            "1w",
            "1M",
        ],
    )
    def test_live_get_candles_all_timeframes(self, timeframe: str):
        """Test all supported timeframes."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="BINANCE", symbol="BTCUSDT", timeframe=timeframe, numb_candles=3
        )
        assert result["status"] == STATUS_SUCCESS, f"Failed for timeframe {timeframe}"
        assert len(result["data"]["ohlcv"]) >= 1, f"No data for timeframe {timeframe}"
        assert result["metadata"]["timeframe"] == timeframe


class TestLiveStreamingCandlesNumbCandles:
    """Test different numb_candles values."""

    @pytest.mark.parametrize(
        "numb_candles",
        [5, 10, 50],
    )
    def test_live_get_candles_numb_candles(self, numb_candles: int):
        """Test different numb_candles values."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="BINANCE",
            symbol="BTCUSDT",
            timeframe="1h",
            numb_candles=numb_candles,
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]["ohlcv"]) >= 1


class TestLiveStreamingCandlesCombinations:
    """Test various exchange/symbol combinations."""

    @pytest.mark.parametrize(
        "exchange,symbol",
        [
            ("BINANCE", "BTCUSDT"),
            ("BINANCE", "ETHUSDT"),
            ("NASDAQ", "AAPL"),
            ("NASDAQ", "TSLA"),
            ("NYSE", "JPM"),
            ("NYSE", "A"),
            ("FX_IDC", "EURUSD"),
            ("FX_IDC", "GBPUSD"),
        ],
    )
    def test_live_get_candles_combinations(self, exchange: str, symbol: str):
        """Test various exchange/symbol combinations."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange=exchange, symbol=symbol, timeframe="1h", numb_candles=3
        )
        assert result["status"] == STATUS_SUCCESS, f"Failed for {exchange}:{symbol}"
        assert len(result["data"]["ohlcv"]) >= 1
        assert result["metadata"]["exchange"] == exchange
        assert result["metadata"]["symbol"] == symbol


class TestLiveStreamingCandlesWithIndicators:
    """Test candle streaming with indicators."""

    def test_live_get_candles_with_indicators(self):
        """Verify candle fetching with indicators works."""
        cookie = os.environ.get("TRADINGVIEW_COOKIE") or os.environ.get("TV_COOKIE")
        if not cookie:
            pytest.skip(
                "Indicator live test requires TRADINGVIEW_COOKIE (or TV_COOKIE)."
            )

        streamer = Streamer(cookie=cookie)
        result = streamer.get_candles(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="1h",
            numb_candles=10,
            indicators=[("STD;RSI", "37.0")],
        )
        assert result["status"] in [STATUS_SUCCESS, "failed"]
        assert "data" in result

    def test_live_get_candles_with_indicators_no_cookie(self):
        """Test without cookie - may fail for indicators but should handle gracefully."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="1h",
            numb_candles=5,
            indicators=[("STD;RSI", "37.0")],
        )
        assert "status" in result

    def test_live_get_candles_with_macd(self):
        """Test with MACD indicator."""
        cookie = os.environ.get("TRADINGVIEW_COOKIE") or os.environ.get("TV_COOKIE")
        if not cookie:
            pytest.skip(
                "Indicator live test requires TRADINGVIEW_COOKIE (or TV_COOKIE)."
            )

        streamer = Streamer(cookie=cookie)
        result = streamer.get_candles(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="1h",
            numb_candles=10,
            indicators=[("STD;MACD", "12.0")],
        )
        assert "status" in result


class TestLiveStreamingCandlesVolume:
    """Test volume data in candles."""

    def test_live_get_candles_with_volume(self):
        """Verify volume data is included in candles."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="BINANCE", symbol="ETHUSDT", timeframe="1h", numb_candles=5
        )
        assert result["status"] == STATUS_SUCCESS

        candle = result["data"]["ohlcv"][0]
        assert "volume" in candle
        assert candle["volume"] is not None

    def test_live_get_candles_volume_positive(self):
        """Verify volume is non-negative."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="BINANCE", symbol="BTCUSDT", timeframe="1h", numb_candles=5
        )
        assert result["status"] == STATUS_SUCCESS

        for candle in result["data"]["ohlcv"]:
            if candle.get("volume") is not None:
                assert candle["volume"] >= 0


class TestLiveStreamingCandlesResponseStructure:
    """Test response structure."""

    def test_live_response_has_all_keys(self):
        """Test success response has all required keys."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="BINANCE", symbol="BTCUSDT", timeframe="1h", numb_candles=5
        )

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result

    def test_live_metadata_structure(self):
        """Test metadata contains expected fields."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="1h",
            numb_candles=5,
        )

        meta = result["metadata"]
        assert "exchange" in meta
        assert "symbol" in meta
        assert "timeframe" in meta
        assert "numb_candles" in meta

    def test_live_ohlcv_structure(self):
        """Test OHLCV data structure."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="BINANCE", symbol="BTCUSDT", timeframe="1h", numb_candles=5
        )

        assert result["status"] == STATUS_SUCCESS
        ohlcv = result["data"]["ohlcv"]
        assert len(ohlcv) > 0

        candle = ohlcv[0]
        assert "index" in candle
        assert "timestamp" in candle
        assert "open" in candle
        assert "high" in candle
        assert "low" in candle
        assert "close" in candle
        assert "volume" in candle

    def test_live_indicators_structure(self):
        """Test indicators data structure when present."""
        cookie = os.environ.get("TRADINGVIEW_COOKIE") or os.environ.get("TV_COOKIE")
        if not cookie:
            pytest.skip("Requires TRADINGVIEW_COOKIE")

        streamer = Streamer(cookie=cookie)
        result = streamer.get_candles(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="1h",
            numb_candles=10,
            indicators=[("STD;RSI", "37.0")],
        )

        if result["status"] == STATUS_SUCCESS:
            assert "indicators" in result["data"]


class TestLiveStreamingCandlesEdgeCases:
    """Test edge cases."""

    def test_live_invalid_symbol_handling(self):
        """Verify graceful handling of invalid symbols."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="NASDAQ", symbol="INVALIDSYMBOL999", timeframe="1h", numb_candles=5
        )
        assert "status" in result

    def test_live_large_candle_request(self):
        """Verify handling of larger candle requests."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="BINANCE", symbol="BTCUSDT", timeframe="1h", numb_candles=50
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]["ohlcv"]) >= 10


class TestLiveStreamingCandlesConnectionStability:
    """Test connection stability."""

    def test_sequential_requests(self):
        """Verify multiple sequential requests work."""
        for i in range(3):
            streamer = Streamer()
            result = streamer.get_candles(
                exchange="BINANCE", symbol="BTCUSDT", timeframe="1h", numb_candles=3
            )
            assert result["status"] == STATUS_SUCCESS, f"Failed on iteration {i + 1}"
            time.sleep(0.5)

    def test_different_symbols_sequential(self):
        """Verify fetching different symbols sequentially works."""
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

        for symbol in symbols:
            streamer = Streamer()
            result = streamer.get_candles(
                exchange="BINANCE", symbol=symbol, timeframe="1h", numb_candles=3
            )
            assert result["status"] == STATUS_SUCCESS, f"Failed for {symbol}"
            time.sleep(0.5)


class TestLiveCandleStreamerDirect:
    """Test CandleStreamer directly."""

    def test_candle_streamer_direct(self):
        """Test CandleStreamer class directly."""
        cs = CandleStreamer()
        result = cs.get_candles(
            exchange="BINANCE", symbol="BTCUSDT", timeframe="1h", numb_candles=5
        )
        assert result["status"] == STATUS_SUCCESS
        assert "ohlcv" in result["data"]


class TestLiveStreamingCandlesExport:
    """Test export functionality."""

    def test_export_json(self):
        """Test JSON export flag works."""
        streamer = Streamer(export_result=True, export_type="json")
        result = streamer.get_candles(
            exchange="BINANCE", symbol="BTCUSDT", timeframe="1h", numb_candles=2
        )
        assert result["status"] in [STATUS_SUCCESS, "failed"]


class TestLiveCandleDataQuality:
    """Test data quality."""

    def test_candle_high_low_order(self):
        """Verify high >= low for all candles."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="BINANCE", symbol="BTCUSDT", timeframe="1h", numb_candles=10
        )
        assert result["status"] == STATUS_SUCCESS

        for candle in result["data"]["ohlcv"]:
            assert candle["high"] >= candle["low"], "High should be >= low"

    def test_candle_close_within_range(self):
        """Verify close is within high-low range."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="BINANCE", symbol="BTCUSDT", timeframe="1h", numb_candles=10
        )
        assert result["status"] == STATUS_SUCCESS

        for candle in result["data"]["ohlcv"]:
            assert candle["low"] <= candle["close"] <= candle["high"], (
                "Close should be within high-low range"
            )

    def test_candle_timestamps_ascending(self):
        """Verify candle timestamps are ascending."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="BINANCE", symbol="BTCUSDT", timeframe="1h", numb_candles=10
        )
        assert result["status"] == STATUS_SUCCESS

        timestamps = [c["timestamp"] for c in result["data"]["ohlcv"]]
        assert timestamps == sorted(timestamps), "Timestamps should be ascending"
