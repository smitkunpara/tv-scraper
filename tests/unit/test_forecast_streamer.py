"""Unit tests for ForecastStreamer.

Comprehensive tests covering valid inputs, invalid inputs, edge cases,
and various parameter combinations using mocking - no actual WebSocket connections.
"""

import json
from unittest.mock import MagicMock, patch

import requests

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.streaming.forecast_streamer import ForecastStreamer


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

    def test_cookie_from_env(self, monkeypatch):
        """Test cookie from environment variable."""
        monkeypatch.setenv("TRADINGVIEW_COOKIE", "env_cookie")
        fs = ForecastStreamer()
        assert fs.cookie == "env_cookie"

    def test_cookie_param_overrides_env(self, monkeypatch):
        """Test cookie parameter overrides environment."""
        monkeypatch.setenv("TRADINGVIEW_COOKIE", "env_cookie")
        fs = ForecastStreamer(cookie="param_cookie")
        assert fs.cookie == "param_cookie"


class TestInheritance:
    """Test that ForecastStreamer inherits from BaseStreamer/BaseScraper."""

    def test_inherits_from_base_scraper(self):
        """Verify ForecastStreamer inherits BaseScraper methods."""
        fs = ForecastStreamer()
        assert hasattr(fs, "_success_response")
        assert hasattr(fs, "_error_response")
        assert hasattr(fs, "_export")

    def test_inherits_connect_method(self):
        """Verify connect method exists."""
        fs = ForecastStreamer()
        assert hasattr(fs, "connect")
        assert callable(fs.connect)


class TestGetForecastInvalidInputs:
    """Test get_forecast with invalid inputs."""

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    def test_empty_exchange(self, mock_cc):
        """Test empty exchange returns error."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="", symbol="A")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    def test_empty_symbol(self, mock_cc):
        """Test empty symbol returns error."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="NYSE", symbol="")

        assert result["status"] == STATUS_FAILED

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    def test_null_exchange(self, mock_cc):
        """Test null exchange returns error."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange=None, symbol="A")

        assert result["status"] == STATUS_FAILED

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    def test_null_symbol(self, mock_cc):
        """Test null symbol returns error."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="NYSE", symbol=None)

        assert result["status"] == STATUS_FAILED

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    def test_whitespace_only_exchange(self, mock_cc):
        """Test whitespace-only exchange returns error."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="   ", symbol="A")

        assert result["status"] == STATUS_FAILED

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    def test_whitespace_only_symbol(self, mock_cc):
        """Test whitespace-only symbol returns error."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="NYSE", symbol="   ")

        assert result["status"] == STATUS_FAILED


class TestGetForecastNonStockSymbol:
    """Test get_forecast with non-stock symbols."""

    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_crypto_symbol_returns_error(self, mock_get):
        """Test crypto symbol returns error."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"type": "crypto"}
        mock_get.return_value = mock_response

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="BINANCE", symbol="BTCUSDT")

        assert result["status"] == STATUS_FAILED
        assert "crypto" in result["error"]

    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_forex_symbol_returns_error(self, mock_get):
        """Test forex symbol returns error."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"type": "forex"}
        mock_get.return_value = mock_response

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="FX", symbol="EURUSD")

        assert result["status"] == STATUS_FAILED
        assert "forex" in result["error"]

    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_index_symbol_returns_error(self, mock_get):
        """Test index symbol returns error."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"type": "index"}
        mock_get.return_value = mock_response

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="INDEX", symbol="SPX")

        assert result["status"] == STATUS_FAILED
        assert "index" in result["error"]

    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_etf_symbol_returns_error(self, mock_get):
        """Test ETF symbol returns error."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"type": "etf"}
        mock_get.return_value = mock_response

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="NYSE", symbol="SPY")

        assert result["status"] == STATUS_FAILED
        assert "etf" in result["error"]


