"""Unit tests for tv_scraper.streaming modules.

All tests use mocking — no actual WebSocket or HTTP connections.
"""

import json
import re
from unittest.mock import MagicMock, patch, call

import pytest

# ---------------------------------------------------------------------------
# StreamHandler tests
# ---------------------------------------------------------------------------


class TestStreamHandler:
    """Tests for the low-level WebSocket protocol handler."""

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def _make_handler(self, mock_create_conn, jwt_token="unauthorized_user_token"):
        """Helper: build a StreamHandler with a mocked WebSocket."""
        mock_ws = MagicMock()
        mock_create_conn.return_value = mock_ws
        from tv_scraper.streaming.stream_handler import StreamHandler

        handler = StreamHandler(jwt_token=jwt_token)
        return handler, mock_ws, mock_create_conn

    # -- generate_session --------------------------------------------------

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_generate_session_format(self, mock_cc):
        """Session id = prefix + 12 lowercase letters."""
        mock_cc.return_value = MagicMock()
        from tv_scraper.streaming.stream_handler import StreamHandler

        handler = StreamHandler()
        session = handler.generate_session("qs_")
        assert session.startswith("qs_")
        suffix = session[3:]
        assert len(suffix) == 12
        assert suffix.isalpha() and suffix.islower()

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_generate_session_different_prefix(self, mock_cc):
        """Session with cs_ prefix."""
        mock_cc.return_value = MagicMock()
        from tv_scraper.streaming.stream_handler import StreamHandler

        handler = StreamHandler()
        session = handler.generate_session("cs_")
        assert session.startswith("cs_")
        assert len(session) == 15  # 3 prefix + 12 chars

    # -- prepend_header ----------------------------------------------------

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_prepend_header(self, mock_cc):
        """Header format: ~m~{len}~m~{msg}."""
        mock_cc.return_value = MagicMock()
        from tv_scraper.streaming.stream_handler import StreamHandler

        handler = StreamHandler()
        msg = '{"m":"test","p":[]}'
        result = handler.prepend_header(msg)
        expected = f"~m~{len(msg)}~m~{msg}"
        assert result == expected

    # -- construct_message -------------------------------------------------

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_construct_message(self, mock_cc):
        """JSON-RPC format: {"m": func, "p": params}."""
        mock_cc.return_value = MagicMock()
        from tv_scraper.streaming.stream_handler import StreamHandler

        handler = StreamHandler()
        result = handler.construct_message("set_locale", ["en", "US"])
        parsed = json.loads(result)
        assert parsed == {"m": "set_locale", "p": ["en", "US"]}

    # -- create_message ----------------------------------------------------

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_create_message(self, mock_cc):
        """create_message = prepend_header(construct_message(...))."""
        mock_cc.return_value = MagicMock()
        from tv_scraper.streaming.stream_handler import StreamHandler

        handler = StreamHandler()
        result = handler.create_message("set_locale", ["en", "US"])
        body = handler.construct_message("set_locale", ["en", "US"])
        assert result == handler.prepend_header(body)
        # Also verify the frame pattern
        assert re.match(r"~m~\d+~m~\{", result)

    # -- send_message ------------------------------------------------------

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_send_message(self, mock_cc):
        """ws.send() is called with the framed message."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        from tv_scraper.streaming.stream_handler import StreamHandler

        handler = StreamHandler()
        # Reset call tracking after __init__ setup messages
        mock_ws.send.reset_mock()
        handler.send_message("test_func", ["arg1", "arg2"])
        mock_ws.send.assert_called_once()
        sent = mock_ws.send.call_args[0][0]
        assert "test_func" in sent
        assert "arg1" in sent

    # -- _initialize_sessions ----------------------------------------------

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_initialize_sessions_sends_setup_messages(self, mock_cc):
        """Initialization must send all 6 required setup messages."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        from tv_scraper.streaming.stream_handler import StreamHandler

        handler = StreamHandler(jwt_token="test_token")
        # Gather all sent message bodies
        sent_messages = []
        for c in mock_ws.send.call_args_list:
            raw = c[0][0]
            # Extract the JSON body from ~m~{len}~m~{json}
            match = re.search(r"~m~\d+~m~(.+)", raw)
            if match:
                try:
                    parsed = json.loads(match.group(1))
                    sent_messages.append(parsed["m"])
                except (json.JSONDecodeError, KeyError):
                    pass

        assert "set_auth_token" in sent_messages
        assert "set_locale" in sent_messages
        assert "chart_create_session" in sent_messages
        assert "quote_create_session" in sent_messages
        assert "quote_set_fields" in sent_messages
        assert "quote_hibernate_all" in sent_messages

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_handler_stores_sessions(self, mock_cc):
        """Handler stores quote_session and chart_session attributes."""
        mock_cc.return_value = MagicMock()
        from tv_scraper.streaming.stream_handler import StreamHandler

        handler = StreamHandler()
        assert hasattr(handler, "quote_session")
        assert hasattr(handler, "chart_session")
        assert handler.quote_session.startswith("qs_")
        assert handler.chart_session.startswith("cs_")


