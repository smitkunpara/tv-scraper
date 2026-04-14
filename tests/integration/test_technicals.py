"""Integration tests for Technicals scraper.

Tests cross-module workflows and integration with other components
like DataValidator, Fundamentals, etc.
"""

from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.market_data.technicals import Technicals


@pytest.mark.integration
class TestTechnicalsWorkflows:
    """Test complete workflows combining multiple operations."""

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_symbol_analysis_workflow(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test symbol analysis workflow: validate -> fetch -> analyze."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "RSI": 55.5,
            "MACD.macd": 0.12,
            "MACD.signal": 0.10,
            "Stoch.K": 65.3,
            "Stoch.D": 60.1,
            "CCI20": 25.0,
            "ADX": 30.0,
        }
        mock_response.text = '{"RSI": 55.5, "MACD.macd": 0.12}'
        mock_request.return_value = mock_response

        t = Technicals()

        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI", "MACD.macd", "Stoch.K"],
        )

        assert result["status"] == STATUS_SUCCESS
        data = result["data"]

        if "RSI" in data:
            rsi = data["RSI"]
            assert isinstance(rsi, (int, float))
            assert 0 <= rsi <= 100

        if "MACD.macd" in data:
            macd = data["MACD.macd"]
            assert isinstance(macd, (int, float))

        if "Stoch.K" in data:
            stoch = data["Stoch.K"]
            assert isinstance(stoch, (int, float))
            assert 0 <= stoch <= 100

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_multi_timeframe_analysis(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test multi-timeframe analysis workflow."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"RSI": 55.5}
        mock_response.text = '{"RSI": 55.5}'
        mock_request.return_value = mock_response

        t = Technicals()
        timeframes = ["15m", "1h", "4h", "1d"]
        results = {}

        for tf in timeframes:
            result = t.get_technicals(
                exchange="NASDAQ",
                symbol="AAPL",
                timeframe=tf,
                technical_indicators=["RSI"],
            )
            assert result["status"] == STATUS_SUCCESS
            results[tf] = result["data"]

        assert len(results) == len(timeframes)
        for tf in timeframes:
            assert "RSI" in results[tf]


@pytest.mark.integration
class TestTechnicalsErrorPropagation:
    """Test error handling and propagation across the system."""

    def test_validation_error_structure(self):
        """Test validation error returns proper structure."""
        t = Technicals()
        result = t.get_technicals(
            exchange="INVALID",
            symbol="AAPL",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "metadata" in result
        assert result["metadata"]["exchange"] == "INVALID"
        assert result["metadata"]["symbol"] == "AAPL"

    def test_http_error_handling(self):
        """Test HTTP error is handled properly."""
        t = Technicals()
        result = t.get_technicals(
            exchange="INVALID_EXCHANGE_XYZ",
            symbol="AAPL",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_FAILED
        assert "error" in result


@pytest.mark.integration
class TestTechnicalsWithExport:
    """Test Technicals with export functionality."""

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    @patch("tv_scraper.core.base.save_json_file")
    def test_export_json_integration(
        self, mock_save, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test JSON export integration."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"RSI": 55.5, "MACD.macd": 0.12}
        mock_response.text = '{"RSI": 55.5, "MACD.macd": 0.12}'
        mock_request.return_value = mock_response

        t = Technicals(export="json")
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI", "MACD.macd"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert mock_save.called

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    @patch("tv_scraper.core.base.save_csv_file")
    def test_export_csv_integration(
        self, mock_save, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test CSV export integration."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"RSI": 55.5}
        mock_response.text = '{"RSI": 55.5}'
        mock_request.return_value = mock_response

        t = Technicals(export="csv")
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert mock_save.called


@pytest.mark.integration
class TestTechnicalsScenarios:
    """Test complete real-world scenarios."""

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_crypto_screening_workflow(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test crypto screening workflow."""
        mock_verify.return_value = ("BINANCE", "BTCUSDT")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "RSI": 68.5,
            "MACD.macd": 150.0,
            "ADX": 45.0,
            "Stoch.K": 78.2,
        }
        mock_response.text = '{"RSI": 68.5}'
        mock_request.return_value = mock_response

        t = Technicals()
        result = t.get_technicals(
            exchange="BINANCE",
            symbol="BTCUSDT",
            timeframe="4h",
            technical_indicators=["RSI", "MACD.macd", "ADX", "Stoch.K"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["exchange"] == "BINANCE"
        assert result["metadata"]["symbol"] == "BTCUSDT"
        assert result["metadata"]["timeframe"] == "4h"

        data = result["data"]
        assert isinstance(data, dict)

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_stock_screening_workflow(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test stock screening workflow."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "RSI": 55.5,
            "MACD.macd": 0.12,
            "EMA50": 175.0,
            "EMA200": 150.0,
        }
        mock_response.text = '{"RSI": 55.5}'
        mock_request.return_value = mock_response

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="1d",
            technical_indicators=["RSI", "MACD.macd", "EMA50", "EMA200"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["exchange"] == "NASDAQ"
        assert result["metadata"]["symbol"] == "AAPL"

        data = result["data"]
        if "EMA50" in data and "EMA200" in data:
            if data["EMA50"] > data["EMA200"]:
                trend = "bullish"
            else:
                trend = "bearish"
            assert trend == "bullish"

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_momentum_analysis_workflow(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test momentum analysis workflow."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "RSI": 65.0,
            "CCI20": 120.0,
            "ADX": 35.0,
            "Stoch.K": 75.0,
            "Stoch.D": 70.0,
        }
        mock_response.text = '{"RSI": 65.0}'
        mock_request.return_value = mock_response

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI", "CCI20", "ADX", "Stoch.K", "Stoch.D"],
        )

        assert result["status"] == STATUS_SUCCESS
        data = result["data"]

        indicators = ["RSI", "CCI20", "ADX", "Stoch.K", "Stoch.D"]
        available = [ind for ind in indicators if ind in data]

        momentum_signals = []
        if "RSI" in data and data["RSI"] > 60:
            momentum_signals.append("RSI_bullish")
        if "CCI20" in data and data["CCI20"] > 100:
            momentum_signals.append("CCI20_overbought")
        if "Stoch.K" in data and data["Stoch.K"] > 80:
            momentum_signals.append("Stoch_overbought")

        assert len(available) >= 3


@pytest.mark.integration
class TestTechnicalsConcurrentOperations:
    """Test concurrent operations with Technicals."""

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_sequential_symbol_fetching(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test sequential fetching of multiple symbols."""
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        symbols = [
            ("NASDAQ", "AAPL"),
            ("NASDAQ", "MSFT"),
            ("NYSE", "JPM"),
        ]

        def make_mock_response():
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"RSI": 50.0}
            mock_response.text = '{"RSI": 50.0}'
            return mock_response

        def verify_side_effect(exchange, symbol):
            return (exchange, symbol)

        mock_verify.side_effect = verify_side_effect
        mock_request.return_value = make_mock_response()

        t = Technicals()
        results = []

        for exchange, symbol in symbols:
            result = t.get_technicals(
                exchange=exchange,
                symbol=symbol,
                technical_indicators=["RSI"],
            )
            results.append(result)

        assert len(results) == len(symbols)
        for i, result in enumerate(results):
            assert result["status"] == STATUS_SUCCESS
            assert result["metadata"]["exchange"] == symbols[i][0]
            assert result["metadata"]["symbol"] == symbols[i][1]


@pytest.mark.integration
class TestTechnicalsPerformance:
    """Test performance characteristics."""

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_response_time_structure(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test response structure is consistent."""
        import time

        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"RSI": 55.5}
        mock_response.text = '{"RSI": 55.5}'
        mock_request.return_value = mock_response

        t = Technicals()
        start = time.time()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI"],
        )
        elapsed = time.time() - start

        assert result["status"] == STATUS_SUCCESS
        assert elapsed < 1.0

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
