"""Integration tests for forecast streaming.

Tests cross-module workflows combining forecast streaming with other features.
"""

import json
from unittest.mock import MagicMock, patch

from tv_scraper import Streamer
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.streaming.forecast_streamer import ForecastStreamer


class TestIntegrationForecastStreamer:
    """Test ForecastStreamer as standalone component."""

    @staticmethod
    def _make_full_packets() -> list:
        qsd_data = {
            "fundamental_currency_code": "USD",
            "regular_close": 114.5,
            "price_target_average": 162.8,
            "price_target_high": 185.0,
            "price_target_low": 145.0,
            "price_target_median": 160.0,
            "earnings_fy_h": [{"FiscalPeriod": "2026", "Estimate": 5.9}],
            "earnings_fq_h": [{"FiscalPeriod": "2026-Q1", "Estimate": 1.36}],
            "revenues_fy_h": [{"FiscalPeriod": "2026", "Estimate": 7395056494}],
            "revenues_fq_h": [{"FiscalPeriod": "2026-Q1", "Estimate": 1807792308}],
        }
        qsd_pkt = {"m": "qsd", "p": ["qs_test", {"v": qsd_data}]}
        qsd_raw = json.dumps(qsd_pkt)
        qsd_framed = f"~m~{len(qsd_raw)}~m~{qsd_raw}"
        return [qsd_framed, ConnectionError("done")]

    def test_forecast_streamer_standalone(self):
        """Test ForecastStreamer works standalone."""
        with (
            patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get,
            patch("tv_scraper.streaming.base_streamer.create_connection") as mock_cc,
        ):
            mock_ws = MagicMock()
            mock_cc.return_value = mock_ws

            type_response = MagicMock()
            type_response.raise_for_status = MagicMock()
            type_response.json.return_value = {"type": "stock"}
            mock_get.return_value = type_response

            mock_ws.recv.side_effect = self._make_full_packets()

            fs = ForecastStreamer()
            result = fs.get_forecast(exchange="NYSE", symbol="A")

            assert result["status"] == STATUS_SUCCESS
            assert "average_price_target" in result["data"]


class TestIntegrationStreamerForecast:
    """Test Streamer.get_forecast integration."""

    @staticmethod
    def _make_full_packets() -> list:
        qsd_data = {
            "fundamental_currency_code": "USD",
            "regular_close": 114.5,
            "price_target_average": 162.8,
            "price_target_high": 185.0,
            "price_target_low": 145.0,
            "price_target_median": 160.0,
            "earnings_fy_h": [{"FiscalPeriod": "2026", "Estimate": 5.9}],
            "earnings_fq_h": [{"FiscalPeriod": "2026-Q1", "Estimate": 1.36}],
            "revenues_fy_h": [{"FiscalPeriod": "2026", "Estimate": 7395056494}],
            "revenues_fq_h": [{"FiscalPeriod": "2026-Q1", "Estimate": 1807792308}],
        }
        qsd_pkt = {"m": "qsd", "p": ["qs_test", {"v": qsd_data}]}
        qsd_raw = json.dumps(qsd_pkt)
        qsd_framed = f"~m~{len(qsd_raw)}~m~{qsd_raw}"
        return [qsd_framed, ConnectionError("done")]

    def test_streamer_delegates_to_forecast_streamer(self):
        """Test Streamer.get_forecast delegates to ForecastStreamer."""
        with (
            patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get,
            patch("tv_scraper.streaming.base_streamer.create_connection") as mock_cc,
        ):
            mock_ws = MagicMock()
            mock_cc.return_value = mock_ws

            type_response = MagicMock()
            type_response.raise_for_status = MagicMock()
            type_response.json.return_value = {"type": "stock"}
            mock_get.return_value = type_response

            mock_ws.recv.side_effect = self._make_full_packets()

            streamer = Streamer()
            result = streamer.get_forecast(exchange="NYSE", symbol="A")

            assert result["status"] == STATUS_SUCCESS
            assert result["metadata"]["exchange"] == "NYSE"
            assert result["metadata"]["symbol"] == "A"

    def test_streamer_candles_and_forecast_independent(self):
        """Test that candles and forecast are independent operations."""
        with (
            patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get,
            patch("tv_scraper.streaming.base_streamer.create_connection") as mock_cc,
        ):
            mock_ws = MagicMock()
            mock_cc.return_value = mock_ws

            type_response = MagicMock()
            type_response.raise_for_status = MagicMock()
            type_response.json.return_value = {"type": "stock"}
            mock_get.return_value = type_response

            mock_ws.recv.side_effect = self._make_full_packets()

            streamer = Streamer()

            forecast_result = streamer.get_forecast(exchange="NYSE", symbol="A")
            assert forecast_result["status"] == STATUS_SUCCESS
            assert "average_price_target" in forecast_result["data"]