class TestGetForecastSymbolTypeResolution:
    """Test symbol type resolution edge cases."""

    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_network_error_raises(self, mock_get):
        """Test network error during symbol type check raises."""
        mock_get.side_effect = requests.RequestException("Network error")

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="NYSE", symbol="A")

        assert result["status"] == STATUS_FAILED

    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_invalid_json_response_raises(self, mock_get):
        """Test invalid JSON response raises."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="NYSE", symbol="A")

        assert result["status"] == STATUS_FAILED

    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_missing_type_field(self, mock_get):
        """Test missing type field in response."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {}  # No type field
        mock_get.return_value = mock_response

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="NYSE", symbol="A")

        # Missing type treated as non-stock
        assert result["status"] == STATUS_FAILED


class TestGetForecastValidStock:
    """Test get_forecast with valid stock symbols."""

    def _make_mock_qsd_packets(self, with_all_fields: bool = True) -> list:
        """Create mock WebSocket packets with forecast data."""
        # Full qsd packet with all forecast fields
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

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_stock_symbol_success(self, mock_get, mock_cc):
        """Test successful forecast fetch for stock symbol."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        # Mock symbol type response
        type_response = MagicMock()
        type_response.raise_for_status = MagicMock()
        type_response.json.return_value = {"type": "stock"}
        mock_get.return_value = type_response

        mock_ws.recv.side_effect = self._make_mock_qsd_packets()

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="NYSE", symbol="A")

        assert result["status"] == STATUS_SUCCESS
        assert "revenue_currency" in result["data"]
        assert result["data"]["revenue_currency"] == "USD"

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_multiple_stock_symbols(self, mock_get, mock_cc):
        """Test with multiple different stock symbols."""
        type_response = MagicMock()
        type_response.raise_for_status = MagicMock()
        type_response.json.return_value = {"type": "stock"}
        mock_get.return_value = type_response

        def fresh_ws(*args, **kwargs):
            """Return a fresh mock WebSocket with new recv packets each call."""
            mock_ws = MagicMock()
            mock_ws.recv.side_effect = self._make_mock_qsd_packets()
            return mock_ws

        mock_cc.side_effect = fresh_ws

        fs = ForecastStreamer()

        symbols = [
            ("NYSE", "A"),
            ("NASDAQ", "AAPL"),
            ("NASDAQ", "MSFT"),
            ("NYSE", "IBM"),
        ]

        for exchange, symbol in symbols:
            result = fs.get_forecast(exchange=exchange, symbol=symbol)
            assert result["status"] == STATUS_SUCCESS, f"Failed for {exchange}:{symbol}"
            assert result["metadata"]["exchange"] == exchange
            assert result["metadata"]["symbol"] == symbol


class TestGetForecastPartialData:
    """Test get_forecast with partial data."""

    def _make_partial_qsd_packets(self) -> list:
        """Create mock WebSocket packets with partial forecast data."""
        # Only some fields
        qsd_data = {
            "fundamental_currency_code": "USD",
            "price_target_average": 162.8,
            "price_target_high": 185.0,
            "price_target_low": 145.0,
            "price_target_median": 160.0,
            # Missing: regular_close, earnings, revenues
        }

        qsd_pkt = {"m": "qsd", "p": ["qs_test", {"v": qsd_data}]}
        qsd_raw = json.dumps(qsd_pkt)
        qsd_framed = f"~m~{len(qsd_raw)}~m~{qsd_raw}"

        return [qsd_framed, ConnectionError("done")]

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_partial_data_returns_failed_with_data(self, mock_get, mock_cc):
        """Test partial data returns failed status with available data."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        type_response = MagicMock()
        type_response.raise_for_status = MagicMock()
        type_response.json.return_value = {"type": "stock"}
        mock_get.return_value = type_response

        mock_ws.recv.side_effect = self._make_partial_qsd_packets()

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="NYSE", symbol="A")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is not None
        # Output uses mapped key names (e.g. average_price_target, not price_target_average)
        assert "average_price_target" in result["data"]
        assert "failed to fetch keys" in result["error"]