# ---------------------------------------------------------------------------
# Streamer tests
# ---------------------------------------------------------------------------


class TestStreamer:
    """Tests for the main Streamer class (candles + indicators)."""

    @patch("tv_scraper.streaming.streamer.validate_symbols")
    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_get_candles_returns_success_response(self, mock_cc, mock_validate):
        """get_candles returns standardized response envelope on success."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.return_value = True

        # Build a timescale_update packet
        ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
        ts_pkt = {"m": "timescale_update", "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}]}
        ts_raw = json.dumps(ts_pkt)
        framed = f"~m~{len(ts_raw)}~m~{ts_raw}"

        mock_ws.recv.side_effect = [framed, ConnectionError("done")]

        from tv_scraper.streaming.streamer import Streamer

        s = Streamer()
        result = s.get_candles(exchange="BINANCE", symbol="BTCUSDT")

        assert result["status"] == "success"
        assert "data" in result
        assert "ohlcv" in result["data"]
        assert result["error"] is None

    @patch("tv_scraper.streaming.streamer.validate_symbols")
    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_get_candles_ohlcv_extraction(self, mock_cc, mock_validate):
        """OHLCV data is correctly serialized from timescale_update packets."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.return_value = True

        ohlcv_entries = [
            {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]},
            {"i": 1, "v": [1700000060, 102.0, 108.0, 101.0, 107.0, 6000]},
        ]
        ts_pkt = {"m": "timescale_update", "p": ["cs_test", {"sds_1": {"s": ohlcv_entries}}]}
        ts_raw = json.dumps(ts_pkt)
        framed = f"~m~{len(ts_raw)}~m~{ts_raw}"

        mock_ws.recv.side_effect = [framed, ConnectionError("done")]

        from tv_scraper.streaming.streamer import Streamer

        s = Streamer()
        result = s.get_candles(exchange="BINANCE", symbol="BTCUSDT", numb_candles=2)

        ohlcv = result["data"]["ohlcv"]
        assert len(ohlcv) == 2
        assert ohlcv[0]["open"] == 100.0
        assert ohlcv[0]["close"] == 102.0
        assert ohlcv[0]["volume"] == 5000
        assert ohlcv[1]["high"] == 108.0

    @patch("tv_scraper.streaming.streamer.fetch_indicator_metadata")
    @patch("tv_scraper.streaming.streamer.validate_symbols")
    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_get_candles_indicator_extraction(self, mock_cc, mock_validate, mock_fetch_meta):
        """Indicator data is correctly extracted from du packets."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.return_value = True

        # Mock indicator metadata
        mock_fetch_meta.return_value = {
            "m": "create_study",
            "p": ["cs_test", "st9", "st1", "sds_1", "Script@tv-scripting-101!", {}],
        }

        # OHLCV packet
        ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
        ts_pkt = {"m": "timescale_update", "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}]}
        ts_raw = json.dumps(ts_pkt)
        ts_framed = f"~m~{len(ts_raw)}~m~{ts_raw}"

        # Indicator (du) packet — data for study st9
        ind_data = [
            {"i": 0, "v": [1700000000, 55.5, 60.0]},
            {"i": 1, "v": [1700000060, 56.2, 61.0]},
        ] + [{"i": k, "v": [1700000000 + k * 60, 50.0 + k, 60.0 + k]} for k in range(2, 12)]
        du_pkt = {"m": "du", "p": ["cs_test", {"st9": {"st": ind_data}}]}
        du_raw = json.dumps(du_pkt)
        du_framed = f"~m~{len(du_raw)}~m~{du_raw}"

        mock_ws.recv.side_effect = [ts_framed, du_framed, ConnectionError("done")]

        from tv_scraper.streaming.streamer import Streamer

        s = Streamer()
        result = s.get_candles(
            exchange="BINANCE",
            symbol="BTCUSDT",
            numb_candles=1,
            indicators=[("STD;RSI", "37.0")],
        )

        assert "indicators" in result["data"]
        assert "STD;RSI" in result["data"]["indicators"]
        assert len(result["data"]["indicators"]["STD;RSI"]) > 0

    @patch("tv_scraper.streaming.streamer.validate_symbols")
    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_get_candles_with_timeframe(self, mock_cc, mock_validate):
        """Timeframe mapping: '1h' → '60', '1d' → '1D', etc."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.return_value = True

        ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
        ts_pkt = {"m": "timescale_update", "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}]}
        ts_raw = json.dumps(ts_pkt)
        framed = f"~m~{len(ts_raw)}~m~{ts_raw}"

        mock_ws.recv.side_effect = [framed, ConnectionError("done")]

        from tv_scraper.streaming.streamer import Streamer

        s = Streamer()
        # Reset send mock to track only session-add messages
        mock_ws.send.reset_mock()
        s.get_candles(exchange="BINANCE", symbol="BTCUSDT", timeframe="1h", numb_candles=1)

        # Verify the mapped timeframe '60' was sent in create_series
        all_sent = " ".join(c[0][0] for c in mock_ws.send.call_args_list)
        assert '"60"' in all_sent or "'60'" in all_sent

    @patch("tv_scraper.streaming.streamer.validate_symbols")
    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_get_candles_export(self, mock_cc, mock_validate):
        """Export is called when export_result=True."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.return_value = True

        ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
        ts_pkt = {"m": "timescale_update", "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}]}
        ts_raw = json.dumps(ts_pkt)
        framed = f"~m~{len(ts_raw)}~m~{ts_raw}"
        mock_ws.recv.side_effect = [framed, ConnectionError("done")]

        from tv_scraper.streaming.streamer import Streamer

        with patch("tv_scraper.streaming.streamer.save_json_file") as mock_save:
            s = Streamer(export_result=True, export_type="json")
            s.get_candles(exchange="BINANCE", symbol="BTCUSDT", numb_candles=1)
            assert mock_save.called

    @patch("tv_scraper.streaming.streamer.validate_symbols")
    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_stream_alias(self, mock_cc, mock_validate):
        """stream() is a compatibility alias for get_candles()."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.return_value = True

        ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
        ts_pkt = {"m": "timescale_update", "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}]}
        ts_raw = json.dumps(ts_pkt)
        framed = f"~m~{len(ts_raw)}~m~{ts_raw}"
        mock_ws.recv.side_effect = [framed, ConnectionError("done")]

        from tv_scraper.streaming.streamer import Streamer

        s = Streamer()
        result = s.stream(exchange="BINANCE", symbol="BTCUSDT", numb_candles=1)
        assert result["status"] == "success"

    @patch("tv_scraper.streaming.streamer.validate_symbols")
    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_stream_realtime_price_yields_data(self, mock_cc, mock_validate):
        """stream_realtime_price returns a generator that yields normalized price data."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.return_value = True

        # A qsd (quote session data) packet
        qsd_pkt = {
            "m": "qsd",
            "p": [
                "qs_test",
                {
                    "n": "BINANCE:BTCUSDT",
                    "s": "ok",
                    "v": {
                        "lp": 42000.0,
                        "volume": 12345,
                        "ch": 150.0,
                        "chp": 0.36,
                        "exchange": "BINANCE",
                        "short_name": "BTCUSDT",
                    },
                },
            ],
        }
        qsd_raw = json.dumps(qsd_pkt)
        framed = f"~m~{len(qsd_raw)}~m~{qsd_raw}"

        from websocket import WebSocketConnectionClosedException

        mock_ws.recv.side_effect = [framed, WebSocketConnectionClosedException("closed")]

        from tv_scraper.streaming.streamer import Streamer

        s = Streamer()
        gen = s.stream_realtime_price(exchange="BINANCE", symbol="BTCUSDT")

        # Should be a generator
        import types
        assert isinstance(gen, types.GeneratorType)

        data = next(gen)
        assert data["price"] == 42000.0
        assert data["volume"] == 12345
        assert data["change"] == 150.0
        assert data["change_percent"] == 0.36

    @patch("tv_scraper.streaming.streamer.validate_symbols")
    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_stream_realtime_price_heartbeat(self, mock_cc, mock_validate):
        """Heartbeat messages are echoed back, not yielded as data."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.return_value = True

        heartbeat = "~m~4~m~~h~42"
        qsd_pkt = {
            "m": "qsd",
            "p": [
                "qs_test",
                {
                    "n": "BINANCE:BTCUSDT",
                    "s": "ok",
                    "v": {"lp": 42000.0, "volume": 100, "ch": 10.0, "chp": 0.1},
                },
            ],
        }
        qsd_raw = json.dumps(qsd_pkt)
        framed = f"~m~{len(qsd_raw)}~m~{qsd_raw}"

        from websocket import WebSocketConnectionClosedException

        mock_ws.recv.side_effect = [
            heartbeat,
            framed,
            WebSocketConnectionClosedException("closed"),
        ]

        from tv_scraper.streaming.streamer import Streamer

        s = Streamer()
        gen = s.stream_realtime_price(exchange="BINANCE", symbol="BTCUSDT")
        data = next(gen)

        # Heartbeat should have been echoed
        mock_ws.send.assert_any_call(heartbeat)
        # But we only get the qsd data, not heartbeat
        assert data["price"] == 42000.0

    @patch("tv_scraper.streaming.streamer.validate_symbols")
    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_get_candles_error_returns_error_response(self, mock_cc, mock_validate):
        """When validation fails, an error response is returned (not raised)."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_validate.side_effect = ValueError("Invalid symbol")

        from tv_scraper.streaming.streamer import Streamer

        s = Streamer()
        result = s.get_candles(exchange="BAD", symbol="XXX")

        assert result["status"] == "failed"
        assert result["data"] is None
        assert "Invalid symbol" in result["error"]


# ---------------------------------------------------------------------------
# RealTimeData tests
# ---------------------------------------------------------------------------


class TestRealTimeData:
    """Tests for simple OHLCV + watchlist streaming."""

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_get_ohlcv_returns_generator(self, mock_cc):
        """get_ohlcv returns a generator."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        # Feed a data packet then close
        pkt = {"m": "timescale_update", "p": ["cs_test", {"sds_1": {"s": []}}]}
        raw = json.dumps(pkt)
        framed = f"~m~{len(raw)}~m~{raw}"

        from websocket import WebSocketConnectionClosedException

        mock_ws.recv.side_effect = [framed, WebSocketConnectionClosedException("closed")]

        from tv_scraper.streaming.price import RealTimeData

        rt = RealTimeData()
        gen = rt.get_ohlcv(exchange="BINANCE", symbol="BTCUSDT")

        import types
        assert isinstance(gen, types.GeneratorType)

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_get_latest_trade_info_returns_generator(self, mock_cc):
        """get_latest_trade_info returns a generator for multiple symbols."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        qsd_pkt = {"m": "qsd", "p": ["qs_test", {"n": "BINANCE:BTCUSDT", "v": {"lp": 100}}]}
        raw = json.dumps(qsd_pkt)
        framed = f"~m~{len(raw)}~m~{raw}"

        from websocket import WebSocketConnectionClosedException

        mock_ws.recv.side_effect = [framed, WebSocketConnectionClosedException("closed")]

        from tv_scraper.streaming.price import RealTimeData

        rt = RealTimeData()
        gen = rt.get_latest_trade_info(
            exchanges=["BINANCE", "NASDAQ"],
            symbols=["BTCUSDT", "AAPL"],
        )

        import types
        assert isinstance(gen, types.GeneratorType)

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    def test_heartbeat_handling(self, mock_cc):
        """Heartbeat messages are echoed back, not yielded."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        heartbeat = "~m~4~m~~h~99"
        pkt = {"m": "qsd", "p": ["qs_test", {"n": "X:Y", "v": {"lp": 50}}]}
        raw = json.dumps(pkt)
        framed = f"~m~{len(raw)}~m~{raw}"

        from websocket import WebSocketConnectionClosedException

        mock_ws.recv.side_effect = [heartbeat, framed, WebSocketConnectionClosedException("closed")]

        from tv_scraper.streaming.price import RealTimeData

        rt = RealTimeData()
        gen = rt.get_ohlcv(exchange="X", symbol="Y")
        data = next(gen)

        # Heartbeat should be echoed
        mock_ws.send.assert_any_call(heartbeat)
        # Data should be the qsd packet
        assert data["m"] == "qsd"


# ---------------------------------------------------------------------------
# Utils tests
# ---------------------------------------------------------------------------


class TestStreamingUtils:
    """Tests for streaming utility functions."""

    @patch("tv_scraper.streaming.utils.requests.get")
    def test_validate_symbols_valid(self, mock_get):
        """Valid symbol returns True."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        from tv_scraper.streaming.utils import validate_symbols

        result = validate_symbols("BINANCE", "BTCUSDT")
        assert result is True

    @patch("tv_scraper.streaming.utils.requests.get")
    def test_validate_symbols_invalid(self, mock_get):
        """Invalid symbol raises ValueError."""
        import requests as req_lib

        mock_resp = MagicMock()
        mock_resp.status_code = 404
        exc = req_lib.exceptions.HTTPError(response=mock_resp)
        mock_resp.raise_for_status.side_effect = exc
        mock_get.return_value = mock_resp

        from tv_scraper.streaming.utils import validate_symbols

        with pytest.raises(ValueError, match="Invalid"):
            validate_symbols("BAD", "XXXYYY")

    @patch("tv_scraper.streaming.utils.requests.get")
    def test_fetch_indicator_metadata(self, mock_get):
        """fetch_indicator_metadata returns prepared payload on success."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "result": {
                "metaInfo": {
                    "inputs": [{"id": "text", "defval": "test_input", "type": "text"}],
                    "pine": {"version": "5.0"},
                }
            }
        }
        mock_get.return_value = mock_resp

        from tv_scraper.streaming.utils import fetch_indicator_metadata

        result = fetch_indicator_metadata("STD;RSI", "37.0", "cs_test123")
        assert result["m"] == "create_study"
        assert result["p"][0] == "cs_test123"

    def test_prepare_indicator_metadata_structure(self):
        """prepare_indicator_metadata builds correct payload structure."""
        from tv_scraper.streaming.utils import prepare_indicator_metadata

        metainfo = {
            "inputs": [
                {"id": "text", "defval": "RSI", "type": "text"},
                {"id": "in_0", "defval": 14, "type": "integer"},
                {"id": "in_1", "defval": "close", "type": "source"},
            ],
            "pine": {"version": "5.0"},
        }
        result = prepare_indicator_metadata("STD;RSI", metainfo, "cs_abc")

        assert result["m"] == "create_study"
        assert result["p"][0] == "cs_abc"
        assert result["p"][1] == "st9"  # default study id
        # The dict param should contain input overrides in_0, in_1
        dict_param = [p for p in result["p"] if isinstance(p, dict)][0]
        assert "in_0" in dict_param
        assert dict_param["in_0"]["v"] == 14

    @patch("tv_scraper.streaming.utils.requests.get")
    def test_fetch_tradingview_indicators(self, mock_get):
        """fetch_tradingview_indicators returns filtered indicator list."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "results": [
                {
                    "scriptName": "RSI Strategy",
                    "imageUrl": "http://example.com/img.png",
                    "author": {"username": "trader1"},
                    "agreeCount": 100,
                    "isRecommended": True,
                    "scriptIdPart": "STD;RSI",
                    "version": "37.0",
                },
                {
                    "scriptName": "MACD Helper",
                    "imageUrl": "http://example.com/img2.png",
                    "author": {"username": "trader2"},
                    "agreeCount": 50,
                    "isRecommended": False,
                    "scriptIdPart": "STD;MACD",
                    "version": "31.0",
                },
            ]
        }
        mock_get.return_value = mock_resp

        from tv_scraper.streaming.utils import fetch_tradingview_indicators

        results = fetch_tradingview_indicators("RSI")
        assert len(results) == 1
        assert results[0]["scriptName"] == "RSI Strategy"
        assert results[0]["scriptIdPart"] == "STD;RSI"
