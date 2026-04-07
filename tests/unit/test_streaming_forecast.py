"""Unit tests for forecast streaming.

Comprehensive isolated function tests with full mocking - no actual connections.
"""

import json
from unittest.mock import MagicMock, patch

import requests

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.streaming.forecast_streamer import (
    _FORECAST_SOURCE_KEY_MAP,
    ForecastStreamer,
)


class TestForecastSourceKeyMap:
    """Test the forecast source key mapping."""

    def test_all_required_keys_mapped(self):
        """Verify all required output keys are mapped."""
        expected_keys = {
            "revenue_currency",
            "previous_close_price",
            "average_price_target",
            "highest_price_target",
            "lowest_price_target",
            "median_price_target",
            "yearly_eps_data",
            "quarterly_eps_data",
            "yearly_revenue_data",
            "quarterly_revenue_data",
        }
        output_keys = set(_FORECAST_SOURCE_KEY_MAP.keys())
        assert output_keys == expected_keys

    def test_source_keys_unique(self):
        """Verify source keys are unique."""
        source_keys = list(_FORECAST_SOURCE_KEY_MAP.values())
        assert len(source_keys) == len(set(source_keys))


class TestForecastStreamerInit:
    """Tests for ForecastStreamer initialization."""

    def test_default_init(self):
        """Test default initialization."""
        fs = ForecastStreamer()
        assert fs.export_result is False
        assert fs.export_type == "json"
        assert fs.cookie is None

    def test_custom_init(self):
        """Test custom initialization."""
        fs = ForecastStreamer(
            export_result=True, export_type="csv", cookie="test_cookie"
        )
        assert fs.export_result is True
        assert fs.export_type == "csv"
        assert fs.cookie == "test_cookie"


class TestForecastStreamerInheritance:
    """Test ForecastStreamer inheritance from BaseStreamer."""

    def test_inherits_base_scraper_methods(self):
        """Verify inherits BaseScraper methods."""
        fs = ForecastStreamer()
        assert hasattr(fs, "_success_response")
        assert hasattr(fs, "_error_response")
        assert hasattr(fs, "_export")

    def test_inherits_connect_method(self):
        """Verify connect method exists."""
        fs = ForecastStreamer()
        assert hasattr(fs, "connect")
        assert callable(fs.connect)


class TestForecastInvalidInputs:
    """Test get_forecast with invalid inputs."""

    def test_empty_exchange_returns_error(self):
        """Test empty exchange returns error."""
        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="", symbol="A")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None

    def test_empty_symbol_returns_error(self):
        """Test empty symbol returns error."""
        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="NYSE", symbol="")

        assert result["status"] == STATUS_FAILED

    def test_whitespace_only_exchange_returns_error(self):
        """Test whitespace-only exchange returns error."""
        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="   ", symbol="A")

        assert result["status"] == STATUS_FAILED


class TestForecastNonStockSymbol:
    """Test get_forecast rejects non-stock symbols."""

    def test_crypto_symbol_returns_error(self):
        """Test crypto symbol returns error."""
        with patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"type": "crypto"}
            mock_get.return_value = mock_response

            fs = ForecastStreamer()
            result = fs.get_forecast(exchange="BINANCE", symbol="BTCUSDT")

            assert result["status"] == STATUS_FAILED
            assert "crypto" in result["error"]
            assert "forecast is not available" in result["error"]

    def test_forex_symbol_returns_error(self):
        """Test forex symbol returns error."""
        with patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"type": "forex"}
            mock_get.return_value = mock_response

            fs = ForecastStreamer()
            result = fs.get_forecast(exchange="FX", symbol="EURUSD")

            assert result["status"] == STATUS_FAILED
            assert "forex" in result["error"]

    def test_index_symbol_returns_error(self):
        """Test index symbol returns error."""
        with patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"type": "index"}
            mock_get.return_value = mock_response

            fs = ForecastStreamer()
            result = fs.get_forecast(exchange="INDEX", symbol="SPX")

            assert result["status"] == STATUS_FAILED
            assert "index" in result["error"]

    def test_etf_symbol_returns_error(self):
        """Test ETF symbol returns error."""
        with patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"type": "etf"}
            mock_get.return_value = mock_response

            fs = ForecastStreamer()
            result = fs.get_forecast(exchange="NYSE", symbol="SPY")

            assert result["status"] == STATUS_FAILED
            assert "etf" in result["error"]


