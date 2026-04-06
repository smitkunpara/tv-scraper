"""Unit tests for Fundamentals scraper.

Isolated function tests using mocks - no network calls.
Tests initialization, inheritance, field groups, and error handling.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.market_data.fundamentals import Fundamentals


class TestFundamentalsInit:
    """Tests for Fundamentals initialization."""

    def test_default_init(self) -> None:
        """Test default initialization."""
        fund = Fundamentals()
        assert fund.export_result is False
        assert fund.export_type == "json"
        assert fund.cookie is None
        assert hasattr(fund, "validator")

    def test_custom_init(self) -> None:
        """Test custom initialization."""
        fund = Fundamentals(export_result=True, export_type="csv", timeout=30)
        assert fund.export_result is True
        assert fund.export_type == "csv"
        assert fund.timeout == 30

    def test_cookie_from_env(self, monkeypatch) -> None:
        """Test cookie from environment variable."""
        monkeypatch.setenv("TRADINGVIEW_COOKIE", "env_cookie")
        fund = Fundamentals()
        assert fund.cookie == "env_cookie"

    def test_cookie_param_overrides_env(self, monkeypatch) -> None:
        """Test cookie parameter overrides environment."""
        monkeypatch.setenv("TRADINGVIEW_COOKIE", "env_cookie")
        fund = Fundamentals(cookie="param_cookie")
        assert fund.cookie == "param_cookie"

    def test_invalid_export_type(self) -> None:
        """Test invalid export type raises error."""
        with pytest.raises(ValueError) as exc_info:
            Fundamentals(export_type="invalid")
        assert "Invalid export_type" in str(exc_info.value)

    def test_invalid_timeout_too_low(self) -> None:
        """Test timeout too low raises error."""
        with pytest.raises(ValueError) as exc_info:
            Fundamentals(timeout=0)
        assert "Timeout must be an integer" in str(exc_info.value)

    def test_invalid_timeout_too_high(self) -> None:
        """Test timeout too high raises error."""
        with pytest.raises(ValueError) as exc_info:
            Fundamentals(timeout=500)
        assert "Timeout must be an integer" in str(exc_info.value)


class TestInheritance:
    """Test that Fundamentals inherits from ScannerScraper."""

    def test_inherits_from_scanner_scraper(self) -> None:
        """Verify Fundamentals inherits ScannerScraper methods."""
        fund = Fundamentals()
        assert hasattr(fund, "_success_response")
        assert hasattr(fund, "_error_response")
        assert hasattr(fund, "_export")
        assert hasattr(fund, "_request")
        assert hasattr(fund, "_fetch_symbol_fields")

    def test_has_validator(self) -> None:
        """Verify validator is available."""
        fund = Fundamentals()
        assert hasattr(fund, "validator")
        assert fund.validator is not None


class TestFundamentalsFieldGroups:
    """Test field group constants."""

    def test_income_statement_fields_count(self) -> None:
        """Verify income statement has expected number of fields."""
        assert len(Fundamentals.INCOME_STATEMENT_FIELDS) == 13

    def test_balance_sheet_fields_count(self) -> None:
        """Verify balance sheet has expected number of fields."""
        assert len(Fundamentals.BALANCE_SHEET_FIELDS) == 9

    def test_cash_flow_fields_count(self) -> None:
        """Verify cash flow has expected number of fields."""
        assert len(Fundamentals.CASH_FLOW_FIELDS) == 7

    def test_margin_fields_count(self) -> None:
        """Verify margin has expected number of fields."""
        assert len(Fundamentals.MARGIN_FIELDS) == 8

    def test_profitability_fields_count(self) -> None:
        """Verify profitability has expected number of fields."""
        assert len(Fundamentals.PROFITABILITY_FIELDS) == 5

    def test_liquidity_fields_count(self) -> None:
        """Verify liquidity has expected number of fields."""
        assert len(Fundamentals.LIQUIDITY_FIELDS) == 4

    def test_leverage_fields_count(self) -> None:
        """Verify leverage has expected number of fields."""
        assert len(Fundamentals.LEVERAGE_FIELDS) == 3

    def test_valuation_fields_count(self) -> None:
        """Verify valuation has expected number of fields."""
        assert len(Fundamentals.VALUATION_FIELDS) == 8

    def test_dividend_fields_count(self) -> None:
        """Verify dividend has expected number of fields."""
        assert len(Fundamentals.DIVIDEND_FIELDS) == 3

    def test_all_fields_count(self) -> None:
        """Verify ALL_FIELDS contains all field groups."""
        total = (
            len(Fundamentals.INCOME_STATEMENT_FIELDS)
            + len(Fundamentals.BALANCE_SHEET_FIELDS)
            + len(Fundamentals.CASH_FLOW_FIELDS)
            + len(Fundamentals.MARGIN_FIELDS)
            + len(Fundamentals.PROFITABILITY_FIELDS)
            + len(Fundamentals.LIQUIDITY_FIELDS)
            + len(Fundamentals.LEVERAGE_FIELDS)
            + len(Fundamentals.VALUATION_FIELDS)
            + len(Fundamentals.DIVIDEND_FIELDS)
        )
        assert len(Fundamentals.ALL_FIELDS) == total

    def test_all_fields_unique(self) -> None:
        """Verify ALL_FIELDS contains no duplicates."""
        assert len(Fundamentals.ALL_FIELDS) == len(set(Fundamentals.ALL_FIELDS))

    def test_default_comparison_fields_subset(self) -> None:
        """Verify DEFAULT_COMPARISON_FIELDS are all in ALL_FIELDS."""
        for field in Fundamentals.DEFAULT_COMPARISON_FIELDS:
            assert field in Fundamentals.ALL_FIELDS


class TestGetFundamentalsInvalidInputs:
    """Test get_fundamentals with invalid inputs."""

    def test_fields_not_list_string(self) -> None:
        """Test fields as string returns error."""
        fund = Fundamentals()
        result = fund.get_fundamentals(
            exchange="NASDAQ", symbol="AAPL", fields="total_revenue"
        )

        assert result["status"] == STATUS_FAILED
        assert "Fields must be a list" in result["error"]

    def test_fields_not_list_dict(self) -> None:
        """Test fields as dict returns error."""
        fund = Fundamentals()
        result = fund.get_fundamentals(
            exchange="NASDAQ", symbol="AAPL", fields={"field": "value"}
        )

        assert result["status"] == STATUS_FAILED
        assert "Fields must be a list" in result["error"]

    def test_fields_not_list_int(self) -> None:
        """Test fields as int returns error."""
        fund = Fundamentals()
        result = fund.get_fundamentals(exchange="NASDAQ", symbol="AAPL", fields=123)

        assert result["status"] == STATUS_FAILED
        assert "Fields must be a list" in result["error"]

    def test_invalid_field_names(self) -> None:
        """Test invalid field names return error."""
        fund = Fundamentals()
        result = fund.get_fundamentals(
            exchange="NASDAQ",
            symbol="AAPL",
            fields=["invalid_field", "another_invalid"],
        )

        assert result["status"] == STATUS_FAILED
        assert "Invalid field" in result["error"]

    def test_empty_fields_list(self) -> None:
        """Test empty fields list is handled gracefully by validator."""
        fund = Fundamentals()
        result = fund.get_fundamentals(exchange="NASDAQ", symbol="AAPL", fields=[])
        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result

    def test_mixed_valid_invalid_fields(self) -> None:
        """Test mixed valid/invalid fields returns error."""
        fund = Fundamentals()
        result = fund.get_fundamentals(
            exchange="NASDAQ",
            symbol="AAPL",
            fields=["total_revenue", "invalid_field"],
        )

        assert result["status"] == STATUS_FAILED
        assert "Invalid field" in result["error"]


class TestGetFundamentalsNetworkErrors:
    """Test get_fundamentals with network errors."""

    @patch("tv_scraper.core.base.requests.request")
    def test_network_error(self, mock_request: MagicMock) -> None:
        """Test network error returns error."""
        mock_request.side_effect = requests.RequestException("Network error")

        fund = Fundamentals()
        result = fund.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_FAILED
        assert "Network error" in result["error"]

    @patch("tv_scraper.core.base.requests.request")
    def test_http_error(self, mock_request: MagicMock) -> None:
        """Test HTTP error returns error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "500 Server Error"
        )
        mock_request.return_value = mock_response

        fund = Fundamentals()
        result = fund.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_FAILED
        assert "Network error" in result["error"]

    @patch("tv_scraper.core.base.requests.request")
    def test_timeout_error(self, mock_request: MagicMock) -> None:
        """Test timeout error returns error."""
        mock_request.side_effect = requests.Timeout("Request timed out")

        fund = Fundamentals()
        result = fund.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_FAILED
        assert "Network error" in result["error"]

    @patch("tv_scraper.core.base.requests.request")
    def test_empty_response(self, mock_request: MagicMock) -> None:
        """Test empty response returns error."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.text = ""
        mock_request.return_value = mock_response

        fund = Fundamentals()
        result = fund.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None

    @patch("tv_scraper.core.base.requests.request")
    def test_invalid_json_response(self, mock_request: MagicMock) -> None:
        """Test invalid JSON returns error."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.text = "not valid json {"
        mock_request.return_value = mock_response

        fund = Fundamentals()
        result = fund.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_FAILED


class TestGetFundamentalsAPIErrors:
    """Test get_fundamentals with API error responses."""

    @patch("tv_scraper.core.base.requests.request")
    def test_api_error_in_response(self, mock_request: MagicMock) -> None:
        """Test API error in response body."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.text = json.dumps(
            {"error": "API Error", "errmsg": "Invalid symbol"}
        )
        mock_request.return_value = mock_response

        fund = Fundamentals()
        result = fund.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_FAILED
        assert "API error" in result["error"]

    @patch("tv_scraper.core.base.requests.request")
    def test_api_s_error_status(self, mock_request: MagicMock) -> None:
        """Test 's': 'error' in response body."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.text = json.dumps({"s": "error", "errmsg": "Server error"})
        mock_request.return_value = mock_response

        fund = Fundamentals()
        result = fund.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_FAILED
        assert "API error" in result["error"]

    @patch("tv_scraper.core.base.requests.request")
    def test_no_data_returned(self, mock_request: MagicMock) -> None:
        """Test empty data returns error."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.text = json.dumps({})
        mock_request.return_value = mock_response

        fund = Fundamentals()
        result = fund.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None


class TestGetFundamentalsValidation:
    """Test get_fundamentals with validation errors."""

    @patch("tv_scraper.core.base.requests.request")
    def test_invalid_exchange(self, mock_request: MagicMock) -> None:
        """Test invalid exchange returns error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.RequestException(
            "Not found"
        )
        mock_request.return_value = mock_response

        fund = Fundamentals()
        result = fund.get_fundamentals(exchange="INVALID_EXCHANGE", symbol="AAPL")

        assert result["status"] == STATUS_FAILED
        assert "Invalid exchange" in result["error"]


class TestGetFundamentalsSuccess:
    """Test get_fundamentals successful responses."""

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_success_with_all_fields(self, mock_fetch: MagicMock) -> None:
        """Test success with all fields."""
        mock_fetch.return_value = {
            "status": STATUS_SUCCESS,
            "data": {
                "symbol": "NASDAQ:AAPL",
                "total_revenue": 394328000000,
                "net_income": 99803000000,
            },
            "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
            "error": None,
        }

        fund = Fundamentals()
        result = fund.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None
        assert result["data"]["symbol"] == "NASDAQ:AAPL"

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_success_with_custom_fields(self, mock_fetch: MagicMock) -> None:
        """Test success with custom fields."""
        mock_fetch.return_value = {
            "status": STATUS_SUCCESS,
            "data": {
                "symbol": "NASDAQ:AAPL",
                "total_revenue": 394328000000,
                "net_income": 99803000000,
            },
            "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
            "error": None,
        }

        fund = Fundamentals()
        result = fund.get_fundamentals(
            exchange="NASDAQ",
            symbol="AAPL",
            fields=["total_revenue", "net_income"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_missing_fields_in_response(self, mock_fetch: MagicMock) -> None:
        """Test missing fields are handled gracefully."""
        mock_fetch.return_value = {
            "status": STATUS_SUCCESS,
            "data": {
                "symbol": "NASDAQ:AAPL",
                "total_revenue": 394328000000,
                "net_income": None,
            },
            "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
            "error": None,
        }

        fund = Fundamentals()
        result = fund.get_fundamentals(
            exchange="NASDAQ",
            symbol="AAPL",
            fields=["total_revenue", "net_income"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"]["total_revenue"] == 394328000000
        assert result["data"]["net_income"] is None


class TestGetFundamentalsMetadata:
    """Test metadata in responses."""

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_success_metadata(self, mock_fetch: MagicMock) -> None:
        """Test success metadata contains exchange and symbol."""
        mock_fetch.return_value = {
            "status": STATUS_SUCCESS,
            "data": {"symbol": "NASDAQ:AAPL"},
            "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
            "error": None,
        }

        fund = Fundamentals()
        result = fund.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert result["metadata"]["exchange"] == "NASDAQ"
        assert result["metadata"]["symbol"] == "AAPL"

    @patch("tv_scraper.core.base.requests.request")
    def test_error_metadata(self, mock_request: MagicMock) -> None:
        """Test error metadata contains exchange and symbol."""
        mock_request.side_effect = requests.RequestException("Network error")

        fund = Fundamentals()
        result = fund.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert result["metadata"]["exchange"] == "NASDAQ"
        assert result["metadata"]["symbol"] == "AAPL"


class TestGetFundamentalsResponseEnvelope:
    """Test standardized response envelope."""

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_success_response_structure(self, mock_fetch: MagicMock) -> None:
        """Test success response has all required keys."""
        mock_fetch.return_value = {
            "status": STATUS_SUCCESS,
            "data": {"symbol": "NASDAQ:AAPL"},
            "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
            "error": None,
        }

        fund = Fundamentals()
        result = fund.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None

    @patch("tv_scraper.core.base.requests.request")
    def test_error_response_structure(self, mock_request: MagicMock) -> None:
        """Test error response has all required keys."""
        mock_request.side_effect = requests.RequestException("Network error")

        fund = Fundamentals()
        result = fund.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None


class TestGetFundamentalsExport:
    """Test export functionality."""

    def test_export_json_enabled(self) -> None:
        """Test export setting is stored correctly."""
        fund = Fundamentals(export_result=True, export_type="json")
        assert fund.export_result is True
        assert fund.export_type == "json"

    def test_export_csv_enabled(self) -> None:
        """Test CSV export setting is stored correctly."""
        fund = Fundamentals(export_result=True, export_type="csv")
        assert fund.export_result is True
        assert fund.export_type == "csv"

    def test_export_disabled(self) -> None:
        """Test export disabled by default."""
        fund = Fundamentals()
        assert fund.export_result is False


class TestFundamentalsEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_none_fields_returns_all(self) -> None:
        """Test None fields means all fields are used."""
        fund = Fundamentals()
        assert fund.ALL_FIELDS is not None
        assert len(fund.ALL_FIELDS) > 0

    @patch.object(Fundamentals, "_fetch_symbol_fields")
    def test_duplicate_fields_in_request(self, mock_fetch: MagicMock) -> None:
        """Test duplicate fields are handled."""
        mock_fetch.return_value = {
            "status": STATUS_SUCCESS,
            "data": {"symbol": "NASDAQ:AAPL", "total_revenue": 100},
            "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
            "error": None,
        }

        fund = Fundamentals()
        result = fund.get_fundamentals(
            exchange="NASDAQ",
            symbol="AAPL",
            fields=["total_revenue", "total_revenue"],
        )

        assert result["status"] == STATUS_SUCCESS

    def test_case_sensitivity_in_fields(self) -> None:
        """Test field names are case sensitive."""
        fund = Fundamentals()
        result = fund.get_fundamentals(
            exchange="NASDAQ",
            symbol="AAPL",
            fields=["Total_Revenue"],
        )

        assert result["status"] == STATUS_FAILED
        assert "Invalid field" in result["error"]
