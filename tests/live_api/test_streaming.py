"""Comprehensive live API tests for streaming functionality.

These tests verify real-time WebSocket connections and data streaming
with the TradingView platform. They use actual network connections.
"""

import time
from typing import Any, Dict

import pytest

from tv_scraper import Streamer, RealTimeData
from tv_scraper.core.constants import STATUS_SUCCESS


@pytest.mark.live
class TestLiveStreamer:
    """Live tests for Streamer class with real WebSocket connections."""

    # --- Historical Candles ---

    def test_live_get_candles_basic(self) -> None:
        """Verify basic candle fetching works."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="1h",
            numb_candles=5
        )
        assert result["status"] == STATUS_SUCCESS
        assert "ohlcv" in result["data"]
        assert len(result["data"]["ohlcv"]) >= 1
        
        # Verify OHLCV structure
        candle = result["data"]["ohlcv"][0]
        assert "timestamp" in candle
        assert "open" in candle
        assert "high" in candle
        assert "low" in candle
        assert "close" in candle

    def test_live_get_candles_multiple_timeframes(self) -> None:
        """Verify candle fetching works across different timeframes."""
        timeframes = ["1m", "5m", "15m", "1h", "1d"]
        
        for tf in timeframes:
            # Create new streamer for each timeframe (WebSocket closes after use)
            streamer = Streamer()
            result = streamer.get_candles(
                exchange="BINANCE",
                symbol="BTCUSDT",
                timeframe=tf,
                numb_candles=3
            )
            assert result["status"] == STATUS_SUCCESS, f"Failed for timeframe {tf}"
            assert len(result["data"]["ohlcv"]) >= 1, f"No data for timeframe {tf}"

    def test_live_get_candles_with_volume(self) -> None:
        """Verify volume data is included in candles."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="BINANCE",
            symbol="ETHUSDT",
            timeframe="1h",
            numb_candles=5
        )
        assert result["status"] == STATUS_SUCCESS
        
        # Check volume is present
        candle = result["data"]["ohlcv"][0]
        assert "volume" in candle
        assert candle["volume"] is not None
        assert candle["volume"] >= 0

    @pytest.mark.skip(reason="Requires JWT token and can hang - indicator fetching needs authentication")
    def test_live_get_candles_with_indicators(self) -> None:
        """Verify candle fetching with indicators works."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="NASDAQ",
            symbol="TSLA",
            timeframe="1h",
            numb_candles=10,
            indicators=[("STD;RSI", "37.0")]
        )
        assert result["status"] == STATUS_SUCCESS
        assert "ohlcv" in result["data"]
        assert "indicators" in result["data"]
        # Note: Indicator data might not always be present depending on subscription
        # Just verify the structure is correct

    def test_live_get_candles_crypto(self) -> None:
        """Verify candle fetching works for crypto exchanges."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="BINANCE",
            symbol="BTCUSDT",
            timeframe="5m",
            numb_candles=5
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]["ohlcv"]) >= 1

    def test_live_get_candles_indian_market(self) -> None:
        """Verify candle fetching works for Indian market."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="NSE",
            symbol="NIFTY",
            timeframe="1h",
            numb_candles=5
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]["ohlcv"]) >= 1

    def test_live_get_candles_forex(self) -> None:
        """Verify candle fetching works for forex pairs."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="FX_IDC",
            symbol="EURUSD",
            timeframe="1h",
            numb_candles=5
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]["ohlcv"]) >= 1

    # --- Real-Time Price Streaming ---

    def test_live_stream_realtime_price_basic(self) -> None:
        """Verify real-time price streaming receives updates."""
        streamer = Streamer()
        gen = streamer.stream_realtime_price(exchange="BINANCE", symbol="BTCUSDT")
        
        # Collect first 3 updates or timeout after 30 seconds
        updates: list[Dict[str, Any]] = []
        start_time = time.time()
        timeout = 30
        
        for update in gen:
            updates.append(update)
            if len(updates) >= 3:
                break
            if time.time() - start_time > timeout:
                break
        
        # Should have received at least one update
        assert len(updates) >= 1, "No updates received within timeout"
        
        # Verify structure of first update
        first_update = updates[0]
        assert "price" in first_update
        assert "symbol" in first_update
        assert "exchange" in first_update
        assert first_update["price"] is not None
        assert first_update["price"] > 0

    def test_live_stream_realtime_price_indian_market(self) -> None:
        """Verify real-time streaming works for Indian market (NSE)."""
        streamer = Streamer()
        gen = streamer.stream_realtime_price(exchange="NSE", symbol="NIFTY")
        
        updates = []
        start_time = time.time()
        timeout = 30
        
        for update in gen:
            updates.append(update)
            if len(updates) >= 2:
                break
            if time.time() - start_time > timeout:
                break
        
        assert len(updates) >= 1, "No updates received for NSE:NIFTY"
        
        # Verify data structure
        update = updates[0]
        assert update["price"] is not None
        assert update["symbol"] == "NIFTY" or "NIFTY" in str(update["symbol"])

    def test_live_stream_realtime_price_data_quality(self) -> None:
        """Verify streaming data contains expected fields."""
        streamer = Streamer()
        gen = streamer.stream_realtime_price(exchange="NASDAQ", symbol="AAPL")
        
        update = next(gen)
        
        # Required fields
        assert "price" in update
        assert "symbol" in update
        assert "exchange" in update
        
        # Optional fields (may or may not be present)
        optional_fields = ["volume", "change", "change_percent", "high", "low", "open"]
        # Just verify they exist in the dict even if None
        for field in optional_fields:
            assert field in update

    def test_live_stream_realtime_price_update_frequency(self) -> None:
        """Verify streaming receives updates at reasonable frequency."""
        streamer = Streamer()
        gen = streamer.stream_realtime_price(exchange="BINANCE", symbol="ETHUSDT")
        
        update_times = []
        start_time = time.time()
        timeout = 30
        target_updates = 3
        
        for update in gen:
            update_times.append(time.time())
            if len(update_times) >= target_updates:
                break
            if time.time() - start_time > timeout:
                break
        
        # Should receive at least 2 updates within timeout
        assert len(update_times) >= 2, "Insufficient updates received"
        
        # Calculate average time between updates
        if len(update_times) >= 2:
            intervals = [update_times[i+1] - update_times[i] for i in range(len(update_times)-1)]
            avg_interval = sum(intervals) / len(intervals)
            
            # Updates should come within reasonable time (< 15 seconds on average)
            assert avg_interval < 15, f"Updates too slow: {avg_interval:.1f}s average interval"

    def test_live_stream_handles_qsd_and_du_messages(self) -> None:
        """Verify streaming handles both QSD and DU message types."""
        streamer = Streamer()
        gen = streamer.stream_realtime_price(exchange="BINANCE", symbol="BTCUSDT")
        
        # Collect multiple updates to get both message types
        updates = []
        start_time = time.time()
        timeout = 45  # Longer timeout to catch both message types
        
        for update in gen:
            if update["price"] is not None:
                updates.append(update)
            if len(updates) >= 5:
                break
            if time.time() - start_time > timeout:
                break
        
        # Should have received multiple updates
        assert len(updates) >= 2, "Not enough updates to test message diversity"
        
        # All updates should have valid prices
        for update in updates:
            assert update["price"] > 0, "Invalid price in update"


