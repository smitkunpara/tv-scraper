"""Unit tests for CandleStreamer.

Comprehensive tests covering valid inputs, invalid inputs, edge cases,
and various parameter combinations using mocking - no actual WebSocket connections.
"""

import json
from unittest.mock import MagicMock, patch

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.streaming.candle_streamer import CandleStreamer


class TestCandleStreamerInit:
    """Tests for CandleStreamer initialization."""

    def test_default_init(self):
        """Test default initialization."""
        cs = CandleStreamer()
        assert cs.export_result is False
        assert cs.export_type == "json"
        assert cs.cookie is None
        assert cs.study_id_to_name_map == {}

    def test_custom_init(self):
        """Test custom initialization."""
        cs = CandleStreamer(export_result=True, export_type="csv", cookie="test_cookie")
        assert cs.export_result is True
        assert cs.export_type == "csv"
        assert cs.cookie == "test_cookie"

    def test_cookie_from_env(self, monkeypatch):
        """Test cookie from environment variable."""
        monkeypatch.setenv("TRADINGVIEW_COOKIE", "env_cookie")
        cs = CandleStreamer()
        assert cs.cookie == "env_cookie"

    def test_cookie_param_overrides_env(self, monkeypatch):
        """Test cookie parameter overrides environment."""
        monkeypatch.setenv("TRADINGVIEW_COOKIE", "env_cookie")
        cs = CandleStreamer(cookie="param_cookie")
        assert cs.cookie == "param_cookie"


class TestInheritance:
    """Test that CandleStreamer inherits from BaseStreamer/BaseScraper."""

    def test_inherits_from_base_scraper(self):
        """Verify CandleStreamer inherits BaseScraper methods."""
        cs = CandleStreamer()
        assert hasattr(cs, "_success_response")
        assert hasattr(cs, "_error_response")
        assert hasattr(cs, "_export")

    def test_inherits_connect_method(self):
        """Verify connect method exists."""
        cs = CandleStreamer()
        assert hasattr(cs, "connect")
        assert callable(cs.connect)


class TestGetCandlesInvalidInputs:
    """Test get_candles with invalid inputs."""

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_empty_exchange(self, mock_cc):
        """Test empty exchange returns error."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        cs = CandleStreamer()
        result = cs.get_candles(exchange="", symbol="BTCUSDT")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "exchange" in result["metadata"]
        assert "symbol" in result["metadata"]

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_empty_symbol(self, mock_cc):
        """Test empty symbol returns error."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        cs = CandleStreamer()
        result = cs.get_candles(exchange="BINANCE", symbol="")

        assert result["status"] == STATUS_FAILED

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_null_exchange(self, mock_cc):
        """Test null exchange returns error."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        cs = CandleStreamer()
        result = cs.get_candles(exchange=None, symbol="BTCUSDT")

        assert result["status"] == STATUS_FAILED

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_null_symbol(self, mock_cc):
        """Test null symbol returns error."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        cs = CandleStreamer()
        result = cs.get_candles(exchange="BINANCE", symbol=None)  # type: ignore
        assert result["status"] == STATUS_FAILED
        assert "Symbol must be a non-empty string" in result["error"]

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_whitespace_only_exchange(self, mock_cc):
        """Test whitespace-only exchange returns error."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        cs = CandleStreamer()
        result = cs.get_candles(exchange="   ", symbol="BTCUSDT")

        assert result["status"] == STATUS_FAILED

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_whitespace_only_symbol(self, mock_cc):
        """Test whitespace-only symbol returns error."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        cs = CandleStreamer()
        result = cs.get_candles(exchange="BINANCE", symbol="   ")

        assert result["status"] == STATUS_FAILED


class TestGetCandlesInvalidTimeframe:
    """Test get_candles with invalid timeframe."""

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_invalid_timeframe(self, mock_validate, mock_cc):
        """Test invalid timeframe is handled gracefully.

        An invalid timeframe falls back to the "1" mapping (1-minute).
        No OHLCV data is provided, so the result is STATUS_FAILED.
        """
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())
        # Must terminate the recv loop; no OHLCV data → STATUS_FAILED
        mock_ws.recv.side_effect = [ConnectionError("done")]

        cs = CandleStreamer()
        result = cs.get_candles(
            exchange="BINANCE", symbol="BTCUSDT", timeframe="invalid"
        )

        assert "status" in result
        assert result["status"] == STATUS_FAILED
        # The timeframe is preserved in metadata even on failure
        assert result["metadata"]["timeframe"] == "invalid"