class TestGetForecastExport:
    """Test export functionality."""

    def _make_mock_packets(self) -> list:
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

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    @patch("tv_scraper.core.base.save_json_file")
    def test_export_json(self, mock_save, mock_get, mock_cc):
        """Test JSON export."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        type_response = MagicMock()
        type_response.raise_for_status = MagicMock()
        type_response.json.return_value = {"type": "stock"}
        mock_get.return_value = type_response

        mock_ws.recv.side_effect = self._make_mock_packets()

        fs = ForecastStreamer(export_result=True, export_type="json")
        fs.get_forecast(exchange="NYSE", symbol="A")

        assert mock_save.called

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    @patch("tv_scraper.core.base.save_csv_file")
    def test_export_csv(self, mock_save, mock_get, mock_cc):
        """Test CSV export (patches BaseScraper._export which calls save_csv_file)."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        type_response = MagicMock()
        type_response.raise_for_status = MagicMock()
        type_response.json.return_value = {"type": "stock"}
        mock_get.return_value = type_response

        mock_ws.recv.side_effect = self._make_mock_packets()

        fs = ForecastStreamer(export_result=True, export_type="csv")
        fs.get_forecast(exchange="NYSE", symbol="A")

        assert mock_save.called


class TestGetForecastMetadata:
    """Test metadata in responses."""

    def _make_mock_packets(self) -> list:
        qsd_data = {
            "fundamental_currency_code": "USD",
            "regular_close": 114.5,
            "price_target_average": 162.8,
            "price_target_high": 185.0,
            "price_target_low": 145.0,
            "price_target_median": 160.0,
            "earnings_fy_h": [{"FiscalPeriod": "2026", "Estimate": 5.9}],
            "earnings_fq_h": None,
            "revenues_fy_h": None,
            "revenues_fq_h": None,
        }
        qsd_pkt = {"m": "qsd", "p": ["qs_test", {"v": qsd_data}]}
        qsd_raw = json.dumps(qsd_pkt)
        qsd_framed = f"~m~{len(qsd_raw)}~m~{qsd_raw}"
        return [qsd_framed, ConnectionError("done")]

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_success_metadata(self, mock_get, mock_cc):
        """Test success metadata contains exchange and symbol."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        type_response = MagicMock()
        type_response.raise_for_status = MagicMock()
        type_response.json.return_value = {"type": "stock"}
        mock_get.return_value = type_response

        mock_ws.recv.side_effect = self._make_mock_packets()

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="NASDAQ", symbol="AAPL")

        assert result["metadata"]["exchange"] == "NASDAQ"
        assert result["metadata"]["symbol"] == "AAPL"
        assert "available_output_keys" in result["metadata"]

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_partial_data_metadata(self, mock_get, mock_cc):
        """Test partial data metadata contains available keys."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        type_response = MagicMock()
        type_response.raise_for_status = MagicMock()
        type_response.json.return_value = {"type": "stock"}
        mock_get.return_value = type_response

        # Create partial data
        qsd_data = {
            "fundamental_currency_code": "USD",
            "price_target_average": 162.8,
        }
        qsd_pkt = {"m": "qsd", "p": ["qs_test", {"v": qsd_data}]}
        qsd_raw = json.dumps(qsd_pkt)
        qsd_framed = f"~m~{len(qsd_raw)}~m~{qsd_raw}"
        mock_ws.recv.side_effect = [qsd_framed, ConnectionError("done")]

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="NYSE", symbol="A")

        assert "available_output_keys" in result["metadata"]
        # Output uses mapped key names: fundamental_currency_code → revenue_currency
        assert "revenue_currency" in result["metadata"]["available_output_keys"]
        assert "average_price_target" in result["metadata"]["available_output_keys"]


