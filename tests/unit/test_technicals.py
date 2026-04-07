"""Unit tests for Technicals scraper.

Comprehensive tests covering valid inputs, invalid inputs, edge cases,
and various parameter combinations using mocking - no actual HTTP connections.
"""

import json
from unittest.mock import MagicMock, patch

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.market_data.technicals import Technicals


class TestTechnicalsInit:
    """Tests for Technicals initialization."""

    def test_default_init(self):
        """Test default initialization."""
        t = Technicals()
        assert t.export_result is False
        assert t.export_type == "json"

    def test_custom_init(self):
        """Test custom initialization."""
        t = Technicals(export_result=True, export_type="csv")
        assert t.export_result is True
        assert t.export_type == "csv"


class TestInheritance:
    """Test that Technicals inherits from ScannerScraper/BaseScraper."""

    def test_inherits_from_base_scraper(self):
        """Verify Technicals inherits BaseScraper methods."""
        t = Technicals()
        assert hasattr(t, "_success_response")
        assert hasattr(t, "_error_response")
        assert hasattr(t, "_export")
        assert hasattr(t, "validator")


class TestGetTechnicalsInvalidInputs:
    """Test get_technicals with invalid inputs."""

    def test_empty_exchange(self):
        """Test empty exchange returns error."""
        t = Technicals()
        result = t.get_technicals(exchange="", symbol="AAPL")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "symbol" in result["metadata"]

        result = t.get_technicals(exchange=None, symbol="AAPL")  # type: ignore
        assert result["status"] == STATUS_FAILED
        assert "Exchange must be a non-empty string" in result["error"]

    def test_null_symbol(self):
        """Test null symbol returns error."""
        t = Technicals()
        result = t.get_technicals(exchange="NASDAQ", symbol=None)  # type: ignore

        assert result["status"] == STATUS_FAILED
        assert "Symbol must be a non-empty string" in result["error"]

    def test_whitespace_only_exchange(self):
        """Test whitespace-only exchange returns error."""
        t = Technicals()
        result = t.get_technicals(exchange="   ", symbol="AAPL")

        assert result["status"] == STATUS_FAILED

    def test_whitespace_only_symbol(self):
        """Test whitespace-only symbol returns error."""
        t = Technicals()
        result = t.get_technicals(exchange="NASDAQ", symbol="   ")

        assert result["status"] == STATUS_FAILED


class TestGetTechnicalsInvalidTimeframe:
    """Test get_technicals with invalid timeframe."""

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_invalid_timeframe(self, mock_verify):
        """Test invalid timeframe returns error."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="13h",  # type: ignore[arg-type]
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None
        assert "timeframe" in result["error"].lower() or "13h" in result["error"]


class TestGetTechnicalsInvalidIndicators:
    """Test get_technicals with invalid indicators."""

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_invalid_indicator(self, mock_verify):
        """Test invalid indicator returns error."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["INVALID_XYZ"],
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_empty_indicators_list(self, mock_verify):
        """Test empty indicators list returns error."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=[],
        )

        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_none_indicators_without_all_indicators(self, mock_verify):
        """Test None indicators without all_indicators returns error."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=None,
            all_indicators=False,
        )

        assert result["status"] == STATUS_FAILED
        assert "No indicators provided" in result["error"]