class TestForecastSymbolTypeResolution:
    """Test symbol type resolution edge cases."""

    def test_network_error_returns_failed(self):
        """Test network error returns failed status."""
        with patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("Network error")

            fs = ForecastStreamer()
            result = fs.get_forecast(exchange="NYSE", symbol="A")

            assert result["status"] == STATUS_FAILED

    def test_missing_type_field_returns_error(self):
        """Test missing type field returns error."""
        with patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {}
            mock_get.return_value = mock_response

            fs = ForecastStreamer()
            result = fs.get_forecast(exchange="NYSE", symbol="A")

            assert result["status"] == STATUS_FAILED


class TestForecastStockSuccess:
    """Test get_forecast with valid stock symbols."""

    @staticmethod
    def _make_full_qsd_packets() -> list:
        """Create full qsd packets with all forecast fields."""
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
            "earnings_fq_h": [{"FiscalPeriod": "2026-Q1", "Estimate": 1.36}],
            "revenues_fy_h": [{"FiscalPeriod": "2026", "Estimate": 7395056494}],
            "revenues_fq_h": [{"FiscalPeriod": "2026-Q1", "Estimate": 1807792308}],
        }
        qsd_pkt = {"m": "qsd", "p": ["qs_test", {"v": qsd_data}]}
        qsd_raw = json.dumps(qsd_pkt)
        qsd_framed = f"~m~{len(qsd_raw)}~m~{qsd_raw}"
        return [qsd_framed, ConnectionError("done")]

    def test_stock_symbol_success(self):
        """Test successful forecast for stock symbol."""
        with (
            patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get,
            patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc,
        ):
            mock_ws = MagicMock()
            mock_cc.return_value = mock_ws

            type_response = MagicMock()
            type_response.raise_for_status = MagicMock()
            type_response.json.return_value = {"type": "stock"}
            mock_get.return_value = type_response

            mock_ws.recv.side_effect = self._make_full_qsd_packets()

            fs = ForecastStreamer()
            result = fs.get_forecast(exchange="NYSE", symbol="A")

            assert result["status"] == STATUS_SUCCESS
            assert result["data"]["revenue_currency"] == "USD"

    def test_multiple_stock_symbols(self):
        """Test with multiple stock symbols."""
        with (
            patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get,
            patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc,
        ):
            type_response = MagicMock()
            type_response.raise_for_status = MagicMock()
            type_response.json.return_value = {"type": "stock"}
            mock_get.return_value = type_response

            def fresh_ws(*args, **kwargs):
                mock_ws = MagicMock()
                mock_ws.recv.side_effect = self._make_full_qsd_packets()
                return mock_ws

            mock_cc.side_effect = fresh_ws

            fs = ForecastStreamer()
            symbols = [
                ("NYSE", "A"),
                ("NASDAQ", "AAPL"),
                ("NASDAQ", "MSFT"),
            ]

            for exchange, symbol in symbols:
                result = fs.get_forecast(exchange=exchange, symbol=symbol)
                assert result["status"] == STATUS_SUCCESS, (
                    f"Failed for {exchange}:{symbol}"
                )