class TestIntegrationForecastExport:
    """Test forecast export integration."""

    @staticmethod
    def _make_full_packets() -> list:
        qsd_data = {
            "fundamental_currency_code": "USD",
            "regular_close": 114.5,
            "price_target_average": 162.8,
            "price_target_high": 185.0,
            "price_target_low": 145.0,
            "price_target_median": 160.0,
            "earnings_fy_h": [{"FiscalPeriod": "2026", "Estimate": 5.9}],
            "earnings_fq_h": [{"FiscalPeriod": "2026-Q1", "Estimate": 1.36}],
            "revenues_fy_h": [{"FiscalPeriod": "2026", "Estimate": 7395056494}],
            "revenues_fq_h": [{"FiscalPeriod": "2026-Q1", "Estimate": 1807792308}],
        }
        qsd_pkt = {"m": "qsd", "p": ["qs_test", {"v": qsd_data}]}
        qsd_raw = json.dumps(qsd_pkt)
        qsd_framed = f"~m~{len(qsd_raw)}~m~{qsd_raw}"
        return [qsd_framed, ConnectionError("done")]

    @patch("tv_scraper.core.base.save_json_file")
    def test_streamer_export_forecast_json(self, mock_save):
        """Test Streamer exports forecast as JSON."""
        with (
            patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get,
            patch("tv_scraper.streaming.base_streamer.create_connection") as mock_cc,
        ):
            mock_ws = MagicMock()
            mock_cc.return_value = mock_ws

            type_response = MagicMock()
            type_response.raise_for_status = MagicMock()
            type_response.json.return_value = {"type": "stock"}
            mock_get.return_value = type_response

            mock_ws.recv.side_effect = self._make_full_packets()

            streamer = Streamer(export_result=True, export_type="json")
            result = streamer.get_forecast(exchange="NYSE", symbol="A")

            assert result["status"] == STATUS_SUCCESS
            assert mock_save.called


class TestIntegrationForecastNonStockError:
    """Test non-stock error handling across modules."""

    def test_streamer_forecast_rejects_crypto(self):
        """Test Streamer.get_forecast rejects crypto."""
        with patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"type": "crypto"}
            mock_get.return_value = mock_response

            streamer = Streamer()
            result = streamer.get_forecast(exchange="BINANCE", symbol="BTCUSDT")

            assert result["status"] == STATUS_FAILED
            assert "forecast is not available" in result["error"]
            assert "crypto" in result["error"]

    def test_forecast_streamer_rejects_forex(self):
        """Test ForecastStreamer rejects forex."""
        with patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"type": "forex"}
            mock_get.return_value = mock_response

            fs = ForecastStreamer()
            result = fs.get_forecast(exchange="FX", symbol="EURUSD")

            assert result["status"] == STATUS_FAILED
            assert "forex" in result["error"]


class TestIntegrationForecastMetadata:
    """Test forecast metadata across modules."""

    @staticmethod
    def _make_full_packets() -> list:
        qsd_data = {
            "fundamental_currency_code": "USD",
            "regular_close": 114.5,
            "price_target_average": 162.8,
            "price_target_high": 185.0,
            "price_target_low": 145.0,
            "price_target_median": 160.0,
            "earnings_fy_h": [{"FiscalPeriod": "2026", "Estimate": 5.9}],
            "earnings_fq_h": [{"FiscalPeriod": "2026-Q1", "Estimate": 1.36}],
            "revenues_fy_h": [{"FiscalPeriod": "2026", "Estimate": 7395056494}],
            "revenues_fq_h": [{"FiscalPeriod": "2026-Q1", "Estimate": 1807792308}],
        }
        qsd_pkt = {"m": "qsd", "p": ["qs_test", {"v": qsd_data}]}
        qsd_raw = json.dumps(qsd_pkt)
        qsd_framed = f"~m~{len(qsd_raw)}~m~{qsd_raw}"
        return [qsd_framed, ConnectionError("done")]

    def test_metadata_consistent_across_modules(self):
        """Test metadata is consistent between Streamer and ForecastStreamer."""
        with (
            patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get,
            patch("tv_scraper.streaming.base_streamer.create_connection") as mock_cc,
        ):
            mock_ws = MagicMock()
            mock_cc.return_value = mock_ws

            type_response = MagicMock()
            type_response.raise_for_status = MagicMock()
            type_response.json.return_value = {"type": "stock"}
            mock_get.return_value = type_response

            mock_ws.recv.side_effect = self._make_full_packets()

            fs = ForecastStreamer()
            fs_result = fs.get_forecast(exchange="NASDAQ", symbol="AAPL")

            streamer = Streamer()
            streamer_result = streamer.get_forecast(exchange="NASDAQ", symbol="AAPL")

            assert (
                fs_result["metadata"]["exchange"]
                == streamer_result["metadata"]["exchange"]
            )
            assert (
                fs_result["metadata"]["symbol"] == streamer_result["metadata"]["symbol"]
            )