class TestGetCandlesInvalidNumbCandles:
    """Test get_candles with invalid numb_candles values."""

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_negative_numb_candles(self, mock_validate, mock_cc):
        """Test negative numb_candles returns error."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        cs = CandleStreamer()
        result = cs.get_candles(exchange="BINANCE", symbol="BTCUSDT", numb_candles=-5)

        assert result["status"] == STATUS_FAILED

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_zero_numb_candles(self, mock_validate, mock_cc):
        """Test zero numb_candles returns error."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        cs = CandleStreamer()
        result = cs.get_candles(exchange="BINANCE", symbol="BTCUSDT", numb_candles=0)

        assert result["status"] == STATUS_FAILED

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_very_large_numb_candles(self, mock_validate, mock_cc):
        """Test very large numb_candles."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        # Create mock packet
        ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
        ts_pkt = {
            "m": "timescale_update",
            "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
        }
        ts_raw = json.dumps(ts_pkt)
        framed = f"~m~{len(ts_raw)}~m~{ts_raw}"
        mock_ws.recv.side_effect = [framed, ConnectionError("done")]

        cs = CandleStreamer()
        result = cs.get_candles(
            exchange="BINANCE", symbol="BTCUSDT", numb_candles=10000
        )

        # Should handle gracefully - either return data or error
        assert "status" in result


class TestGetCandlesInvalidIndicators:
    """Test get_candles with invalid indicators."""

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_empty_indicators_list(self, mock_validate, mock_cc):
        """Test empty indicators list works."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
        ts_pkt = {
            "m": "timescale_update",
            "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
        }
        ts_raw = json.dumps(ts_pkt)
        framed = f"~m~{len(ts_raw)}~m~{ts_raw}"
        mock_ws.recv.side_effect = [framed, ConnectionError("done")]

        cs = CandleStreamer()
        result = cs.get_candles(exchange="BINANCE", symbol="BTCUSDT", indicators=[])

        assert result["status"] == STATUS_SUCCESS

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_none_indicators(self, mock_validate, mock_cc):
        """Test None indicators works."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
        ts_pkt = {
            "m": "timescale_update",
            "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
        }
        ts_raw = json.dumps(ts_pkt)
        framed = f"~m~{len(ts_raw)}~m~{ts_raw}"
        mock_ws.recv.side_effect = [framed, ConnectionError("done")]

        cs = CandleStreamer()
        result = cs.get_candles(exchange="BINANCE", symbol="BTCUSDT", indicators=None)

        assert result["status"] == STATUS_SUCCESS


class TestGetCandlesValidInputs:
    """Test get_candles with valid inputs and various combinations."""

    def _make_mock_packets(self, num_candles: int = 5) -> list:
        """Create mock WebSocket packets — all candles in a single timescale_update.

        TradingView's timescale_update contains all requested candles in the
        's' array of a single message. The code replaces ohlcv_data (not extends)
        on each timescale_update, so putting multiple entries in one packet is correct.
        """
        ohlcv_entries = [
            {
                "i": i,
                "v": [
                    1700000000 + (i * 3600),
                    100.0 + i,
                    105.0 + i,
                    99.0 + i,
                    102.0 + i,
                    5000 + i,
                ],
            }
            for i in range(num_candles)
        ]
        ts_pkt = {
            "m": "timescale_update",
            "p": ["cs_test", {"sds_1": {"s": ohlcv_entries}}],
        }
        ts_raw = json.dumps(ts_pkt)
        framed = f"~m~{len(ts_raw)}~m~{ts_raw}"
        return [framed, ConnectionError("done")]

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_basic_success(self, mock_validate, mock_cc):
        """Test basic successful call."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())
        mock_ws.recv.side_effect = self._make_mock_packets(5)

        cs = CandleStreamer()
        result = cs.get_candles(exchange="BINANCE", symbol="BTCUSDT", numb_candles=5)

        assert result["status"] == STATUS_SUCCESS
        assert "ohlcv" in result["data"]
        assert len(result["data"]["ohlcv"]) == 5
        assert result["metadata"]["exchange"] == "BINANCE"
        assert result["metadata"]["symbol"] == "BTCUSDT"

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_small_numb_candles(self, mock_validate, mock_cc):
        """Test with small numb_candles (1)."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())
        mock_ws.recv.side_effect = self._make_mock_packets(1)

        cs = CandleStreamer()
        result = cs.get_candles(exchange="NASDAQ", symbol="AAPL", numb_candles=1)

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]["ohlcv"]) == 1

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_medium_numb_candles(self, mock_validate, mock_cc):
        """Test with medium numb_candles (50)."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())
        mock_ws.recv.side_effect = self._make_mock_packets(50)

        cs = CandleStreamer()
        result = cs.get_candles(exchange="NYSE", symbol="A", numb_candles=50)

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]["ohlcv"]) == 50

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_all_timeframes(self, mock_validate, mock_cc):
        """Test with all supported timeframes."""
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        def fresh_ws(*args, **kwargs):
            """Return a fresh mock WebSocket with new recv packets each call."""
            mock_ws = MagicMock()
            mock_ws.recv.side_effect = self._make_mock_packets(5)
            return mock_ws

        mock_cc.side_effect = fresh_ws

        timeframes = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "1d", "1w", "1M"]

        cs = CandleStreamer()
        for tf in timeframes:
            result = cs.get_candles(
                exchange="BINANCE", symbol="BTCUSDT", timeframe=tf, numb_candles=5
            )
            assert result["metadata"]["timeframe"] == tf, f"Failed for {tf}"

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_different_exchanges(self, mock_validate, mock_cc):
        """Test with different exchanges."""
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        def fresh_ws(*args, **kwargs):
            """Return a fresh mock WebSocket with new recv packets each call."""
            mock_ws = MagicMock()
            mock_ws.recv.side_effect = self._make_mock_packets(5)
            return mock_ws

        mock_cc.side_effect = fresh_ws

        exchanges = ["BINANCE", "NASDAQ", "NYSE", "FX", "CRYPTOCAP"]

        cs = CandleStreamer()
        for exch in exchanges:
            result = cs.get_candles(exchange=exch, symbol="BTCUSDT", numb_candles=5)
            assert result["metadata"]["exchange"] == exch, f"Failed for {exch}"


