"""
Comprehensive tests for the Streamer class functionality.
Tests cover: OHLCV streaming, single/multiple indicators, error handling.

Set the TRADINGVIEW_JWT_TOKEN environment variable to run these tests:
    export TRADINGVIEW_JWT_TOKEN="your_jwt_token_here"
"""
import pytest
import json
import os
import time
from tv_scraper import Streamer


# Get JWT token from environment variable
JWT_TOKEN = os.getenv("TRADINGVIEW_JWT_TOKEN", "unauthorized_user_token")

# Skip all tests if JWT token is not set
# pytestmark = pytest.mark.skipif(
#     not JWT_TOKEN,
#     reason="TRADINGVIEW_JWT_TOKEN environment variable not set. Set it to run these tests."
# )


class TestStreamerOHLCV:
    """Test OHLCV data streaming without indicators"""
    
    def test_stream_ohlcv_only(self):
        """Test streaming OHLCV data without any indicators"""
        streamer = Streamer(
            export_result=True,
            export_type='json',
            websocket_jwt_token=JWT_TOKEN
        )
        
        result = streamer.stream(
            exchange="BINANCE",
            symbol="BTCUSDT",
            timeframe="1m",
            numb_price_candles=3
        )
        
        # Assertions
        assert "status" in result
        assert result["status"] == "success"
        data = result["data"]
        assert "ohlcv" in data
        assert "indicators" in data
        assert isinstance(data["ohlcv"], list)
        assert isinstance(data["indicators"], dict)
        assert len(data["ohlcv"]) > 0
        assert len(data["indicators"]) == 0  # No indicators requested
        
        # Sleep to avoid forbidden error
        time.sleep(1)


class TestStreamerSingleIndicator:
    """Test streaming with a single indicator"""
    
    def test_stream_with_rsi(self):
        """Test streaming OHLCV data with RSI indicator"""
        if JWT_TOKEN == "unauthorized_user_token":
            pytest.skip("Skipping indicator test: TRADINGVIEW_JWT_TOKEN not set")

        streamer = Streamer(
            export_result=True,
            export_type='json',
            websocket_jwt_token=JWT_TOKEN
        )
        
        result = streamer.stream(
            exchange="BINANCE",
            symbol="BTCUSDT",
            indicators=[("STD;RSI", "37.0")],
            timeframe="1m",
            numb_price_candles=3
        )
        
        # Assertions
        assert result["status"] == "success"
        data = result["data"]
        assert "ohlcv" in data
        assert "indicators" in data
        assert len(data["ohlcv"]) > 0
        assert len(data["indicators"]) == 1
        assert "STD;RSI" in data["indicators"]
        assert isinstance(data["indicators"]["STD;RSI"], list)
        assert len(data["indicators"]["STD;RSI"]) > 0
        
        # Sleep to avoid forbidden error
        time.sleep(1)


class TestStreamerMultipleIndicators:
    """Test streaming with multiple indicators"""
    
    def test_stream_with_rsi_and_macd(self):
        """Test streaming with RSI and MACD indicators"""
        if JWT_TOKEN == "unauthorized_user_token":
            pytest.skip("Skipping indicator test: TRADINGVIEW_JWT_TOKEN not set")

        streamer = Streamer(
            export_result=True,
            export_type='json',
            websocket_jwt_token=JWT_TOKEN
        )
        
        result = streamer.stream(
            exchange="BINANCE",
            symbol="BTCUSDT",
            indicators=[("STD;RSI", "37.0"), ("STD;MACD", "31.0")],
            timeframe="1m",
            numb_price_candles=3
        )
        
        # Assertions
        assert result["status"] == "success"
        data = result["data"]
        assert "ohlcv" in data
        assert "indicators" in data
        assert len(data["ohlcv"]) > 0
        assert len(data["indicators"]) == 2
        assert "STD;RSI" in data["indicators"]
        assert "STD;MACD" in data["indicators"]
        assert isinstance(data["indicators"]["STD;RSI"], list)
        assert isinstance(data["indicators"]["STD;MACD"], list)
        assert len(data["indicators"]["STD;RSI"]) > 0
        assert len(data["indicators"]["STD;MACD"]) > 0
        
        # Sleep to avoid forbidden error
        time.sleep(1)
    
    def test_stream_with_three_indicators(self):
        """Test streaming with three indicators: RSI, MACD, and CCI
        
        Note: Free TradingView accounts are limited to 2 indicators maximum.
        This test will only receive 2 indicators (RSI and MACD), and CCI will timeout.
        The error message "❌ Unable to scrape indicator: STD;CCI" should be logged.
        """
        if JWT_TOKEN == "unauthorized_user_token":
            pytest.skip("Skipping indicator test: TRADINGVIEW_JWT_TOKEN not set")

        streamer = Streamer(
            export_result=True,
            export_type='json',
            websocket_jwt_token=JWT_TOKEN
        )
        
        result = streamer.stream(
            exchange="BINANCE",
            symbol="BTCUSDT",
            indicators=[
                ("STD;RSI", "37.0"),
                ("STD;MACD", "31.0"),
                ("STD;CCI", "37.0")
            ],
            timeframe="1m",
            numb_price_candles=3
        )
        
        # Assertions for free account (2 indicator limit)
        # We expect only 2 indicators to be received
        data = result["data"]
        assert len(data["indicators"]) == 2, f"Free accounts can only stream 2 indicators, got {len(data['indicators'])}"
        assert "STD;RSI" in data["indicators"], "RSI should be present"
        assert "STD;MACD" in data["indicators"], "MACD should be present"
        
        # Sleep to avoid forbidden error
        time.sleep(1)


class TestStreamerDataStructure:
    """Test data structure and content validation"""
    
    def test_ohlcv_data_structure(self):
        """Test that OHLCV data has correct structure"""
        streamer = Streamer(
            export_result=True,
            export_type='json',
            websocket_jwt_token=JWT_TOKEN
        )
        
        result = streamer.stream(
            exchange="BINANCE",
            symbol="BTCUSDT",
            timeframe="1m",
            numb_candles=3
        )
        
        # Check OHLCV structure
        ohlcv_candle = result["data"]["ohlcv"][0]
        required_keys = ['index', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
        for key in required_keys:
            assert key in ohlcv_candle, f"Missing key: {key}"
        
        # Sleep to avoid forbidden error
        time.sleep(1)
    
    def test_indicator_data_structure(self):
        """Test that indicator data has correct structure"""
        if JWT_TOKEN == "unauthorized_user_token":
            pytest.skip("Skipping indicator test: TRADINGVIEW_JWT_TOKEN not set")

        streamer = Streamer(
            export_result=True,
            export_type='json',
            websocket_jwt_token=JWT_TOKEN
        )
        
        result = streamer.stream(
            exchange="BINANCE",
            symbol="BTCUSDT",
            indicators=[("STD;RSI", "37.0")],
            timeframe="1m",
            numb_candles=3
        )
        
        # Check indicator structure
        rsi_data = result["data"]["indicators"]["STD;RSI"][0]
        assert 'index' in rsi_data
        assert 'timestamp' in rsi_data
        assert isinstance(rsi_data['timestamp'], (int, float))
        
        # Sleep to avoid forbidden error
        time.sleep(1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