class TestForecastPartialData:
    """Test get_forecast with partial data."""

    @staticmethod
    def _make_partial_packets() -> list:
        """Create partial qsd packets."""
        qsd_data = {
            "fundamental_currency_code": "USD",
            "price_target_average": 162.8,
        }
        qsd_pkt = {"m": "qsd", "p": ["qs_test", {"v": qsd_data}]}
        qsd_raw = json.dumps(qsd_pkt)
        qsd_framed = f"~m~{len(qsd_raw)}~m~{qsd_raw}"
        return [qsd_framed, ConnectionError("done")]

    def test_partial_data_returns_failed_with_data(self):
        """Test partial data returns failed with available data."""
        with (
            patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get,
            patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc,
        ):
            mock_ws = MagicMock()
            mock_cc.return_value = mock_ws

            type_response = MagicMock()
            type_response.raise_for_status = MagicMock()
            type_response.json.return_value = {"type": "stock"}
            mock_get.return_value = type_response

            mock_ws.recv.side_effect = self._make_partial_packets()

            fs = ForecastStreamer()
            result = fs.get_forecast(exchange="NYSE", symbol="A")

            assert result["status"] == STATUS_FAILED
            assert result["data"] is not None
            assert "average_price_target" in result["data"]
            assert "failed to fetch keys" in result["error"]


class TestForecastResponseEnvelope:
    """Test standardized response envelope."""

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

    def test_success_has_all_keys(self):
        """Test success response has required keys."""
        with (
            patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get,
            patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc,
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

            assert "status" in result
            assert "data" in result
            assert "metadata" in result
            assert "error" in result
            assert result["status"] == STATUS_SUCCESS
            assert result["error"] is None

    def test_error_has_all_keys(self):
        """Test error response has required keys."""
        with patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"type": "crypto"}
            mock_get.return_value = mock_response

            fs = ForecastStreamer()
            result = fs.get_forecast(exchange="BINANCE", symbol="BTCUSDT")

            assert "status" in result
            assert "data" in result
            assert "metadata" in result
            assert "error" in result
            assert result["status"] == STATUS_FAILED
            assert result["data"] is None
            assert result["error"] is not None