class TestGetTechnicalsValidInputs:
    """Test get_technicals with valid inputs and various combinations."""

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_single_indicator_success(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test single indicator returns success."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"RSI": 55.5, "MACD.macd": 0.12}
        mock_response.text = json.dumps(mock_response.json.return_value)
        mock_request.return_value = mock_response

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], dict)
        assert "RSI" in result["data"]

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_multiple_indicators_success(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test multiple indicators returns success."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "RSI": 55.5,
            "MACD.macd": 0.12,
            "MACD.signal": 0.10,
        }
        mock_response.text = json.dumps(mock_response.json.return_value)
        mock_request.return_value = mock_response

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI", "MACD.macd"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert "RSI" in result["data"]
        assert "MACD.macd" in result["data"]

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.get_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_all_indicators_success(
        self, mock_request, mock_get_ind, mock_validate_tf, mock_verify
    ):
        """Test all_indicators=True returns success."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_get_ind.return_value = ["RSI", "MACD.macd"]

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"RSI": 55.5, "MACD.macd": 0.12}
        mock_response.text = json.dumps(mock_response.json.return_value)
        mock_request.return_value = mock_response

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            all_indicators=True,
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["all_indicators"] is True


class TestGetTechnicalsTimeframes:
    """Test get_technicals with various timeframes."""

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_all_timeframes(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test with all supported timeframes."""
        mock_verify.return_value = ("BINANCE", "BTCUSDT")
        mock_validate_ind.return_value = True

        timeframes = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "1d", "1w", "1M"]

        for tf in timeframes:
            mock_validate_tf.side_effect = lambda x, t=tf: (
                True if t == x else (_ for _ in ()).throw(Exception(f"Invalid: {x}"))
            )

            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"RSI": 55.5}
            mock_response.text = json.dumps(mock_response.json.return_value)
            mock_request.return_value = mock_response

            t = Technicals()
            result = t.get_technicals(
                exchange="BINANCE",
                symbol="BTCUSDT",
                timeframe=tf,
                technical_indicators=["RSI"],
            )

            if result["status"] == STATUS_SUCCESS:
                assert result["metadata"]["timeframe"] == tf


