"""Mock tests for Technicals scraper.

Tests using saved JSON fixtures to simulate API responses.
These tests do not make actual HTTP requests.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.market_data.technicals import Technicals

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "technicals"


def load_fixture(filename: str) -> dict[str, Any]:
    """Load a JSON fixture file."""
    fixture_path = FIXTURES_DIR / filename
    if not fixture_path.exists():
        pytest.skip(f"Fixture not found: {fixture_path}")
    with open(fixture_path) as f:
        return json.load(f)


def _mock_response(fixture_name: str) -> MagicMock:
    """Create a mock response from a fixture."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = load_fixture(fixture_name)
    mock_response.text = json.dumps(mock_response.json.return_value)
    return mock_response


class TestMockTechnicalsBasic:
    """Test basic mock scenarios."""

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    @patch("tv_scraper.core.validators.DataValidator.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_nasdaq_aapl_rsi(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test NASDAQ:AAPL with RSI indicator."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True
        mock_request.return_value = _mock_response("nasdaq_aapl_rsi.json")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["exchange"] == "NASDAQ"
        assert result["metadata"]["symbol"] == "AAPL"
        assert "RSI" in result["data"]

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    @patch("tv_scraper.core.validators.DataValidator.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_binance_btcusdt_rsi(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test BINANCE:BTCUSDT with RSI indicator."""
        mock_verify.return_value = ("BINANCE", "BTCUSDT")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True
        mock_request.return_value = _mock_response("binance_btcusdt_rsi.json")

        t = Technicals()
        result = t.get_technicals(
            exchange="BINANCE",
            symbol="BTCUSDT",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["exchange"] == "BINANCE"
        assert result["metadata"]["symbol"] == "BTCUSDT"
        assert "RSI" in result["data"]


class TestMockTechnicalsMultipleIndicators:
    """Test mock scenarios with multiple indicators."""

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    @patch("tv_scraper.core.validators.DataValidator.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_nasdaq_aapl_rsi_macd(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test NASDAQ:AAPL with RSI and MACD indicators."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True
        mock_request.return_value = _mock_response("nasdaq_aapl_rsi_macd.json")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI", "MACD.macd"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert "RSI" in result["data"]
        assert "MACD.macd" in result["data"]

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    @patch("tv_scraper.core.validators.DataValidator.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_binance_btcusdt_rsi_macd(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test BINANCE:BTCUSDT with RSI and MACD indicators."""
        mock_verify.return_value = ("BINANCE", "BTCUSDT")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True
        mock_request.return_value = _mock_response("binance_btcusdt_rsi_macd.json")

        t = Technicals()
        result = t.get_technicals(
            exchange="BINANCE",
            symbol="BTCUSDT",
            technical_indicators=["RSI", "MACD.macd"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert "RSI" in result["data"]
        assert "MACD.macd" in result["data"]


class TestMockTechnicalsTimeframes:
    """Test mock scenarios with various timeframes."""

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    @patch("tv_scraper.core.validators.DataValidator.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_timeframe_1m(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test timeframe 1m."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True
        mock_request.return_value = _mock_response("nasdaq_aapl_rsi_1m.json")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="1m",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["timeframe"] == "1m"
        assert "RSI" in result["data"]

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    @patch("tv_scraper.core.validators.DataValidator.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_timeframe_5m(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test timeframe 5m."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True
        mock_request.return_value = _mock_response("nasdaq_aapl_rsi_5m.json")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="5m",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["timeframe"] == "5m"

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    @patch("tv_scraper.core.validators.DataValidator.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_timeframe_15m(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test timeframe 15m."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True
        mock_request.return_value = _mock_response("nasdaq_aapl_rsi_15m.json")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="15m",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["timeframe"] == "15m"

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    @patch("tv_scraper.core.validators.DataValidator.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_timeframe_30m(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test timeframe 30m."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True
        mock_request.return_value = _mock_response("nasdaq_aapl_rsi_30m.json")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="30m",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["timeframe"] == "30m"

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    @patch("tv_scraper.core.validators.DataValidator.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_timeframe_1h(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test timeframe 1h."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True
        mock_request.return_value = _mock_response("nasdaq_aapl_rsi_1h.json")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="1h",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["timeframe"] == "1h"

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    @patch("tv_scraper.core.validators.DataValidator.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_timeframe_4h(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test timeframe 4h."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True
        mock_request.return_value = _mock_response("nasdaq_aapl_rsi_4h.json")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="4h",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["timeframe"] == "4h"

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    @patch("tv_scraper.core.validators.DataValidator.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_timeframe_1d(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test timeframe 1d."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True
        mock_request.return_value = _mock_response("nasdaq_aapl_rsi_1d.json")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="1d",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["timeframe"] == "1d"

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    @patch("tv_scraper.core.validators.DataValidator.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_timeframe_1w(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test timeframe 1w."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True
        mock_request.return_value = _mock_response("nasdaq_aapl_rsi_1w.json")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="1w",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["timeframe"] == "1w"

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    @patch("tv_scraper.core.validators.DataValidator.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_timeframe_1m_monthly(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test timeframe 1M (monthly)."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True
        mock_request.return_value = _mock_response("nasdaq_aapl_rsi_1m_monthly.json")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="1M",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["timeframe"] == "1M"


class TestMockTechnicalsAllIndicators:
    """Test mock scenarios with all_indicators=True."""

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    @patch("tv_scraper.core.validators.DataValidator.get_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_nasdaq_aapl_all_indicators(
        self, mock_request, mock_get_ind, mock_validate_tf, mock_verify
    ):
        """Test NASDAQ:AAPL with all indicators."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_get_ind.return_value = ["RSI", "MACD.macd", "MACD.signal"]
        mock_request.return_value = _mock_response("nasdaq_aapl_all_indicators.json")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            all_indicators=True,
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["all_indicators"] is True
        assert len(result["data"]) > 0


class TestMockTechnicalsErrorHandling:
    """Test mock scenarios for error handling."""

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    @patch("tv_scraper.core.validators.DataValidator.validate_indicators")
    def test_invalid_indicator(self, mock_validate_ind, mock_validate_tf, mock_verify):
        """Test invalid indicator returns error."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True

        from tv_scraper.core.exceptions import ValidationError

        mock_validate_ind.side_effect = ValidationError(
            "Invalid indicator: 'INVALID_XYZ'. Did you mean: RSI?"
        )

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["INVALID_XYZ"],
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    def test_invalid_timeframe(self, mock_validate_tf, mock_verify):
        """Test invalid timeframe returns error."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        from tv_scraper.core.exceptions import ValidationError

        mock_validate_tf.side_effect = ValidationError(
            "Invalid timeframe: '13h'. Valid timeframes: 1m, 5m, 15m, ..."
        )

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="13h",  # type: ignore[arg-type]
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "timeframe" in result["error"].lower()

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    @patch("tv_scraper.core.validators.DataValidator.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_empty_response(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test empty response returns error."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {}
        mock_response.text = json.dumps({})
        mock_request.return_value = mock_response

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_FAILED
        assert "Empty response" in result["error"]

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    @patch("tv_scraper.core.validators.DataValidator.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_network_error(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test network error returns error response."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        import requests

        mock_request.side_effect = requests.RequestException("Connection refused")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None


class TestMockTechnicalsFieldsFiltering:
    """Test fields filtering with mock fixtures."""

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    @patch("tv_scraper.core.validators.DataValidator.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_fields_filtering(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test fields parameter filters output correctly."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True
        mock_request.return_value = _mock_response("nasdaq_aapl_rsi_macd.json")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI", "MACD.macd"],
            fields=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert "RSI" in result["data"]


class TestMockTechnicalsResponseEnvelope:
    """Test response envelope structure with mock fixtures."""

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.DataValidator.validate_timeframe")
    @patch("tv_scraper.core.validators.DataValidator.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_success_response_structure(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test success response has correct structure."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True
        mock_request.return_value = _mock_response("nasdaq_aapl_rsi.json")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["data"] is not None
        assert result["error"] is None
        assert "exchange" in result["metadata"]
        assert "symbol" in result["metadata"]
        assert "timeframe" in result["metadata"]
        assert "all_indicators" in result["metadata"]
        assert "technical_indicators" in result["metadata"]

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    def test_error_response_structure(self, mock_verify):
        """Test error response has correct structure."""
        from tv_scraper.core.exceptions import ValidationError

        mock_verify.side_effect = ValidationError("Invalid exchange: 'INVALID'")

        t = Technicals()
        result = t.get_technicals(
            exchange="INVALID",
            symbol="AAPL",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_FAILED
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["data"] is None
        assert result["error"] is not None