class TestForecastDataFields:
    """Test individual data fields in forecast response."""

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
                {"FiscalPeriod": "2025-Q4", "Estimate": 1.28},
            ],
            "revenues_fy_h": [
                {"FiscalPeriod": "2026", "Estimate": 7395056494},
                {"FiscalPeriod": "2025", "Estimate": 6823456789},
            ],
            "revenues_fq_h": [
                {"FiscalPeriod": "2026-Q1", "Estimate": 1807792308},
                {"FiscalPeriod": "2025-Q4", "Estimate": 1756421356},
            ],
        }
        qsd_pkt = {"m": "qsd", "p": ["qs_test", {"v": qsd_data}]}
        qsd_raw = json.dumps(qsd_pkt)
        qsd_framed = f"~m~{len(qsd_raw)}~m~{qsd_raw}"
        return [qsd_framed, ConnectionError("done")]

    def test_all_price_target_fields(self):
        """Test all price target fields are present."""
        with (
            patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get,
            patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc,
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

            data = result["data"]
            assert "revenue_currency" in data
            assert "previous_close_price" in data
            assert "average_price_target" in data
            assert "highest_price_target" in data
            assert "lowest_price_target" in data
            assert "median_price_target" in data

    def test_eps_data_fields(self):
        """Test EPS data fields."""
        with (
            patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get,
            patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc,
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

            data = result["data"]
            assert "yearly_eps_data" in data
            assert "quarterly_eps_data" in data
            assert isinstance(data["yearly_eps_data"], list)
            assert isinstance(data["quarterly_eps_data"], list)

    def test_revenue_data_fields(self):
        """Test revenue data fields."""
        with (
            patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get,
            patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc,
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

            data = result["data"]
            assert "yearly_revenue_data" in data
            assert "quarterly_revenue_data" in data
            assert isinstance(data["yearly_revenue_data"], list)
            assert isinstance(data["quarterly_revenue_data"], list)


class TestForecastMetadata:
    """Test metadata in responses."""

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

    def test_success_metadata(self):
        """Test success metadata contains exchange and symbol."""
        with (
            patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get,
            patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc,
        ):
            mock_ws = MagicMock()
            mock_cc.return_value = mock_ws

            type_response = MagicMock()
            type_response.raise_for_status = MagicMock()
            type_response.json.return_value = {"type": "stock"}
            mock_get.return_value = type_response

            mock_ws.recv.side_effect = self._make_full_packets()

            fs = ForecastStreamer()
            result = fs.get_forecast(exchange="NASDAQ", symbol="AAPL")

            assert result["metadata"]["exchange"] == "NASDAQ"
            assert result["metadata"]["symbol"] == "AAPL"
            assert "available_output_keys" in result["metadata"]


class TestForecastExport:
    """Test export functionality."""

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
    def test_export_json(self, mock_save):
        """Test JSON export."""
        with (
            patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get,
            patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc,
        ):
            mock_ws = MagicMock()
            mock_cc.return_value = mock_ws

            type_response = MagicMock()
            type_response.raise_for_status = MagicMock()
            type_response.json.return_value = {"type": "stock"}
            mock_get.return_value = type_response

            mock_ws.recv.side_effect = self._make_full_packets()

            fs = ForecastStreamer(export_result=True, export_type="json")
            fs.get_forecast(exchange="NYSE", symbol="A")

            assert mock_save.called

    @patch("tv_scraper.core.base.save_csv_file")
    def test_export_csv(self, mock_save):
        """Test CSV export."""
        with (
            patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get,
            patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc,
        ):
            mock_ws = MagicMock()
            mock_cc.return_value = mock_ws

            type_response = MagicMock()
            type_response.raise_for_status = MagicMock()
            type_response.json.return_value = {"type": "stock"}
            mock_get.return_value = type_response

            mock_ws.recv.side_effect = self._make_full_packets()

            fs = ForecastStreamer(export_result=True, export_type="csv")
            fs.get_forecast(exchange="NYSE", symbol="A")

            assert mock_save.called


class TestForecastConnect:
    """Test connect method."""

    def test_connect_without_cookie(self):
        """Test connect without cookie."""
        with patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc:
            mock_ws = MagicMock()
            mock_cc.return_value = mock_ws

            fs = ForecastStreamer()
            fs.connect()

            mock_cc.assert_called_once()

    @patch("tv_scraper.streaming.auth.get_valid_jwt_token")
    def test_connect_with_cookie(self, mock_jwt):
        """Test connect with cookie resolves JWT."""
        with patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc:
            mock_ws = MagicMock()
            mock_cc.return_value = mock_ws
            mock_jwt.return_value = "resolved_jwt_token"

            fs = ForecastStreamer(cookie="test_cookie")
            fs.connect()

            mock_jwt.assert_called_once_with("test_cookie")


class TestForecastTimeout:
    """Test timeout scenarios."""

    def test_timeout_returns_partial_data(self):
        """Test timeout returns partial data."""
        with (
            patch("tv_scraper.streaming.forecast_streamer.requests.get") as mock_get,
            patch("tv_scraper.streaming.stream_handler.create_connection") as mock_cc,
        ):
            mock_ws = MagicMock()
            mock_cc.return_value = mock_ws

            type_response = MagicMock()
            type_response.raise_for_status = MagicMock()
            type_response.json.return_value = {"type": "stock"}
            mock_get.return_value = type_response

            packets = []
            for _ in range(20):
                qsd_data = {"fundamental_currency_code": "USD"}
                qsd_pkt = {"m": "qsd", "p": ["qs_test", {"v": qsd_data}]}
                qsd_raw = json.dumps(qsd_pkt)
                packets.append(f"~m~{len(qsd_raw)}~m~{qsd_raw}")
            packets.append(ConnectionError("done"))
            mock_ws.recv.side_effect = packets

            fs = ForecastStreamer()
            result = fs.get_forecast(exchange="NYSE", symbol="A")

            assert "status" in result
