"""Mock tests for forecast streaming.

Uses saved JSON fixtures from live tests to simulate TradingView responses.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tv_scraper import Streamer
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.streaming.forecast_streamer import ForecastStreamer

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "streaming" / "forecast"


def load_fixture(name: str) -> dict:
    """Load a fixture file by name."""
    filepath = FIXTURES_DIR / f"{name}.json"
    with open(filepath) as f:
        return json.load(f)


class TestMockForecastStockSymbols:
    """Test forecast with mock data for stock symbols."""

    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        """Ensure fixtures exist."""
        if not FIXTURES_DIR.exists():
            pytest.skip("Fixtures directory not found")

    def _make_mock_packets_from_data(self, data: dict) -> list:
        """Create mock WebSocket packets from fixture data."""
        reverse_map = {
            "fundamental_currency_code": "revenue_currency",
            "regular_close": "previous_close_price",
            "price_target_average": "average_price_target",
            "price_target_high": "highest_price_target",
            "price_target_low": "lowest_price_target",
            "price_target_median": "median_price_target",
            "earnings_fy_h": "yearly_eps_data",
            "earnings_fq_h": "quarterly_eps_data",
            "revenues_fy_h": "yearly_revenue_data",
            "revenues_fq_h": "quarterly_revenue_data",
        }

        qsd_data = {}
        for src_key, out_key in reverse_map.items():
            if data.get(out_key) is not None:
                qsd_data[src_key] = data[out_key]

        qsd_pkt = {"m": "qsd", "p": ["qs_test", {"v": qsd_data}]}
        qsd_raw = json.dumps(qsd_pkt)
        qsd_framed = f"~m~{len(qsd_raw)}~m~{qsd_raw}"
        return [qsd_framed, ConnectionError("done")]

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_mock_forecast_nyse_a(self, mock_get, mock_cc):
        """Test mock forecast for NYSE:A."""
        try:
            fixture = load_fixture("nyse_a")
        except FileNotFoundError:
            pytest.skip("Fixture nyse_a.json not found")

        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        type_response = MagicMock()
        type_response.raise_for_status = MagicMock()
        type_response.json.return_value = {"type": "stock"}
        mock_get.return_value = type_response

        mock_ws.recv.side_effect = self._make_mock_packets_from_data(fixture["data"])

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="NYSE", symbol="A")

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["exchange"] == "NYSE"
        assert result["metadata"]["symbol"] == "A"

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_mock_forecast_nasdaq_aapl(self, mock_get, mock_cc):
        """Test mock forecast for NASDAQ:AAPL."""
        try:
            fixture = load_fixture("nasdaq_aapl")
        except FileNotFoundError:
            pytest.skip("Fixture nasdaq_aapl.json not found")

        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        type_response = MagicMock()
        type_response.raise_for_status = MagicMock()
        type_response.json.return_value = {"type": "stock"}
        mock_get.return_value = type_response

        mock_ws.recv.side_effect = self._make_mock_packets_from_data(fixture["data"])

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_mock_forecast_nasdaq_msft(self, mock_get, mock_cc):
        """Test mock forecast for NASDAQ:MSFT."""
        try:
            fixture = load_fixture("nasdaq_msft")
        except FileNotFoundError:
            pytest.skip("Fixture nasdaq_msft.json not found")

        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        type_response = MagicMock()
        type_response.raise_for_status = MagicMock()
        type_response.json.return_value = {"type": "stock"}
        mock_get.return_value = type_response

        mock_ws.recv.side_effect = self._make_mock_packets_from_data(fixture["data"])

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="NASDAQ", symbol="MSFT")

        assert result["status"] == STATUS_SUCCESS


class TestMockForecastNonStockRejection:
    """Test mock forecast rejects non-stock symbols."""

    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_mock_crypto_rejected(self, mock_get):
        """Test crypto symbol returns error."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"type": "crypto"}
        mock_get.return_value = mock_response

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="BINANCE", symbol="BTCUSDT")

        assert result["status"] == STATUS_FAILED
        assert "crypto" in result["error"]
        assert "forecast is not available" in result["error"]

    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_mock_forex_rejected(self, mock_get):
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
    def test_mock_index_rejected(self, mock_get):
        """Test index symbol returns error."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"type": "index"}
        mock_get.return_value = mock_response

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="INDEX", symbol="SPX")

        assert result["status"] == STATUS_FAILED
        assert "index" in result["error"]


class TestMockForecastDataFields:
    """Test mock forecast data fields."""

    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        """Ensure fixtures exist."""
        if not FIXTURES_DIR.exists():
            pytest.skip("Fixtures directory not found")

    def _make_full_packets(self) -> list:
        """Create full mock packets with all fields."""
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
    def test_all_price_targets_present(self, mock_get, mock_cc):
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

        assert result["status"] == STATUS_SUCCESS
        data = result["data"]
        assert data["revenue_currency"] == "USD"
        assert data["previous_close_price"] == 114.5
        assert data["average_price_target"] == 162.8
        assert data["highest_price_target"] == 185.0
        assert data["lowest_price_target"] == 145.0
        assert data["median_price_target"] == 160.0

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_eps_data_structure(self, mock_get, mock_cc):
        """Test EPS data structure is correct."""
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
        data = result["data"]
        assert len(data["yearly_eps_data"]) == 2
        assert len(data["quarterly_eps_data"]) == 2
        assert data["yearly_eps_data"][0]["FiscalPeriod"] == "2026"

    @patch("tv_scraper.streaming.base_streamer.create_connection")
    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_revenue_data_structure(self, mock_get, mock_cc):
        """Test revenue data structure is correct."""
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
        data = result["data"]
        assert len(data["yearly_revenue_data"]) == 2
        assert len(data["quarterly_revenue_data"]) == 2


class TestMockForecastResponseEnvelope:
    """Test mock response envelope."""

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
    def test_success_envelope_structure(self, mock_get, mock_cc):
        """Test success envelope has all required keys."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        type_response = MagicMock()
        type_response.raise_for_status = MagicMock()
        type_response.json.return_value = {"type": "stock"}
        mock_get.return_value = type_response

        mock_ws.recv.side_effect = self._make_mock_packets()

        fs = ForecastStreamer()
        result = fs.get_forecast(exchange="NYSE", symbol="A")

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None
        assert result["data"] is not None

    @patch("tv_scraper.streaming.forecast_streamer.requests.get")
    def test_error_envelope_structure(self, mock_get):
        """Test error envelope has all required keys."""
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


class TestMockForecastStreamerClass:
    """Test ForecastStreamer via Streamer class."""

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
    def test_streamer_get_forecast(self, mock_get, mock_cc):
        """Test Streamer.get_forecast delegates correctly."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        type_response = MagicMock()
        type_response.raise_for_status = MagicMock()
        type_response.json.return_value = {"type": "stock"}
        mock_get.return_value = type_response

        mock_ws.recv.side_effect = self._make_mock_packets()

        streamer = Streamer()
        result = streamer.get_forecast(exchange="NYSE", symbol="A")

        assert result["status"] == STATUS_SUCCESS
        assert "average_price_target" in result["data"]


class TestMockForecastExport:
    """Test mock export functionality."""

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
        """Test JSON export works."""
        mock_ws = MagicMock()
        mock_cc.return_value = mock_ws

        type_response = MagicMock()
        type_response.raise_for_status = MagicMock()
        type_response.json.return_value = {"type": "stock"}
        mock_get.return_value = type_response

        mock_ws.recv.side_effect = self._make_mock_packets()

        fs = ForecastStreamer(export="json")
        fs.get_forecast(exchange="NYSE", symbol="A")

        assert mock_save.called