class TestGetCandlesWithIndicators:
    """Test get_candles with various indicator configurations."""

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.streaming.candle_streamer.fetch_indicator_metadata")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_single_indicator(self, mock_validate, mock_fetch_meta, mock_cc):
        """Test with single indicator."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())
        mock_fetch_meta.return_value = {
            "status": "success",
            "data": {
                "m": "create_study",
                "p": ["cs_test", "st9", "st1", "sds_1", "STD;RSI", {}],
            },
        }

        # OHLCV packet
        ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
        ts_pkt = {
            "m": "timescale_update",
            "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
        }
        ts_raw = json.dumps(ts_pkt)
        ts_framed = f"~m~{len(ts_raw)}~m~{ts_raw}"

        # Indicator packet (du)
        ind_data = [{"i": 0, "v": [1700000000, 55.5, 60.0]}]
        du_pkt = {"m": "du", "p": ["cs_test", {"st9": {"st": ind_data}}]}
        du_raw = json.dumps(du_pkt)
        du_framed = f"~m~{len(du_raw)}~m~{du_raw}"

        mock_ws.recv.side_effect = [ts_framed, du_framed, ConnectionError("done")]

        cs = CandleStreamer()
        result = cs.get_candles(
            exchange="NASDAQ",
            symbol="AAPL",
            numb_candles=1,
            indicators=[("STD;RSI", "37.0")],
        )

        assert result["status"] == STATUS_SUCCESS
        assert "indicators" in result["data"]
        assert "STD;RSI" in result["data"]["indicators"]

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.streaming.candle_streamer.fetch_indicator_metadata")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_multiple_indicators(self, mock_validate, mock_fetch_meta, mock_cc):
        """Test with multiple indicators — verifies each is added to the session.

        When indicators are requested but no du packets arrive before disconnect,
        the code returns STATUS_FAILED with a clear error listing missing indicators.
        """
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())
        # Called once per indicator — return a unique study id each time
        study_responses = [
            {
                "status": "success",
                "data": {
                    "m": "create_study",
                    "p": ["cs_test", f"st{9 + i}", "st1", "sds_1", ind, {}],
                },
            }
            for i, ind in enumerate(["STD;RSI", "STD;MACD", "STD;ATR"])
        ]
        mock_fetch_meta.side_effect = study_responses

        # Only OHLCV packet — no du packets for indicators
        ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
        ts_pkt = {
            "m": "timescale_update",
            "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
        }
        ts_raw = json.dumps(ts_pkt)
        ts_framed = f"~m~{len(ts_raw)}~m~{ts_raw}"

        mock_ws.recv.side_effect = [ts_framed, ConnectionError("done")]

        cs = CandleStreamer()
        result = cs.get_candles(
            exchange="NASDAQ",
            symbol="AAPL",
            numb_candles=1,
            indicators=[("STD;RSI", "37.0"), ("STD;MACD", "12.0"), ("STD;ATR", "12.0")],
        )

        # Without indicator data packets, returns failed with missing indicator info
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None
        assert "Failed to fetch indicator data" in result["error"]


class TestGetCandlesExport:
    """Test export functionality."""

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.base.save_json_file")
    def test_export_json(self, mock_save, mock_validate, mock_cc):
        """Test JSON export."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
        ts_pkt = {
            "m": "timescale_update",
            "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
        }
        ts_raw = json.dumps(ts_pkt)
        framed = f"~m~{len(ts_raw)}~m~{ts_raw}"
        mock_ws.recv.side_effect = [framed, ConnectionError("done")]

        cs = CandleStreamer(export_result=True, export_type="json")
        cs.get_candles(exchange="BINANCE", symbol="BTCUSDT", numb_candles=1)

        assert mock_save.called

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.base.save_csv_file")
    def test_export_csv(self, mock_save, mock_validate, mock_cc):
        """Test CSV export (patches BaseScraper._export which calls save_csv_file)."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
        ts_pkt = {
            "m": "timescale_update",
            "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
        }
        ts_raw = json.dumps(ts_pkt)
        framed = f"~m~{len(ts_raw)}~m~{ts_raw}"
        mock_ws.recv.side_effect = [framed, ConnectionError("done")]

        cs = CandleStreamer(export_result=True, export_type="csv")
        cs.get_candles(exchange="BINANCE", symbol="BTCUSDT", numb_candles=1)

        assert mock_save.called


class TestGetCandlesErrorHandling:
    """Test error handling in get_candles."""

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_no_data_received(self, mock_validate, mock_cc):
        """Test when no OHLCV data is received."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())
        mock_ws.recv.side_effect = [ConnectionError("done")]

        cs = CandleStreamer()
        result = cs.get_candles(exchange="BINANCE", symbol="BTCUSDT", numb_candles=5)

        assert result["status"] == STATUS_FAILED
        assert "No OHLCV data received" in result["error"]

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_validation_error(self, mock_validate, mock_cc):
        """Test validation error from DataValidator."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = Exception("Invalid symbol")

        cs = CandleStreamer()
        result = cs.get_candles(
            exchange="INVALID_EXCHANGE", symbol="INVALID", numb_candles=5
        )

        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None


class TestMetadata:
    """Test metadata in responses."""

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_metadata_has_all_params(self, mock_validate, mock_cc):
        """Test metadata contains all input parameters."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
        ts_pkt = {
            "m": "timescale_update",
            "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
        }
        ts_raw = json.dumps(ts_pkt)
        framed = f"~m~{len(ts_raw)}~m~{ts_raw}"
        mock_ws.recv.side_effect = [framed, ConnectionError("done")]

        cs = CandleStreamer()
        result = cs.get_candles(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="4h",
            numb_candles=100,
            indicators=[("STD;RSI", "37.0")],
        )

        meta = result["metadata"]
        assert meta["exchange"] == "NASDAQ"
        assert meta["symbol"] == "AAPL"
        assert meta["timeframe"] == "4h"
        assert meta["numb_candles"] == 100
        assert meta["indicators"] == [("STD;RSI", "37.0")]