@pytest.mark.live
class TestLiveRealTimeData:
    """Live tests for RealTimeData class."""

    def test_live_get_ohlcv_basic(self) -> None:
        """Verify RealTimeData.get_ohlcv() works."""
        rt = RealTimeData()
        gen = rt.get_ohlcv(exchange="BINANCE", symbol="BTCUSDT")
        
        # Get first packet or timeout
        packet_found = False
        start_time = time.time()
        timeout = 20
        
        for packet in gen:
            if packet and isinstance(packet, dict):
                packet_found = True
                break
            if time.time() - start_time > timeout:
                break
        
        assert packet_found, "No packets received from get_ohlcv"

    def test_live_get_latest_trade_info_basic(self) -> None:
        """Verify RealTimeData.get_latest_trade_info() works for multiple symbols."""
        rt = RealTimeData()
        gen = rt.get_latest_trade_info(
            exchanges=["BINANCE", "NASDAQ"],
            symbols=["BTCUSDT", "AAPL"]
        )
        
        # Get first packet or timeout
        packet_found = False
        start_time = time.time()
        timeout = 20
        
        for packet in gen:
            if packet and isinstance(packet, dict):
                packet_found = True
                break
            if time.time() - start_time > timeout:
                break
        
        assert packet_found, "No packets received from get_latest_trade_info"