class TestGetForecastResponseEnvelope:
    """Test standardized response envelope."""

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_success_has_all_keys(self, mock_get, mock_cc):
        """Test success response has required keys."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        type_response = MagicMock()
        type_response.raise_for_status = MagicMock()
        type_response.json.return_value = {"type": "stock"}
        mock_get.return_value = type_response

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
        mock_ws.recv.side_effect = [qsd_framed, ConnectionError("done")]

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="NYSE", symbol="A")

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_error_has_all_keys(self, mock_get, mock_cc):
        """Test error response has required keys."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        type_response = MagicMock()
        type_response.raise_for_status = MagicMock()
        type_response.json.return_value = {"type": "crypto"}
        mock_get.return_value = type_response

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="BINANCE", symbol="BTCUSDT")

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_partial_failure_has_data(self, mock_get, mock_cc):
        """Test partial failure contains partial data."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        type_response = MagicMock()
        type_response.raise_for_status = MagicMock()
        type_response.json.return_value = {"type": "stock"}
        mock_get.return_value = type_response

        qsd_data = {
            "fundamental_currency_code": "USD",
            "price_target_average": 162.8,
        }
        qsd_pkt = {"m": "qsd", "p": ["qs_test", {"v": qsd_data}]}
        qsd_raw = json.dumps(qsd_pkt)
        qsd_framed = f"~m~{len(qsd_raw)}~m~{qsd_raw}"
        mock_ws.recv.side_effect = [qsd_framed, ConnectionError("done")]

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="NYSE", symbol="A")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is not None
        assert "available_output_keys" in result["metadata"]


class TestGetForecastDataFields:
    """Test individual data fields in forecast response."""

    def _make_full_packets(self) -> list:
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

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_all_price_target_fields(self, mock_get, mock_cc):
        """Test all price target fields are present."""
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

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_eps_data_fields(self, mock_get, mock_cc):
        """Test EPS data fields."""
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

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_revenue_data_fields(self, mock_get, mock_cc):
        """Test revenue data fields."""
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


class TestGetForecastConnect:
    """Test connect method."""

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    def test_connect_without_cookie(self, mock_cc):
        """Test connect without cookie uses unauthorized token."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        fs = ForecastStreamer()
        fs.connect()

        mock_cc.assert_called_once()

    @patch("tv_scraper.streaming.auth.get_valid_jwt_token")
    @patch("tv_scraper.streaming.base_streamer.create_connection")
    def test_connect_with_cookie(self, mock_cc, mock_jwt):
        """Test connect with cookie resolves JWT."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws
        mock_jwt.return_value = "resolved_jwt_token"

        fs = ForecastStreamer(cookie="test_cookie")
        fs.connect()

        mock_jwt.assert_called_once_with("test_cookie")


class TestGetForecastEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_special_characters_in_symbol(self, mock_get, mock_cc):
        """Test symbol with special characters."""
        mock_ws = MagicMock()
        mock_ws.recv.side_effect = [ConnectionError("done")]
        mock_cc.return_value = mock_ws
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"type": "stock"}
        mock_get.return_value = mock_response

        fs = ForecastStreamer()

        # Some symbols might have special chars
        result = fs.get_forecast(exchange="NYSE", symbol="BRK.A")
        assert "status" in result

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_case_sensitivity(self, mock_get, mock_cc):
        """Test case insensitivity for exchange."""
        mock_ws = MagicMock()
        mock_ws.recv.side_effect = [ConnectionError("done"), ConnectionError("done")]
        mock_cc.return_value = mock_ws
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"type": "stock"}
        mock_get.return_value = mock_response

        fs = ForecastStreamer()

        # Should work with different cases
        result = fs.get_forecast(exchange="nyse", symbol="a")
        assert "status" in result
        result = fs.get_forecast(exchange="NYSE", symbol="a")
        assert "status" in result


class TestGetForecastErrorScenarios:
    """Test various error scenarios."""

    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_http_error_on_symbol_check(self, mock_get):
        """Test HTTP error during symbol type check."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404")
        mock_get.return_value = mock_response

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="NYSE", symbol="A")

        assert result["status"] == STATUS_FAILED

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_timeout_on_websocket(self, mock_get, mock_cc):
        """Test timeout scenario on WebSocket."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        type_response = MagicMock()
        type_response.raise_for_status = MagicMock()
        type_response.json.return_value = {"type": "stock"}
        mock_get.return_value = type_response

        # Simulate timeout - send many packets without full data
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

        # Should return partial or failed
        assert "status" in result