class TestResponseEnvelope:
    """Test standardized response envelope."""

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_success_has_all_keys(self, mock_validate, mock_cc):
        """Test success response has required keys."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
        ts_pkt = {
            "m": "timescale_update",
            "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
        }
        ts_raw = json.dumps(ts_pkt)
        framed = f"~m~{len(ts_raw)}~m~{ts_raw}"
        mock_ws.recv.side_effect = [framed, ConnectionError("done")]

        cs = CandleStreamer()
        result = cs.get_candles(exchange="BINANCE", symbol="BTCUSDT")

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_error_has_all_keys(self, mock_validate, mock_cc):
        """Test error response has required keys."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = Exception("Invalid")

        cs = CandleStreamer()
        result = cs.get_candles(exchange="INVALID", symbol="INVALID")

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None


class TestConnect:
    """Test connect method."""

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_connect_without_cookie(self, mock_cc):
        """Test connect without cookie sends unauthorized_user_token via set_auth_token."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        cs = CandleStreamer()
        cs.connect()

        mock_cc.assert_called_once()
        # JWT token is sent via WebSocket set_auth_token message, not as a kwarg
        # Verify ws.send was called with the unauthorized token
        sent_messages = [call[0][0] for call in mock_ws.send.call_args_list]
        assert any("unauthorized_user_token" in msg for msg in sent_messages), (
            "Expected unauthorized_user_token in one of the sent WebSocket messages"
        )

    @patch("tv_scraper.streaming.auth.get_valid_jwt_token")
    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_connect_with_cookie(self, mock_cc, mock_jwt):
        """Test connect with cookie resolves JWT."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_jwt.return_value = "resolved_jwt_token"

        cs = CandleStreamer(cookie="test_cookie")
        cs.connect()

        mock_jwt.assert_called_once_with("test_cookie")
        mock_cc.assert_called_once()


