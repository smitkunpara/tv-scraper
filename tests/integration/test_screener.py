"""Integration tests for Screener.

Tests cross-module workflows and interactions with other components
like DataValidator, ScannerScraper, and the streaming modules.
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.core.validators import DataValidator
from tv_scraper.scrapers.screening.screener import Screener
from tv_scraper.streaming.candle_streamer import CandleStreamer
from tv_scraper.streaming.forecast_streamer import ForecastStreamer

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "screener")


def load_fixture(filename: str) -> dict:
    """Load fixture data from file."""
    filepath = os.path.join(FIXTURES_DIR, filename)
    if not os.path.exists(filepath):
        pytest.skip(f"Fixture {filename} not found")
    with open(filepath) as f:
        return json.load(f)


class TestScreenerWithValidator:
    """Test Screener integration with DataValidator."""

    def test_validator_integration(self) -> None:
        """Test Screener uses DataValidator."""
        scraper = Screener()
        assert hasattr(scraper, "validator")
        assert isinstance(scraper.validator, DataValidator)

    @patch.object(Screener, "_request")
    def test_validator_not_called_in_screener(self, mock_request: MagicMock) -> None:
        """Test that Screener doesn't call validator for exchange/symbol validation.

        Screener validates market, not exchange/symbol like other scrapers.
        """
        mock_request.return_value = ({"data": [], "totalCount": 0}, None)

        scraper = Screener()
        result = scraper.get_screener(market="america", limit=5)

        assert result["status"] == STATUS_SUCCESS


class TestScreenerScannerIntegration:
    """Test Screener integration with ScannerScraper base."""

    def test_inherits_scanner_scraper(self) -> None:
        """Test Screener inherits from ScannerScraper."""
        scraper = Screener()
        assert hasattr(scraper, "_map_scanner_rows")
        assert hasattr(scraper, "_request")

    @patch.object(Screener, "_request")
    def test_map_scanner_rows_integration(self, mock_request: MagicMock) -> None:
        """Test _map_scanner_rows is called with correct parameters."""
        mock_response = {
            "data": [
                {"s": "NASDAQ:AAPL", "d": ["Apple Inc.", 150.0, 2.5, 5000000]},
                {"s": "NYSE:MSFT", "d": ["Microsoft Corp.", 300.0, 1.5, 3000000]},
            ],
            "totalCount": 2,
        }
        mock_request.return_value = (mock_response, None)

        scraper = Screener()
        fields = ["name", "close", "change", "volume"]
        result = scraper.get_screener(
            market="america",
            fields=fields,
            limit=5,
        )

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 2
        assert result["data"][0]["symbol"] == "NASDAQ:AAPL"
        assert result["data"][0]["name"] == "Apple Inc."
        assert result["data"][0]["close"] == 150.0


class TestScreenerCandleStreamerWorkflow:
    """Test Screener to CandleStreamer workflow."""

    def test_screener_and_streamer_independent(self) -> None:
        """Test Screener and CandleStreamer can coexist."""
        screener = Screener()
        streamer = CandleStreamer()

        assert hasattr(screener, "get_screener")
        assert hasattr(streamer, "get_candles")

    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch.object(Screener, "_request")
    def test_screener_then_candles_workflow(
        self, mock_screener: MagicMock, mock_ws: MagicMock
    ) -> None:
        """Test workflow: Screener finds symbols, then get candles for top results."""
        screener_response = {
            "data": [
                {"s": "NASDAQ:AAPL", "d": ["Apple Inc.", 150.0, 2.5, 5000000]},
                {"s": "NYSE:MSFT", "d": ["Microsoft Corp.", 300.0, 1.5, 3000000]},
            ],
            "totalCount": 2,
        }
        mock_screener.return_value = (screener_response, None)

        mock_ws_instance = MagicMock()
        mock_ws.return_value = mock_ws_instance
        ohlcv_entry = {"i": 0, "v": [1700000000, 100.0, 105.0, 99.0, 102.0, 5000]}
        ts_pkt = {
            "m": "timescale_update",
            "p": ["cs_test", {"sds_1": {"s": [ohlcv_entry]}}],
        }
        ts_raw = json.dumps(ts_pkt)
        framed = f"~m~{len(ts_raw)}~m~{ts_raw}"
        mock_ws_instance.recv.side_effect = [framed, ConnectionError("done")]

        screener = Screener()
        screener_result = screener.get_screener(market="america", limit=5)
        assert screener_result["status"] == STATUS_SUCCESS

        top_symbol = screener_result["data"][0]["symbol"]
        exchange, symbol = top_symbol.split(":")
        streamer = CandleStreamer()
        candle_result = streamer.get_candles(
            exchange=exchange, symbol=symbol, numb_candles=5
        )
        assert "status" in candle_result


class TestScreenerForecastStreamerWorkflow:
    """Test Screener to ForecastStreamer workflow."""

    def test_screener_and_forecast_independent(self) -> None:
        """Test Screener and ForecastStreamer can coexist."""
        screener = Screener()
        forecast = ForecastStreamer()

        assert hasattr(screener, "get_screener")
        assert hasattr(forecast, "get_forecast")

    @patch.object(Screener, "_request")
    @patch("tv_scraper.streaming.stream_handler.create_connection")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_screener_then_forecast_workflow(
        self,
        mock_validate: MagicMock,
        mock_ws: MagicMock,
        mock_screener: MagicMock,
    ) -> None:
        """Test workflow: Screener finds stock symbols, then get forecasts."""
        screener_response = {
            "data": [
                {"s": "NASDAQ:AAPL", "d": ["Apple Inc.", 150.0, 2.5, 5000000]},
                {"s": "NYSE:JPM", "d": ["JPMorgan Chase", 180.0, 1.2, 3000000]},
            ],
            "totalCount": 2,
        }
        mock_screener.return_value = (screener_response, None)
        mock_validate.side_effect = lambda e, s: (e.upper(), s.upper())

        mock_ws_instance = MagicMock()
        mock_ws.return_value = mock_ws_instance
        mock_ws_instance.recv.side_effect = [ConnectionError("done")]

        screener = Screener()
        screener_result = screener.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "greater", "right": 100}],
            limit=5,
        )
        assert screener_result["status"] == STATUS_SUCCESS


class TestScreenerWithExport:
    """Test Screener export integration."""

    @patch.object(Screener, "_request")
    @patch.object(Screener, "_export")
    def test_export_integration(
        self, mock_export: MagicMock, mock_request: MagicMock
    ) -> None:
        """Test Screener export is called correctly."""
        mock_response = {
            "data": [
                {"s": "NASDAQ:AAPL", "d": ["Apple Inc.", 150.0, 2.5, 5000000]},
            ],
            "totalCount": 1,
        }
        mock_request.return_value = (mock_response, None)

        scraper = Screener(export_result=True)
        result = scraper.get_screener(market="america", limit=5)

        assert result["status"] == STATUS_SUCCESS
        mock_export.assert_called_once()
        call_kwargs = mock_export.call_args.kwargs
        assert call_kwargs["symbol"] == "america_screener"
        assert call_kwargs["data_category"] == "screener"


class TestScreenerMultipleMarkets:
    """Test Screener across multiple market screens."""

    @patch.object(Screener, "_request")
    def test_america_crypto_comparison(self, mock_request: MagicMock) -> None:
        """Test comparing america and crypto markets."""

        def side_effect(*args, **kwargs):
            market = kwargs.get("json_payload", {}).get("markets", [""])[0]
            if market == "america":
                return (
                    {
                        "data": [
                            {
                                "s": "NASDAQ:AAPL",
                                "d": ["Apple Inc.", 150.0, 2.5, 5000000],
                            },
                        ],
                        "totalCount": 1,
                    },
                    None,
                )
            else:
                return (
                    {
                        "data": [
                            {
                                "s": "BINANCE:BTCUSDT",
                                "d": ["Bitcoin", 50000.0, 3.5, 1000000],
                            },
                        ],
                        "totalCount": 1,
                    },
                    None,
                )

        mock_request.side_effect = side_effect

        scraper = Screener()
        america_result = scraper.get_screener(market="america", limit=5)
        crypto_result = scraper.get_screener(market="crypto", limit=5)

        assert america_result["status"] == STATUS_SUCCESS
        assert crypto_result["status"] == STATUS_SUCCESS
        assert america_result["data"][0]["symbol"].startswith("NASDAQ")
        assert crypto_result["data"][0]["symbol"].startswith("BINANCE")


class TestScreenerFilterCombinations:
    """Test Screener with complex filter combinations."""

    @patch.object(Screener, "_request")
    def test_filters_and_symbols_combined(self, mock_request: MagicMock) -> None:
        """Test combining filters with symbol restrictions."""
        mock_response = {
            "data": [
                {"s": "NASDAQ:AAPL", "d": ["Apple Inc.", 150.0, 2.5, 5000000]},
            ],
            "totalCount": 1,
        }
        mock_request.return_value = (mock_response, None)

        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "greater", "right": 100}],
            symbols={"tickers": ["NASDAQ:AAPL", "NYSE:JPM"]},
            limit=10,
        )

        assert result["status"] == STATUS_SUCCESS
        call_args = mock_request.call_args
        payload = call_args.kwargs.get("json_payload", {})
        assert "filter" in payload
        assert "symbols" in payload

    @patch.object(Screener, "_request")
    def test_filters_and_filter2_combined(self, mock_request: MagicMock) -> None:
        """Test combining base filters with filter2 boolean logic."""
        mock_response = {
            "data": [
                {"s": "NASDAQ:AAPL", "d": ["Apple Inc.", 150.0, 2.5, 5000000]},
            ],
            "totalCount": 1,
        }
        mock_request.return_value = (mock_response, None)

        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "greater", "right": 50}],
            filter2={
                "operator": "and",
                "operands": [
                    {"left": "volume", "operation": "greater", "right": 1000000},
                    {"left": "change", "operation": "greater", "right": 0},
                ],
            },
            limit=10,
        )

        assert result["status"] == STATUS_SUCCESS
        call_args = mock_request.call_args
        payload = call_args.kwargs.get("json_payload", {})
        assert "filter" in payload
        assert "filter2" in payload


class TestScreenerResponseTransformation:
    """Test Screener response data transformation."""

    @patch.object(Screener, "_request")
    def test_raw_to_formatted_data(self, mock_request: MagicMock) -> None:
        """Test raw API data is transformed correctly."""
        mock_response = {
            "data": [
                {"s": "NASDAQ:AAPL", "d": ["Apple Inc.", 150.0, 2.5]},
                {"s": "NYSE:MSFT", "d": ["Microsoft", 300.0, 1.5]},
            ],
            "totalCount": 2,
        }
        mock_request.return_value = (mock_response, None)

        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            fields=["name", "close", "change"],
            limit=5,
        )

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 2
        assert result["data"][0]["symbol"] == "NASDAQ:AAPL"
        assert result["data"][0]["name"] == "Apple Inc."
        assert result["data"][0]["close"] == 150.0
        assert result["data"][0]["change"] == 2.5

    @patch.object(Screener, "_request")
    def test_empty_data_handling(self, mock_request: MagicMock) -> None:
        """Test empty data is handled correctly."""
        mock_response = {
            "data": [],
            "totalCount": 0,
        }
        mock_request.return_value = (mock_response, None)

        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "greater", "right": 999999999}],
            limit=5,
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] == []
        assert result["metadata"]["total"] == 0


class TestScreenerErrorPropagation:
    """Test Screener error propagation to response envelope."""

    @patch.object(Screener, "_request")
    def test_network_error_preserved(self, mock_request: MagicMock) -> None:
        """Test network errors are preserved in response envelope."""
        mock_request.return_value = (None, "Connection timeout")

        scraper = Screener()
        result = scraper.get_screener(market="america", limit=5)

        assert result["status"] == STATUS_FAILED
        assert result["error"] == "Connection timeout"
        assert result["data"] is None

    @patch.object(Screener, "_request")
    def test_validation_error_preserved(self, mock_request: MagicMock) -> None:
        """Test validation errors are preserved in response envelope."""
        mock_request.return_value = (None, "Invalid market")

        scraper = Screener()
        result = scraper.get_screener(market="invalid", limit=5)

        assert result["status"] == STATUS_FAILED
        assert "Invalid market" in result["error"]


class TestScreenerMetadataCompleteness:
    """Test Screener metadata completeness."""

    @patch.object(Screener, "_request")
    def test_full_metadata(self, mock_request: MagicMock) -> None:
        """Test metadata contains all relevant information."""
        mock_response = {
            "data": [
                {"s": "NASDAQ:AAPL", "d": ["Apple Inc.", 150.0, 2.5, 5000000]},
            ],
            "totalCount": 50,
        }
        mock_request.return_value = (mock_response, None)

        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "greater", "right": 100}],
            fields=["name", "close"],
            sort_by="close",
            sort_order="desc",
            limit=10,
            symbols={"tickers": ["NASDAQ:AAPL"]},
            filter2={"operator": "and", "operands": []},
        )

        meta = result["metadata"]
        assert meta["market"] == "america"
        assert meta["limit"] == 10
        assert meta["sort_order"] == "desc"
        assert meta["sort_by"] == "close"
        assert meta["filters"] == [
            {"left": "close", "operation": "greater", "right": 100}
        ]
        assert meta["symbols"] == {"tickers": ["NASDAQ:AAPL"]}
        assert meta["filter2"] == {"operator": "and", "operands": []}
        assert meta["total"] == 1
        assert meta["total_available"] == 50


class TestScreenerWithTimeout:
    """Test Screener timeout handling."""

    def test_timeout_parameter(self) -> None:
        """Test timeout parameter is accepted."""
        scraper = Screener(timeout=30)
        assert scraper.timeout == 30

    @patch.object(Screener, "_request")
    def test_timeout_in_request(self, mock_request: MagicMock) -> None:
        """Test timeout is passed to request."""
        mock_request.return_value = ({"data": [], "totalCount": 0}, None)

        scraper = Screener(timeout=5)
        scraper.get_screener(market="america", limit=5)

        call_kwargs = mock_request.call_args.kwargs
        assert "timeout" not in call_kwargs
        assert scraper.timeout == 5


class TestScreenerConsistency:
    """Test Screener consistency with other scrapers."""

    def test_response_envelope_format(self) -> None:
        """Test Screener follows standard response envelope format."""
        scraper = Screener()
        result = scraper.get_screener(market="invalid", limit=5)

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_FAILED

    @patch.object(Screener, "_request")
    def test_success_response_format(self, mock_request: MagicMock) -> None:
        """Test success response follows standard format."""
        mock_request.return_value = ({"data": [], "totalCount": 0}, None)

        scraper = Screener()
        result = scraper.get_screener(market="america", limit=5)

        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None
        assert isinstance(result["data"], list)
        assert isinstance(result["metadata"], dict)
