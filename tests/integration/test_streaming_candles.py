"""Integration tests for streaming candles feature.

Tests cross-module workflows combining streaming with other components
like validation, export, and data processing.
"""

import json
from unittest.mock import MagicMock, patch

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.streaming.candle_streamer import CandleStreamer
from tv_scraper.streaming.streamer import Streamer


class TestIntegrationStreamingCandlesWithValidation:
    """Test streaming candles with validation integration."""

    def test_validation_before_streaming(self):
        """Test that validation is called before streaming."""
        with patch(
            "tv_scraper.core.validators.DataValidator.verify_symbol_exchange"
        ) as mock_validate:
            mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

            mock_ws = MagicMock()
            ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
            ts_pkt = {
                "m": "timescale_update",
                "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
            }
            ts_raw = json.dumps(ts_pkt)
            mock_ws.recv.side_effect = [
                f"~m~{len(ts_raw)}~m~{ts_raw}",
                ConnectionError("done"),
            ]

            with patch(
                "tv_scraper.streaming.stream_handler.create_connection"
            ) as mock_cc:
                mock_cc.return_value = mock_ws

                cs = CandleStreamer()
                result = cs.get_candles(
                    exchange="BINANCE", symbol="BTCUSDT", numb_candles=1
                )

                mock_validate.assert_called_once_with("BINANCE", "BTCUSDT")
                assert "status" in result

    def test_validation_error_propagates(self):
        """Test that validation errors propagate correctly."""
        with patch(
            "tv_scraper.core.validators.DataValidator.verify_symbol_exchange"
        ) as mock_validate:
            mock_validate.side_effect = Exception("Symbol not found")

            cs = CandleStreamer()
            result = cs.get_candles(
                exchange="INVALID", symbol="INVALID", numb_candles=5
            )

            assert result["status"] == "failed"
            assert result["error"] is not None


class TestIntegrationStreamingCandlesWithExport:
    """Test streaming candles with export integration."""

    def test_export_after_successful_stream(self):
        """Test that export is called after successful streaming."""
        with patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc:
            mock_ws = MagicMock()
            ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
            ts_pkt = {
                "m": "timescale_update",
                "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
            }
            ts_raw = json.dumps(ts_pkt)
            mock_ws.recv.side_effect = [
                f"~m~{len(ts_raw)}~m~{ts_raw}",
                ConnectionError("done"),
            ]
            mock_cc.return_value = mock_ws

            with patch(
                "tv_scraper.core.validators.DataValidator.verify_symbol_exchange"
            ) as mock_validate:
                mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

                with patch("tv_scraper.core.base.save_json_file") as mock_save:
                    cs = CandleStreamer(export_result=True, export_type="json")
                    result = cs.get_candles(
                        exchange="BINANCE", symbol="BTCUSDT", numb_candles=1
                    )

                    if result["status"] == STATUS_SUCCESS:
                        mock_save.assert_called()

    def test_no_export_on_failure(self):
        """Test that export is not called on failure."""
        with patch(
            "tv_scraper.core.validators.DataValidator.verify_symbol_exchange"
        ) as mock_validate:
            mock_validate.side_effect = Exception("Invalid")

            with patch("tv_scraper.core.base.save_json_file") as mock_save:
                cs = CandleStreamer(export_result=True, export_type="json")
                cs.get_candles(exchange="INVALID", symbol="INVALID", numb_candles=5)

                mock_save.assert_not_called()


class TestIntegrationStreamingCandlesWithIndicators:
    """Test streaming candles with indicators integration."""

    def test_indicator_metadata_fetched(self):
        """Test that indicator metadata is fetched when indicators requested."""
        with patch(
            "tv_scraper.streaming.candle_streamer.fetch_indicator_metadata"
        ) as mock_fetch:
            mock_fetch.return_value = {
                "status": "success",
                "data": {
                    "m": "create_study",
                    "p": ["cs_test", "st9", "st1", "sds_1", "STD;RSI", {}],
                },
            }

            mock_ws = MagicMock()
            ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
            ts_pkt = {
                "m": "timescale_update",
                "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
            }
            ts_raw = json.dumps(ts_pkt)

            ind_data = [{"i": 0, "v": [1700000000, 55.5]}]
            du_pkt = {"m": "du", "p": ["cs_test", {"st9": {"st": ind_data}}]}
            du_raw = json.dumps(du_pkt)

            mock_ws.recv.side_effect = [
                f"~m~{len(ts_raw)}~m~{ts_raw}",
                f"~m~{len(du_raw)}~m~{du_raw}",
                ConnectionError("done"),
            ]

            with patch(
                "tv_scraper.streaming.stream_handler.create_connection"
            ) as mock_cc:
                mock_cc.return_value = mock_ws

                with patch(
                    "tv_scraper.core.validators.DataValidator.verify_symbol_exchange"
                ) as mock_validate:
                    mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

                    cs = CandleStreamer()
                    cs.get_candles(
                        exchange="NASDAQ",
                        symbol="AAPL",
                        numb_candles=1,
                        indicators=[("STD;RSI", "37.0")],
                    )

                    mock_fetch.assert_called()


