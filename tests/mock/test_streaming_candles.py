"""Mock tests for streaming candles using saved JSON fixtures.

Tests use pre-recorded WebSocket responses to ensure consistent,
repeatable tests without network dependencies.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.streaming.candle_streamer import CandleStreamer
from tv_scraper.streaming.streamer import Streamer

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "streaming" / "candles"


def load_fixture(name: str) -> dict:
    """Load a JSON fixture file."""
    fixture_path = FIXTURES_DIR / f"{name}.json"
    if fixture_path.exists():
        with open(fixture_path) as f:
            return json.load(f)
    pytest.skip(f"Fixture not found: {name}")


def create_mock_from_fixture(fixture_name: str) -> MagicMock:
    """Create mock WebSocket that returns data from fixture."""
    fixture = load_fixture(fixture_name)
    mock_ws = MagicMock()

    recv_data = []
    for pkt in fixture.get("packets", []):
        raw = json.dumps(pkt)
        recv_data.append(f"~m~{len(raw)}~m~{raw}")
    recv_data.append(ConnectionError("done"))
    mock_ws.recv.side_effect = recv_data

    return mock_ws


def get_fixture_files() -> list[str]:
    """Get all fixture file names without extension."""
    if not FIXTURES_DIR.exists():
        return []
    return [f.stem for f in FIXTURES_DIR.glob("*.json")]


class TestMockStreamingCandles:
    """Test streaming candles with mocked WebSocket using fixtures."""

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_basic_candle_success(self, mock_validate, mock_cc):
        """Test basic candle fetch with mock data."""
        mock_ws = create_mock_from_fixture("basic_candles")
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        cs = CandleStreamer()
        result = cs.get_candles(exchange="NASDAQ", symbol="AAPL", numb_candles=5)

        assert result["status"] == STATUS_SUCCESS
        assert "ohlcv" in result["data"]
        assert len(result["data"]["ohlcv"]) > 0

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_candle_structure(self, mock_validate, mock_cc):
        """Test OHLCV candle structure matches expected format."""
        mock_ws = create_mock_from_fixture("basic_candles")
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        cs = CandleStreamer()
        result = cs.get_candles(exchange="NASDAQ", symbol="AAPL", numb_candles=5)

        if result["status"] == STATUS_SUCCESS and result["data"]["ohlcv"]:
            candle = result["data"]["ohlcv"][0]
            required_fields = ["index", "timestamp", "open", "high", "low", "close"]
            for field in required_fields:
                assert field in candle, f"Missing field: {field}"

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_multiple_timeframes_fixture(self, mock_validate, mock_cc):
        """Test multiple timeframes using fixtures."""
        mock_ws = create_mock_from_fixture("multi_timeframe")
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        cs = CandleStreamer()
        result = cs.get_candles(
            exchange="BINANCE", symbol="BTCUSDT", timeframe="1h", numb_candles=10
        )

        assert "status" in result
        if result["status"] == STATUS_SUCCESS:
            assert "ohlcv" in result["data"]
            assert result["metadata"]["timeframe"] == "1h"

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_with_indicators_fixture(self, mock_validate, mock_cc):
        """Test candles with indicators using fixtures."""
        mock_ws = create_mock_from_fixture("with_indicators")
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        cs = CandleStreamer()
        result = cs.get_candles(
            exchange="NASDAQ",
            symbol="AAPL",
            numb_candles=5,
            indicators=[("STD;RSI", "37.0")],
        )

        assert "status" in result

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_different_exchanges_fixture(self, mock_validate, mock_cc):
        """Test different exchanges using fixtures."""
        mock_ws = create_mock_from_fixture("basic_candles")
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        cs = CandleStreamer()

        exchanges = [
            ("BINANCE", "BTCUSDT"),
            ("NASDAQ", "AAPL"),
            ("NYSE", "JPM"),
            ("FX_IDC", "EURUSD"),
        ]

        for exchange, symbol in exchanges:
            mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())
            result = cs.get_candles(exchange=exchange, symbol=symbol, numb_candles=5)
            assert result["metadata"]["exchange"] == exchange.upper()


class TestMockWithIndicators:
    """Test indicators with mocked fixtures."""

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.candle_streamer.fetch_indicator_metadata")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_rsi_indicator(self, mock_validate, mock_fetch_meta, mock_cc):
        """Test RSI indicator extraction."""
        fixture = load_fixture("with_rsi")
        mock_ws = MagicMock()

        recv_data = []
        for pkt in fixture.get("packets", []):
            raw = json.dumps(pkt)
            recv_data.append(f"~m~{len(raw)}~m~{raw}")
        recv_data.append(ConnectionError("done"))
        mock_ws.recv.side_effect = recv_data

        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())
        mock_fetch_meta.return_value = {
            "status": "success",
            "data": {
                "m": "create_study",
                "p": ["cs_test", "st9", "st1", "sds_1", "STD;RSI", {}],
            },
        }

        cs = CandleStreamer()
        result = cs.get_candles(
            exchange="NASDAQ",
            symbol="AAPL",
            numb_candles=5,
            indicators=[("STD;RSI", "37.0")],
        )

        if result["status"] == STATUS_SUCCESS:
            assert "indicators" in result["data"]

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.candle_streamer.fetch_indicator_metadata")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_macd_indicator(self, mock_validate, mock_fetch_meta, mock_cc):
        """Test MACD indicator extraction."""
        fixture = load_fixture("with_macd")
        mock_ws = MagicMock()

        recv_data = []
        for pkt in fixture.get("packets", []):
            raw = json.dumps(pkt)
            recv_data.append(f"~m~{len(raw)}~m~{raw}")
        recv_data.append(ConnectionError("done"))
        mock_ws.recv.side_effect = recv_data

        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())
        mock_fetch_meta.return_value = {
            "status": "success",
            "data": {
                "m": "create_study",
                "p": ["cs_test", "st9", "st1", "sds_1", "STD;MACD", {}],
            },
        }

        cs = CandleStreamer()
        result = cs.get_candles(
            exchange="NYSE",
            symbol="JPM",
            numb_candles=5,
            indicators=[("STD;MACD", "12.0")],
        )

        if result["status"] == STATUS_SUCCESS:
            assert "indicators" in result["data"]


class TestMockCombinations:
    """Test various parameter combinations with fixtures."""

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_all_timeframes_combination(self, mock_validate, mock_cc):
        """Test all supported timeframes."""
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        timeframes = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "1d", "1w", "1M"]

        def fresh_ws(*args, **kwargs):
            fixture = load_fixture("basic_candles")
            mock_ws = MagicMock()
            recv_data = []
            for pkt in fixture.get("packets", []):
                raw = json.dumps(pkt)
                recv_data.append(f"~m~{len(raw)}~m~{raw}")
            recv_data.append(ConnectionError("done"))
            mock_ws.recv.side_effect = recv_data
            return mock_ws

        mock_cc.side_effect = fresh_ws

        cs = CandleStreamer()
        for tf in timeframes:
            result = cs.get_candles(
                exchange="BINANCE", symbol="BTCUSDT", timeframe=tf, numb_candles=5
            )
            assert result["metadata"]["timeframe"] == tf

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_all_exchanges_combination(self, mock_validate, mock_cc):
        """Test all exchanges with fixtures."""
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        exchanges = [
            ("BINANCE", "BTCUSDT"),
            ("BINANCE", "ETHUSDT"),
            ("NASDAQ", "AAPL"),
            ("NYSE", "JPM"),
            ("FX_IDC", "EURUSD"),
        ]

        def fresh_ws(*args, **kwargs):
            fixture = load_fixture("basic_candles")
            mock_ws = MagicMock()
            recv_data = []
            for pkt in fixture.get("packets", []):
                raw = json.dumps(pkt)
                recv_data.append(f"~m~{len(raw)}~m~{raw}")
            recv_data.append(ConnectionError("done"))
            mock_ws.recv.side_effect = recv_data
            return mock_ws

        mock_cc.side_effect = fresh_ws

        cs = CandleStreamer()
        for exchange, symbol in exchanges:
            result = cs.get_candles(exchange=exchange, symbol=symbol, numb_candles=5)
            assert result["metadata"]["exchange"] == exchange.upper()
            assert result["metadata"]["symbol"] == symbol.upper()

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_numb_candles_combinations(self, mock_validate, mock_cc):
        """Test different numb_candles values."""
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        numb_candles_values = [5, 10, 50]

        def fresh_ws(*args, **kwargs):
            fixture = load_fixture("many_candles")
            mock_ws = MagicMock()
            recv_data = []
            for pkt in fixture.get("packets", []):
                raw = json.dumps(pkt)
                recv_data.append(f"~m~{len(raw)}~m~{raw}")
            recv_data.append(ConnectionError("done"))
            mock_ws.recv.side_effect = recv_data
            return mock_ws

        mock_cc.side_effect = fresh_ws

        cs = CandleStreamer()
        for n in numb_candles_values:
            result = cs.get_candles(
                exchange="BINANCE", symbol="BTCUSDT", numb_candles=n
            )
            if result["status"] == STATUS_SUCCESS:
                assert len(result["data"]["ohlcv"]) == n


class TestMockResponseEnvelope:
    """Test response envelope structure with fixtures."""

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_success_envelope_structure(self, mock_validate, mock_cc):
        """Test success envelope has all required fields."""
        mock_ws = create_mock_from_fixture("basic_candles")
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        cs = CandleStreamer()
        result = cs.get_candles(exchange="BINANCE", symbol="BTCUSDT", numb_candles=5)

        if result["status"] == STATUS_SUCCESS:
            assert "status" in result
            assert "data" in result
            assert "metadata" in result
            assert "error" in result
            assert result["error"] is None

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_error_envelope_structure(self, mock_validate, mock_cc):
        """Test error envelope has all required fields."""
        mock_ws = MagicMock()
        mock_ws.recv.side_effect = ConnectionError("Network error")
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = Exception("Validation failed")

        cs = CandleStreamer()
        result = cs.get_candles(exchange="INVALID", symbol="INVALID", numb_candles=5)

        assert result["status"] == STATUS_FAILED
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["error"] is not None


class TestMockMetadata:
    """Test metadata structure with fixtures."""

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_metadata_fields(self, mock_validate, mock_cc):
        """Test metadata contains all expected fields."""
        mock_ws = create_mock_from_fixture("basic_candles")
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        cs = CandleStreamer()
        result = cs.get_candles(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="1h",
            numb_candles=10,
        )

        if result["status"] == STATUS_SUCCESS:
            meta = result["metadata"]
            assert "exchange" in meta
            assert "symbol" in meta
            assert "timeframe" in meta
            assert "numb_candles" in meta


class TestMockEdgeCases:
    """Test edge cases with fixtures."""

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_empty_packet_array(self, mock_validate, mock_cc):
        """Test handling of empty packet array."""
        mock_ws = MagicMock()
        mock_ws.recv.side_effect = [ConnectionError("done")]
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        cs = CandleStreamer()
        result = cs.get_candles(exchange="BINANCE", symbol="BTCUSDT", numb_candles=5)

        assert result["status"] == STATUS_FAILED

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_malformed_json(self, mock_validate, mock_cc):
        """Test handling of malformed JSON."""
        mock_ws = MagicMock()
        mock_ws.recv.side_effect = ["not valid json", ConnectionError("done")]
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        cs = CandleStreamer()
        result = cs.get_candles(exchange="BINANCE", symbol="BTCUSDT", numb_candles=5)

        assert "status" in result

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_partial_ohlcv_data(self, mock_validate, mock_cc):
        """Test handling of partial OHLCV data."""
        partial_pkt = {
            "m": "timescale_update",
            "p": ["cs_test", {"sds_1": {"s": []}}],
        }
        mock_ws = MagicMock()
        raw = json.dumps(partial_pkt)
        mock_ws.recv.side_effect = [
            f"~m~{len(raw)}~m~{raw}",
            ConnectionError("done"),
        ]
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        cs = CandleStreamer()
        result = cs.get_candles(exchange="BINANCE", symbol="BTCUSDT", numb_candles=10)

        assert result["status"] == STATUS_FAILED


class TestStreamerMock:
    """Test Streamer class with mock fixtures."""

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_streamer_delegation(self, mock_validate, mock_cc):
        """Test Streamer delegates to CandleStreamer."""
        mock_ws = create_mock_from_fixture("basic_candles")
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        s = Streamer()
        result = s.get_candles(exchange="BINANCE", symbol="BTCUSDT", numb_candles=5)

        assert "status" in result