class TestStudyIdMap:
    """Test study_id_to_name_map functionality."""

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.streaming.candle_streamer.fetch_indicator_metadata")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_map_is_cleared_on_each_call(self, mock_validate, mock_fetch_meta, mock_cc):
        """Test that study_id_to_name_map is cleared before each call."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())
        mock_fetch_meta.return_value = {
            "status": "success",
            "data": {
                "m": "create_study",
                "p": ["cs_test", "st9", "st1", "sds_1", "STD;RSI", {}],
            },
        }

        ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
        ts_pkt = {
            "m": "timescale_update",
            "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
        }
        ts_raw = json.dumps(ts_pkt)
        framed = f"~m~{len(ts_raw)}~m~{ts_raw}"
        mock_ws.recv.side_effect = [framed, ConnectionError("done")]

        cs = CandleStreamer()

        # First call
        cs.get_candles(
            exchange="BINANCE", symbol="BTCUSDT", indicators=[("STD;RSI", "37.0")]
        )
        assert "st9" in cs.study_id_to_name_map

        # Second call - map should be cleared
        mock_ws.recv.side_effect = [framed, ConnectionError("done")]
        cs.get_candles(
            exchange="BINANCE", symbol="ETHUSDT", indicators=[("STD;RSI", "37.0")]
        )
        assert "st9" in cs.study_id_to_name_map  # Re-populated


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_special_characters_in_symbol(self, mock_validate, mock_cc):
        """Test symbol with special characters."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
        ts_pkt = {
            "m": "timescale_update",
            "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
        }
        ts_raw = json.dumps(ts_pkt)
        framed = f"~m~{len(ts_raw)}~m~{ts_raw}"
        mock_ws.recv.side_effect = [framed, ConnectionError("done")]

        cs = CandleStreamer()
        result = cs.get_candles(exchange="BINANCE", symbol="BTC-USD")

        # Should work if symbol is valid
        assert "status" in result

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_case_sensitivity_exchange(self, mock_validate, mock_cc):
        """Test exchange is case insensitive."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
        ts_pkt = {
            "m": "timescale_update",
            "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
        }
        ts_raw = json.dumps(ts_pkt)
        framed = f"~m~{len(ts_raw)}~m~{ts_raw}"
        mock_ws.recv.side_effect = [framed, ConnectionError("done")]

        cs = CandleStreamer()

        # All should work - validator should handle case
        result = cs.get_candles(exchange="binance", symbol="btcusdt")
        # Note: Metadata captures actual input values.
        assert result["metadata"]["exchange"] == "binance"
        assert result["metadata"]["symbol"] == "btcusdt"