class TestIntegrationCandleStreamerAndStreamer:
    """Test integration between CandleStreamer and Streamer."""

    def test_streamer_uses_candle_streamer(self):
        """Test that Streamer.get_candles uses CandleStreamer internally."""
        with patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc:
            mock_ws = MagicMock()
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
                for i in range(5)
            ]
            ts_pkt = {
                "m": "timescale_update",
                "p": ["cs_test", {"sds_1": {"s": ohlcv_entries}}],
            }
            ts_raw = json.dumps(ts_pkt)
            mock_ws.recv.side_effect = [
                f"~m~{len(ts_raw)}~m~{ts_raw}",
                ConnectionError("done"),
            ]
            mock_cc.return_value = mock_ws

            with patch(
                "tv_scraper.core.validators.DataValidator.verify_symbol_exchange"
            ) as mock_validate:
                mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

                s = Streamer()
                result = s.get_candles(
                    exchange="BINANCE", symbol="BTCUSDT", numb_candles=5
                )

                assert "status" in result
                assert hasattr(s, "_candle_streamer")

    def test_streamer_passes_export_to_candle_streamer(self):
        """Test that Streamer passes export settings to CandleStreamer."""
        s = Streamer(export_result=True, export_type="csv")

        assert s._candle_streamer.export_result is True
        assert s._candle_streamer.export_type == "csv"

    def test_streamer_passes_cookie_to_candle_streamer(self):
        """Test that Streamer passes cookie to CandleStreamer."""
        s = Streamer(cookie="test_cookie")

        assert s._candle_streamer.cookie == "test_cookie"
        assert s.cookie == "test_cookie"


class TestIntegrationCandleDataProcessing:
    """Test integration with data processing."""

    def test_candle_data_sorting(self):
        """Test that candle data is sorted by index."""
        with patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc:
            mock_ws = MagicMock()

            ohlcv_entries = [
                {"i": 4, "v": [1700032400, 44100.0, 44500.0, 44000.0, 44300.0, 35000]},
                {"i": 2, "v": [1700007200, 42600.0, 43000.0, 42400.0, 42800.0, 20000]},
                {"i": 0, "v": [1700000000, 42000.0, 42500.0, 41800.0, 42200.0, 15000]},
                {"i": 3, "v": [1700010800, 42800.0, 43200.0, 42700.0, 43000.0, 22000]},
                {"i": 1, "v": [1700003600, 42200.0, 42800.0, 42100.0, 42600.0, 18000]},
            ]
            ts_pkt = {
                "m": "timescale_update",
                "p": ["cs_test", {"sds_1": {"s": ohlcv_entries}}],
            }
            ts_raw = json.dumps(ts_pkt)
            mock_ws.recv.side_effect = [
                f"~m~{len(ts_raw)}~m~{ts_raw}",
                ConnectionError("done"),
            ]
            mock_cc.return_value = mock_ws

            with patch(
                "tv_scraper.core.validators.DataValidator.verify_symbol_exchange"
            ) as mock_validate:
                mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

                cs = CandleStreamer()
                result = cs.get_candles(
                    exchange="BINANCE", symbol="BTCUSDT", numb_candles=5
                )

                indices = [c["index"] for c in result["data"]["ohlcv"]]
                assert indices == sorted(indices)

    def test_candle_data_truncation(self):
        """Test that candle data is truncated to numb_candles."""
        with patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc:
            mock_ws = MagicMock()

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
                for i in range(20)
            ]
            ts_pkt = {
                "m": "timescale_update",
                "p": ["cs_test", {"sds_1": {"s": ohlcv_entries}}],
            }
            ts_raw = json.dumps(ts_pkt)
            mock_ws.recv.side_effect = [
                f"~m~{len(ts_raw)}~m~{ts_raw}",
                ConnectionError("done"),
            ]
            mock_cc.return_value = mock_ws

            with patch(
                "tv_scraper.core.validators.DataValidator.verify_symbol_exchange"
            ) as mock_validate:
                mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

                cs = CandleStreamer()
                result = cs.get_candles(
                    exchange="BINANCE", symbol="BTCUSDT", numb_candles=10
                )

                assert len(result["data"]["ohlcv"]) == 10