@pytest.mark.live
class TestLiveStreamingCombinations:
    """Test various combinations of streaming parameters."""

    def test_multiple_exchanges(self) -> None:
        """Test streaming from different exchanges."""
        exchanges_symbols = [
            ("NASDAQ", "AAPL"),
            ("BINANCE", "BTCUSDT"),
            ("NSE", "NIFTY"),
        ]
        
        for exchange, symbol in exchanges_symbols:
            # Create new streamer for each test (WebSocket closes after use)
            streamer = Streamer()
            result = streamer.get_candles(
                exchange=exchange,
                symbol=symbol,
                timeframe="1h",
                numb_candles=3
            )
            assert result["status"] == STATUS_SUCCESS, f"Failed for {exchange}:{symbol}"
            assert len(result["data"]["ohlcv"]) >= 1, f"No data for {exchange}:{symbol}"

    def test_various_crypto_symbols(self) -> None:
        """Test streaming various cryptocurrency pairs."""
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        
        for symbol in symbols:
            # Create new streamer for each test (WebSocket closes after use)
            streamer = Streamer()
            result = streamer.get_candles(
                exchange="BINANCE",
                symbol=symbol,
                timeframe="5m",
                numb_candles=3
            )
            assert result["status"] == STATUS_SUCCESS, f"Failed for {symbol}"
            assert len(result["data"]["ohlcv"]) >= 1, f"No data for {symbol}"

    def test_export_functionality(self) -> None:
        """Test that export_result flag works without errors."""
        import os
        import glob
        
        streamer = Streamer(export_result=True, export_type="json")
        
        # Clean up any existing test exports
        test_files = glob.glob("export/*_test_export_*.json")
        for f in test_files:
            try:
                os.remove(f)
            except:
                pass
        
        result = streamer.get_candles(
            exchange="BINANCE",
            symbol="TEST_EXPORT",  # Use unique symbol name
            timeframe="1h",
            numb_candles=2
        )
        
        # Even if it fails, export mechanism should not crash
        assert result["status"] in [STATUS_SUCCESS, "failed"]


@pytest.mark.live
class TestLiveStreamingEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_symbol_handling(self) -> None:
        """Verify graceful handling of invalid symbols."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="NASDAQ",
            symbol="INVALIDSYMBOL999",
            timeframe="1h",
            numb_candles=5
        )
        
        # Should return error response, not crash
        assert "status" in result
        # May succeed or fail depending on validation

    def test_large_candle_request(self) -> None:
        """Verify handling of larger candle requests."""
        streamer = Streamer()
        result = streamer.get_candles(
            exchange="BINANCE",
            symbol="BTCUSDT",
            timeframe="1h",
            numb_candles=50
        )
        
        assert result["status"] == STATUS_SUCCESS
        # May not get all 50 but should get some
        assert len(result["data"]["ohlcv"]) >= 10

    def test_connection_stability(self) -> None:
        """Verify multiple sequential requests work."""
        for i in range(3):
            # Create new streamer for each iteration (WebSocket closes after use)
            streamer = Streamer()
            result = streamer.get_candles(
                exchange="BINANCE",
                symbol="BTCUSDT",
                timeframe="1h",
                numb_candles=3
            )
            assert result["status"] == STATUS_SUCCESS, f"Failed on iteration {i+1}"
            
            # Small delay between requests
            time.sleep(0.5)
