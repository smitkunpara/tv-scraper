"""Live API tests for forecast streaming.

Tests real WebSocket connections and forecast data streaming with TradingView.
Requires live TradingView connection.
"""

import os

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.streaming.forecast_streamer import ForecastStreamer


@pytest.mark.live
class TestLiveForecastStockSymbols:
    """Test forecast for valid stock symbols."""

    def test_live_forecast_nyse_a(self) -> None:
        """Verify forecast works for NYSE:A."""
        streamer = ForecastStreamer()
        result = streamer.get_forecast(exchange="NYSE", symbol="A")

        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None
        assert "data" in result
        assert result["metadata"]["exchange"] == "NYSE"
        assert result["metadata"]["symbol"] == "A"

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

    def test_live_forecast_nasdaq_aapl(self) -> None:
        """Verify forecast works for NASDAQ:AAPL."""
        streamer = ForecastStreamer()
        result = streamer.get_forecast(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None
        assert "data" in result
        assert result["metadata"]["symbol"] == "AAPL"

        data = result["data"]
        assert "average_price_target" in data
        assert "median_price_target" in data

    def test_live_forecast_nasdaq_msft(self) -> None:
        """Verify forecast works for NASDAQ:MSFT."""
        streamer = ForecastStreamer()
        result = streamer.get_forecast(exchange="NASDAQ", symbol="MSFT")

        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None
        assert "data" in result
        assert result["metadata"]["symbol"] == "MSFT"

        data = result["data"]
        assert "average_price_target" in data


@pytest.mark.live
class TestLiveForecastNonStockRejection:
    """Test forecast rejects non-stock symbols."""

    def test_live_forecast_crypto_rejected(self) -> None:
        """Verify forecast rejects crypto symbols."""
        streamer = ForecastStreamer()
        result = streamer.get_forecast(exchange="BINANCE", symbol="BTCUSDT")

        assert result["status"] == "failed"
        assert result["data"] is None
        assert "forecast is not available for this symbol because it is type:" in (
            result["error"] or ""
        )

    def test_live_forecast_forex_rejected(self) -> None:
        """Verify forecast rejects forex symbols."""
        streamer = ForecastStreamer()
        result = streamer.get_forecast(exchange="FX", symbol="EURUSD")

        assert result["status"] == "failed"
        assert result["data"] is None
        assert "forecast is not available for this symbol because it is type:" in (
            result["error"] or ""
        )

    def test_live_forecast_index_handling(self) -> None:
        """Verify forecast handles index symbols (may fail on validation)."""
        streamer = ForecastStreamer()
        result = streamer.get_forecast(exchange="INDEX", symbol="SPX")

        assert "status" in result
        if result["status"] == "failed":
            assert result["error"] is not None


@pytest.mark.live
class TestLiveForecastResponseEnvelope:
    """Test standardized response envelope."""

    def test_response_has_required_keys(self) -> None:
        """Verify response has all required keys."""
        streamer = ForecastStreamer()
        result = streamer.get_forecast(exchange="NYSE", symbol="A")

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result

    def test_success_metadata_fields(self) -> None:
        """Verify success metadata contains required fields."""
        streamer = ForecastStreamer()
        result = streamer.get_forecast(exchange="NYSE", symbol="A")

        if result["status"] == STATUS_SUCCESS:
            metadata = result["metadata"]
            assert "exchange" in metadata
            assert "symbol" in metadata
            assert "available_output_keys" in metadata


@pytest.mark.live
class TestLiveForecastDataTypes:
    """Test data types in forecast responses."""

    def test_price_target_are_floats(self) -> None:
        """Verify price target fields are floats."""
        streamer = ForecastStreamer()
        result = streamer.get_forecast(exchange="NYSE", symbol="A")

        if result["status"] == STATUS_SUCCESS:
            data = result["data"]
            if data.get("previous_close_price") is not None:
                assert isinstance(data["previous_close_price"], (int, float))
            if data.get("average_price_target") is not None:
                assert isinstance(data["average_price_target"], (int, float))
            if data.get("highest_price_target") is not None:
                assert isinstance(data["highest_price_target"], (int, float))
            if data.get("lowest_price_target") is not None:
                assert isinstance(data["lowest_price_target"], (int, float))
            if data.get("median_price_target") is not None:
                assert isinstance(data["median_price_target"], (int, float))

    def test_eps_data_are_lists(self) -> None:
        """Verify EPS data fields are lists."""
        streamer = ForecastStreamer()
        result = streamer.get_forecast(exchange="NYSE", symbol="A")

        if result["status"] == STATUS_SUCCESS:
            data = result["data"]
            if data.get("yearly_eps_data") is not None:
                assert isinstance(data["yearly_eps_data"], list)
            if data.get("quarterly_eps_data") is not None:
                assert isinstance(data["quarterly_eps_data"], list)

    def test_revenue_data_are_lists(self) -> None:
        """Verify revenue data fields are lists."""
        streamer = ForecastStreamer()
        result = streamer.get_forecast(exchange="NYSE", symbol="A")

        if result["status"] == STATUS_SUCCESS:
            data = result["data"]
            if data.get("yearly_revenue_data") is not None:
                assert isinstance(data["yearly_revenue_data"], list)
            if data.get("quarterly_revenue_data") is not None:
                assert isinstance(data["quarterly_revenue_data"], list)

    def test_revenue_currency_is_string(self) -> None:
        """Verify revenue currency is a string."""
        streamer = ForecastStreamer()
        result = streamer.get_forecast(exchange="NYSE", symbol="A")

        if result["status"] == STATUS_SUCCESS:
            data = result["data"]
            if data.get("revenue_currency") is not None:
                assert isinstance(data["revenue_currency"], str)


@pytest.mark.live
class TestLiveForecastStreamerInit:
    """Test ForecastStreamer initialization."""

    def test_default_init(self) -> None:
        """Test default initialization."""
        fs = ForecastStreamer()
        assert fs.export_result is False
        assert fs.export_type == "json"
        assert fs.cookie is None

    def test_custom_init(self) -> None:
        """Test custom initialization."""
        fs = ForecastStreamer(export_result=True, export_type="csv", cookie="test")
        assert fs.export_result is True
        assert fs.export_type == "csv"
        assert fs.cookie == "test"

    def test_cookie_from_env(self) -> None:
        """Test cookie from environment variable."""
        cookie = os.environ.get("TRADINGVIEW_COOKIE")
        if cookie:
            fs = ForecastStreamer()
            assert fs.cookie == cookie