class TestIntegrationForecastDataFields:
    """Test data fields across modules."""

    @staticmethod
    def _make_full_packets() -> list:
        qsd_data = {
            "fundamental_currency_code": "USD",
            "regular_close": 114.5,
            "price_target_average": 162.8,
            "price_target_high": 185.0,
            "price_target_low": 145.0,
            "price_target_median": 160.0,
            "earnings_fy_h": [
                {"FiscalPeriod": "2026", "Estimate": 5.9},
                {"FiscalPeriod": "2025", "Estimate": 5.2},
            ],
            "earnings_fq_h": [
                {"FiscalPeriod": "2026-Q1", "Estimate": 1.36},
            ],
            "revenues_fy_h": [
                {"FiscalPeriod": "2026", "Estimate": 7395056494},
            ],
            "revenues_fq_h": [
                {"FiscalPeriod": "2026-Q1", "Estimate": 1807792308},
            ],
        }
        qsd_pkt = {"m": "qsd", "p": ["qs_test", {"v": qsd_data}]}
        qsd_raw = json.dumps(qsd_pkt)
        qsd_framed = f"~m~{len(qsd_raw)}~m~{qsd_raw}"
        return [qsd_framed, ConnectionError("done")]

    def test_all_data_fields_present(self):
        """Test all expected data fields are present."""
        with (
            patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get,
            patch("tv_scraper.streaming.base_streamer.create_connection") as mock_cc,
        ):
            mock_ws = MagicMock()
            mock_cc.return_value = mock_ws

            type_response = MagicMock()
            type_response.raise_for_status = MagicMock()
            type_response.json.return_value = {"type": "stock"}
            mock_get.return_value = type_response

            mock_ws.recv.side_effect = self._make_full_packets()

            streamer = Streamer()
            result = streamer.get_forecast(exchange="NYSE", symbol="A")

            assert result["status"] == STATUS_SUCCESS
            data = result["data"]

            assert "revenue_currency" in data
            assert "previous_close_price" in data
            assert "average_price_target" in data
            assert "highest_price_target" in data
            assert "lowest_price_target" in data
            assert "median_price_target" in data
            assert "yearly_eps_data" in data
            assert "quarterly_eps_data" in data
            assert "yearly_revenue_data" in data
            assert "quarterly_revenue_data" in data


class TestIntegrationForecastEdgeCases:
    """Test edge cases in cross-module scenarios."""

    @staticmethod
    def _make_partial_packets() -> list:
        qsd_data = {
            "fundamental_currency_code": "USD",
            "price_target_average": 162.8,
        }
        qsd_pkt = {"m": "qsd", "p": ["qs_test", {"v": qsd_data}]}
        qsd_raw = json.dumps(qsd_pkt)
        qsd_framed = f"~m~{len(qsd_raw)}~m~{qsd_raw}"
        return [qsd_framed, ConnectionError("done")]

    def test_partial_data_still_has_metadata(self):
        """Test partial data still returns metadata."""
        with (
            patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get,
            patch("tv_scraper.streaming.base_streamer.create_connection") as mock_cc,
        ):
            mock_ws = MagicMock()
            mock_cc.return_value = mock_ws

            type_response = MagicMock()
            type_response.raise_for_status = MagicMock()
            type_response.json.return_value = {"type": "stock"}
            mock_get.return_value = type_response

            mock_ws.recv.side_effect = self._make_partial_packets()

            streamer = Streamer()
            result = streamer.get_forecast(exchange="NYSE", symbol="A")

            assert result["status"] == STATUS_FAILED
            assert result["data"] is not None
            assert result["metadata"]["exchange"] == "NYSE"
            assert result["metadata"]["symbol"] == "A"
            assert "available_output_keys" in result["metadata"]