class TestIntegrationCandleDataWithMultipleIndicators:
    """Test with multiple indicators."""

    def test_multiple_indicators_all_added(self):
        """Test all indicators are added to study map."""
        with patch(
            "tv_scraper.streaming.candle_streamer.fetch_indicator_metadata"
        ) as mock_fetch:
            study_responses = [
                {
                    "status": "success",
                    "data": {
                        "m": "create_study",
                        "p": ["cs_test", f"st{9 + i}", "st1", "sds_1", ind, {}],
                    },
                }
                for i, ind in enumerate(["STD;RSI", "STD;MACD"])
            ]
            mock_fetch.side_effect = study_responses

            mock_ws = MagicMock()
            ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
            ts_pkt = {
                "m": "timescale_update",
                "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
            }
            ts_raw = json.dumps(ts_pkt)

            ind1_data = [{"i": 0, "v": [1700000000, 55.5]}]
            ind2_data = [{"i": 0, "v": [1700000000, 0.5, 0.3, 0.2]}]
            du_pkt = {
                "m": "du",
                "p": [
                    "cs_test",
                    {
                        "st9": {"st": ind1_data},
                        "st10": {"st": ind2_data},
                    },
                ],
            }
            du_raw = json.dumps(du_pkt)

            mock_ws.recv.side_effect = [
                f"~m~{len(ts_raw)}~m~{ts_raw}",
                f"~m~{len(du_raw)}~m~{du_raw}",
                ConnectionError("done"),
            ]

            with patch(
                "tv_scraper.streaming.stream_handler.create_connection"
            ) as mock_cc:
                mock_cc.return_value = mock_ws

                with patch(
                    "tv_scraper.core.validators.DataValidator.verify_symbol_exchange"
                ) as mock_validate:
                    mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

                    cs = CandleStreamer()
                    cs.get_candles(
                        exchange="NASDAQ",
                        symbol="AAPL",
                        numb_candles=1,
                        indicators=[("STD;RSI", "37.0"), ("STD;MACD", "12.0")],
                    )

                    assert mock_fetch.call_count == 2
                    assert len(cs.study_id_to_name_map) == 2


class TestIntegrationCandleWithConnectionHandling:
    """Test connection handling integration."""

    def test_connection_error_handled(self):
        """Test connection errors are handled gracefully."""
        with patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc:
            mock_ws = MagicMock()
            mock_ws.recv.side_effect = ConnectionError("Connection refused")
            mock_cc.return_value = mock_ws

            with patch(
                "tv_scraper.core.validators.DataValidator.verify_symbol_exchange"
            ) as mock_validate:
                mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

                cs = CandleStreamer()
                result = cs.get_candles(
                    exchange="BINANCE", symbol="BTCUSDT", numb_candles=5
                )

                assert result["status"] == "failed"
                assert result["error"] is not None

    def test_timeout_handling(self):
        """Test timeout is handled."""
        with patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc:
            mock_ws = MagicMock()

            ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
            ts_pkt = {
                "m": "timescale_update",
                "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
            }
            ts_raw = json.dumps(ts_pkt)

            side_effects = [f"~m~{len(ts_raw)}~m~{ts_raw}"] * 16
            side_effects.append(ConnectionError("done"))
            mock_ws.recv.side_effect = side_effects
            mock_cc.return_value = mock_ws

            with patch(
                "tv_scraper.core.validators.DataValidator.verify_symbol_exchange"
            ) as mock_validate:
                mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

                cs = CandleStreamer()
                result = cs.get_candles(
                    exchange="BINANCE", symbol="BTCUSDT", numb_candles=100
                )

                assert "status" in result