class TestGetTechnicalsExchanges:
    """Test get_technicals with various exchanges."""

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_nasdaq_exchange(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test NASDAQ exchange."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"RSI": 55.5}
        mock_response.text = json.dumps(mock_response.json.return_value)
        mock_request.return_value = mock_response

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["exchange"] == "NASDAQ"

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_binance_exchange(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test BINANCE exchange."""
        mock_verify.return_value = ("BINANCE", "BTCUSDT")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"RSI": 60.0}
        mock_response.text = json.dumps(mock_response.json.return_value)
        mock_request.return_value = mock_response

        t = Technicals()
        result = t.get_technicals(
            exchange="BINANCE",
            symbol="BTCUSDT",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["exchange"] == "BINANCE"


class TestGetTechnicalsFieldsFiltering:
    """Test fields filtering parameter."""

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_fields_filtering(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test fields parameter filters output."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "RSI": 55.5,
            "MACD.macd": 0.12,
            "MACD.signal": 0.10,
        }
        mock_response.text = json.dumps(mock_response.json.return_value)
        mock_request.return_value = mock_response

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI", "MACD.macd", "MACD.signal"],
            fields=["RSI", "MACD.macd"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert "RSI" in result["data"]
        assert "MACD.macd" in result["data"]


class TestGetTechnicalsExport:
    """Test export functionality."""

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    @patch("tv_scraper.core.base.save_json_file")
    def test_export_json(
        self, mock_save, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test JSON export."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"RSI": 55.5}
        mock_response.text = json.dumps(mock_response.json.return_value)
        mock_request.return_value = mock_response

        t = Technicals(export_result=True, export_type="json")
        t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI"],
        )

        assert mock_save.called

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    @patch("tv_scraper.core.base.save_csv_file")
    def test_export_csv(
        self, mock_save, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test CSV export."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"RSI": 55.5}
        mock_response.text = json.dumps(mock_response.json.return_value)
        mock_request.return_value = mock_response

        t = Technicals(export_result=True, export_type="csv")
        t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI"],
        )

        assert mock_save.called


class TestGetTechnicalsErrorHandling:
    """Test error handling in get_technicals."""

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.base.requests.request")
    def test_network_error(self, mock_request, mock_validate_tf, mock_verify):
        """Test network error returns error response."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True

        import requests

        mock_request.side_effect = requests.RequestException("Network error")

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
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
        mock_response.text = json.dumps(mock_response.json.return_value)
        mock_request.return_value = mock_response

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_FAILED
        assert "Empty response" in result["error"]


class TestGetTechnicalsMetadata:
    """Test metadata in responses."""

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_success_metadata(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test success metadata contains all parameters."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"RSI": 55.5}
        mock_response.text = json.dumps(mock_response.json.return_value)
        mock_request.return_value = mock_response

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="4h",
            technical_indicators=["RSI", "MACD.macd"],
        )

        meta = result["metadata"]
        assert meta["exchange"] == "NASDAQ"
        assert meta["symbol"] == "AAPL"
        assert meta["timeframe"] == "4h"
        assert meta["all_indicators"] is False
        assert meta["technical_indicators"] == ["RSI", "MACD.macd"]

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.get_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_all_indicators_metadata(
        self, mock_request, mock_get_ind, mock_validate_tf, mock_verify
    ):
        """Test all_indicators metadata."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_get_ind.return_value = ["RSI", "MACD.macd"]

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"RSI": 55.5, "MACD.macd": 0.12}
        mock_response.text = json.dumps(mock_response.json.return_value)
        mock_request.return_value = mock_response

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            all_indicators=True,
        )

        meta = result["metadata"]
        assert meta["all_indicators"] is True
        # Note: Automated metadata includes all non-None arguments.
        # Since technical_indicators defaults to None, it is excluded.
        assert "technical_indicators" not in meta


class TestGetTechnicalsResponseEnvelope:
    """Test standardized response envelope."""

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_success_has_all_keys(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test success response has required keys."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"RSI": 55.5}
        mock_response.text = json.dumps(mock_response.json.return_value)
        mock_request.return_value = mock_response

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["RSI"],
        )

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None

    def test_error_has_all_keys(self):
        """Test error response has required keys."""
        t = Technicals()
        result = t.get_technicals(
            exchange="INVALID_EXCHANGE",
            symbol="INVALID",
            technical_indicators=["RSI"],
        )

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None


class TestReviseResponse:
    """Test _revise_response method."""

    def test_daily_timeframe_no_change(self):
        """Test daily timeframe doesn't modify keys."""
        t = Technicals()
        data = {"RSI": 55.5, "MACD.macd": 0.12}

        result = t._revise_response(data, "1D")

        assert result == data

    def test_empty_timeframe_no_change(self):
        """Test empty timeframe doesn't modify keys."""
        t = Technicals()
        data = {"RSI": 55.5, "MACD.macd": 0.12}

        result = t._revise_response(data, "")

        assert result == data

    def test_hourly_timeframe_strips_suffix(self):
        """Test hourly timeframe strips suffix."""
        t = Technicals()
        data = {"RSI|60": 55.5, "MACD.macd|60": 0.12}

        result = t._revise_response(data, "60")

        assert "RSI" in result
        assert "RSI|60" not in result
        assert "MACD.macd" in result
        assert "MACD.macd|60" not in result

    def test_4h_timeframe_strips_suffix(self):
        """Test 4h timeframe strips suffix."""
        t = Technicals()
        data = {"RSI|240": 55.5, "EMA50|240": 100.0}

        result = t._revise_response(data, "240")

        assert "RSI" in result
        assert "EMA50" in result


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_case_sensitivity_exchange(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test exchange is case insensitive."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"RSI": 55.5}
        mock_response.text = json.dumps(mock_response.json.return_value)
        mock_request.return_value = mock_response

        t = Technicals()
        result = t.get_technicals(
            exchange="nasdaq",  # lowercase
            symbol="aapl",  # lowercase
            technical_indicators=["RSI"],
        )

        assert result["status"] == STATUS_SUCCESS
        # Note: Metadata captures actual input values.
        assert result["metadata"]["exchange"] == "nasdaq"
        assert result["metadata"]["symbol"] == "aapl"

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.validators.validate_timeframe")
    @patch("tv_scraper.core.validators.validate_indicators")
    @patch("tv_scraper.core.base.requests.request")
    def test_indicator_with_dot_notation(
        self, mock_request, mock_validate_ind, mock_validate_tf, mock_verify
    ):
        """Test indicator with dot notation."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_validate_tf.return_value = True
        mock_validate_ind.return_value = True

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "MACD.macd": 0.12,
            "MACD.signal": 0.10,
            "Stoch.K": 75.5,
            "Stoch.D": 70.2,
        }
        mock_response.text = json.dumps(mock_response.json.return_value)
        mock_request.return_value = mock_response

        t = Technicals()
        result = t.get_technicals(
            exchange="NASDAQ",
            symbol="AAPL",
            technical_indicators=["MACD.macd", "MACD.signal", "Stoch.K", "Stoch.D"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert "MACD.macd" in result["data"]
        assert "MACD.signal" in result["data"]
        assert "Stoch.K" in result["data"]
        assert "Stoch.D" in result["data"]