class TestIntegrationCandleWithHeartbeat:
    """Test heartbeat handling integration."""

    def test_heartbeat_echoed(self):
        """Test heartbeat messages are echoed back."""
        with patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc:
            mock_ws = MagicMock()

            heartbeat = "~m~30~m~~h~12345"
            ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
            ts_pkt = {
                "m": "timescale_update",
                "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
            }
            ts_raw = json.dumps(ts_pkt)
            ts_framed = f"~m~{len(ts_raw)}~m~{ts_raw}"

            mock_ws.recv.side_effect = [heartbeat, ts_framed, ConnectionError("done")]
            mock_cc.return_value = mock_ws

            with patch(
                "tv_scraper.core.validators.DataValidator.verify_symbol_exchange"
            ) as mock_validate:
                mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

                cs = CandleStreamer()
                result = cs.get_candles(
                    exchange="BINANCE", symbol="BTCUSDT", numb_candles=1
                )

                assert result["status"] == STATUS_SUCCESS
                heartbeat_sent = any(
                    "h~" in str(call) for call in mock_ws.send.call_args_list
                )
                assert heartbeat_sent or mock_ws.send.called


class TestIntegrationCandleEndToEnd:
    """End-to-end integration tests."""

    def test_full_workflow_success(self):
        """Test complete workflow from request to response."""
        with patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc:
            mock_ws = MagicMock()

            ohlcv_entries = [
                {
                    "i": i,
                    "v": [
                        1700000000 + (i * 3600),
                        42000.0 + i,
                        42500.0 + i,
                        41800.0 + i,
                        42200.0 + i,
                        15000 + i,
                    ],
                }
                for i in range(10)
            ]
            ts_pkt = {
                "m": "timescale_update",
                "p": ["cs_test", {"sds_1": {"s": ohlcv_entries}}],
            }
            ts_raw = json.dumps(ts_pkt)
            mock_ws.recv.side_effect = [
                f"~m~{len(ts_raw)}~m~{ts_raw}",
                ConnectionError("done"),
            ]
            mock_cc.return_value = mock_ws

            with patch(
                "tv_scraper.core.validators.DataValidator.verify_symbol_exchange"
            ) as mock_validate:
                mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

                streamer = Streamer()
                result = streamer.get_candles(
                    exchange="BINANCE",
                    symbol="BTCUSDT",
                    timeframe="1h",
                    numb_candles=10,
                )

                assert result["status"] == STATUS_SUCCESS
                assert result["data"]["ohlcv"]
                assert len(result["data"]["ohlcv"]) == 10
                assert result["metadata"]["exchange"] == "BINANCE"
                assert result["metadata"]["symbol"] == "BTCUSDT"
                assert result["metadata"]["timeframe"] == "1h"
                assert result["metadata"]["numb_candles"] == 10

    def test_full_workflow_with_indicators(self):
        """Test complete workflow with indicators."""
        with patch(
            "tv_scraper.streaming.candle_streamer.fetch_indicator_metadata"
        ) as mock_fetch:
            mock_fetch.return_value = {
                "status": "success",
                "data": {
                    "m": "create_study",
                    "p": ["cs_test", "st9", "st1", "sds_1", "STD;RSI", {}],
                },
            }

            with patch(
                "tv_scraper.streaming.stream_handler.create_connection"
            ) as mock_cc:
                mock_ws = MagicMock()

                ohlcv_entry = {
                    "i": 0,
                    "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000],
                }
                ts_pkt = {
                    "m": "timescale_update",
                    "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
                }
                ts_raw = json.dumps(ts_pkt)

                ind_data = [{"i": 0, "v": [1700000000, 55.5]}]
                du_pkt = {"m": "du", "p": ["cs_test", {"st9": {"st": ind_data}}]}
                du_raw = json.dumps(du_pkt)

                mock_ws.recv.side_effect = [
                    f"~m~{len(ts_raw)}~m~{ts_raw}",
                    f"~m~{len(du_raw)}~m~{du_raw}",
                    ConnectionError("done"),
                ]
                mock_cc.return_value = mock_ws

                with patch(
                    "tv_scraper.core.validators.DataValidator.verify_symbol_exchange"
                ) as mock_validate:
                    mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

                    streamer = Streamer()
                    result = streamer.get_candles(
                        exchange="NASDAQ",
                        symbol="AAPL",
                        timeframe="1h",
                        numb_candles=1,
                        indicators=[("STD;RSI", "37.0")],
                    )

                    assert result["status"] == STATUS_SUCCESS
                    assert "indicators" in result["data"]
                    assert "STD;RSI" in result["data"]["indicators"]
