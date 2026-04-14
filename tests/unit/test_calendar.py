"""Unit tests for Calendar scraper.

Tests isolated functionality with mocking - no network calls.
"""

from datetime import datetime
from unittest.mock import patch

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.events.calendar import (
    _DAYS_OFFSET,
    _SECONDS_PER_DAY,
    DEFAULT_DIVIDEND_FIELDS,
    DEFAULT_EARNINGS_FIELDS,
    Calendar,
)


class TestCalendarInit:
    """Tests for Calendar initialization."""

    def test_default_init(self):
        """Test default initialization."""
        cal = Calendar()
        assert cal.export_result is False
        assert cal.export_type == "json"
        assert cal.timeout == 10

    def test_custom_init(self):
        """Test custom initialization."""
        cal = Calendar(export="csv", timeout=60)
        assert cal.export_result is True
        assert cal.export_type == "csv"
        assert cal.timeout == 60

    def test_inherits_from_scanner_scraper(self):
        """Verify Calendar inherits ScannerScraper methods."""
        cal = Calendar()
        assert hasattr(cal, "_success_response")
        assert hasattr(cal, "_error_response")
        assert hasattr(cal, "_export")
        assert hasattr(cal, "_request")


class TestCalendarConstants:
    """Tests for Calendar constants."""

    def test_dividend_default_fields(self):
        """Verify dividend default fields are defined."""
        assert isinstance(DEFAULT_DIVIDEND_FIELDS, list)
        assert len(DEFAULT_DIVIDEND_FIELDS) > 0
        assert "name" in DEFAULT_DIVIDEND_FIELDS
        assert "description" in DEFAULT_DIVIDEND_FIELDS
        assert "dividend_amount_recent" in DEFAULT_DIVIDEND_FIELDS

    def test_earnings_default_fields(self):
        """Verify earnings default fields are defined."""
        assert isinstance(DEFAULT_EARNINGS_FIELDS, list)
        assert len(DEFAULT_EARNINGS_FIELDS) > 0
        assert "name" in DEFAULT_EARNINGS_FIELDS
        assert "description" in DEFAULT_EARNINGS_FIELDS
        assert "earnings_per_share_fq" in DEFAULT_EARNINGS_FIELDS

    def test_days_offset_constant(self):
        """Verify days offset constant."""
        assert _DAYS_OFFSET == 3

    def test_seconds_per_day_constant(self):
        """Verify seconds per day constant."""
        assert _SECONDS_PER_DAY == 86400


class TestGetDividendsParameters:
    """Test get_dividends with various parameters."""

    @patch.object(Calendar, "_request")
    def test_dividends_timestamp_from_only(self, mock_request):
        """Test dividends with only timestamp_from specified."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_dividends(timestamp_from=1704067200)

        assert mock_request.called
        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        filter_item = payload.get("filter", [{}])[0]
        assert filter_item["right"][0] == 1704067200

    @patch.object(Calendar, "_request")
    def test_dividends_timestamp_to_only(self, mock_request):
        """Test dividends with only timestamp_to specified."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_dividends(timestamp_to=1735689600)

        assert mock_request.called
        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        filter_item = payload.get("filter", [{}])[0]
        assert filter_item["right"][1] == 1735689600

    @patch.object(Calendar, "_request")
    def test_dividends_both_timestamps(self, mock_request):
        """Test dividends with both timestamps specified."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_dividends(timestamp_from=1704067200, timestamp_to=1735689600)

        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        filter_item = payload.get("filter", [{}])[0]
        assert filter_item["right"] == [1704067200, 1735689600]

    @patch.object(Calendar, "_request")
    def test_dividends_no_timestamps(self, mock_request):
        """Test dividends with no timestamps (uses defaults)."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_dividends()

        assert mock_request.called
        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        filter_item = payload.get("filter", [{}])[0]
        now = datetime.now().timestamp()
        midnight = now - (now % _SECONDS_PER_DAY)
        expected_from = int(midnight - _DAYS_OFFSET * _SECONDS_PER_DAY)
        assert filter_item["right"][0] == expected_from

    @patch.object(Calendar, "_request")
    def test_dividends_markets_none(self, mock_request):
        """Test dividends with markets=None."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_dividends(markets=None)

        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        assert "markets" not in payload

    @patch.object(Calendar, "_request")
    def test_dividends_markets_single(self, mock_request):
        """Test dividends with single market."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_dividends(markets=["america"])

        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        assert payload.get("markets") == ["america"]

    @patch.object(Calendar, "_request")
    def test_dividends_markets_multiple(self, mock_request):
        """Test dividends with multiple markets."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_dividends(markets=["america", "uk"])

        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        assert payload.get("markets") == ["america", "uk"]

    @patch.object(Calendar, "_request")
    def test_dividends_fields_none(self, mock_request):
        """Test dividends with fields=None (uses defaults)."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_dividends(fields=None)

        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        assert payload.get("columns") == DEFAULT_DIVIDEND_FIELDS

    @patch.object(Calendar, "_request")
    def test_dividends_custom_fields(self, mock_request):
        """Test dividends with custom fields."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()
        custom_fields = ["name", "description", "market"]

        cal.get_dividends(fields=custom_fields)

        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        assert payload.get("columns") == custom_fields

    @patch.object(Calendar, "_request")
    def test_dividends_language(self, mock_request):
        """Test dividends with language parameter."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_dividends(lang="en")

        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        assert payload.get("options", {}).get("lang") == "en"


class TestGetEarningsParameters:
    """Test get_earnings with various parameters."""

    @patch.object(Calendar, "_request")
    def test_earnings_timestamp_from_only(self, mock_request):
        """Test earnings with only timestamp_from specified."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_earnings(timestamp_from=1704067200)

        assert mock_request.called
        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        filter_item = payload.get("filter", [{}])[0]
        assert filter_item["right"][0] == 1704067200

    @patch.object(Calendar, "_request")
    def test_earnings_timestamp_to_only(self, mock_request):
        """Test earnings with only timestamp_to specified."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_earnings(timestamp_to=1735689600)

        assert mock_request.called
        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        filter_item = payload.get("filter", [{}])[0]
        assert filter_item["right"][1] == 1735689600

    @patch.object(Calendar, "_request")
    def test_earnings_both_timestamps(self, mock_request):
        """Test earnings with both timestamps specified."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_earnings(timestamp_from=1704067200, timestamp_to=1735689600)

        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        filter_item = payload.get("filter", [{}])[0]
        assert filter_item["right"] == [1704067200, 1735689600]

    @patch.object(Calendar, "_request")
    def test_earnings_no_timestamps(self, mock_request):
        """Test earnings with no timestamps (uses defaults)."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_earnings()

        assert mock_request.called
        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        filter_item = payload.get("filter", [{}])[0]
        now = datetime.now().timestamp()
        midnight = now - (now % _SECONDS_PER_DAY)
        expected_from = int(midnight - _DAYS_OFFSET * _SECONDS_PER_DAY)
        assert filter_item["right"][0] == expected_from

    @patch.object(Calendar, "_request")
    def test_earnings_markets_none(self, mock_request):
        """Test earnings with markets=None."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_earnings(markets=None)

        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        assert "markets" not in payload

    @patch.object(Calendar, "_request")
    def test_earnings_markets_single(self, mock_request):
        """Test earnings with single market."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_earnings(markets=["america"])

        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        assert payload.get("markets") == ["america"]

    @patch.object(Calendar, "_request")
    def test_earnings_markets_multiple(self, mock_request):
        """Test earnings with multiple markets."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_earnings(markets=["america", "uk"])

        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        assert payload.get("markets") == ["america", "uk"]

    @patch.object(Calendar, "_request")
    def test_earnings_fields_none(self, mock_request):
        """Test earnings with fields=None (uses defaults)."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_earnings(fields=None)

        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        assert payload.get("columns") == DEFAULT_EARNINGS_FIELDS

    @patch.object(Calendar, "_request")
    def test_earnings_custom_fields(self, mock_request):
        """Test earnings with custom fields."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()
        custom_fields = ["name", "earnings_per_share_fq"]

        cal.get_earnings(fields=custom_fields)

        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        assert payload.get("columns") == custom_fields

    @patch.object(Calendar, "_request")
    def test_earnings_language(self, mock_request):
        """Test earnings with language parameter."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_earnings(lang="en")

        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        assert payload.get("options", {}).get("lang") == "en"


class TestCalendarFieldValidation:
    """Test field validation."""

    def test_dividends_invalid_field_raises_error(self):
        """Test invalid field raises ValidationError."""
        cal = Calendar()
        result = cal.get_dividends(fields=["invalid_field_xyz"])
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "invalid_field_xyz" in result["error"]

    def test_earnings_invalid_field_raises_error(self):
        """Test invalid earnings field raises ValidationError."""
        cal = Calendar()
        result = cal.get_earnings(fields=["nonexistent_field_abc"])
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "nonexistent_field_abc" in result["error"]

    def test_dividends_partial_invalid_fields(self):
        """Test mix of valid and invalid dividend fields."""
        cal = Calendar()
        result = cal.get_dividends(fields=["name", "invalid_field"])
        assert result["status"] == STATUS_FAILED
        assert "invalid_field" in result["error"]

    def test_earnings_partial_invalid_fields(self):
        """Test mix of valid and invalid earnings fields."""
        cal = Calendar()
        result = cal.get_earnings(fields=["name", "bad_field"])
        assert result["status"] == STATUS_FAILED
        assert "bad_field" in result["error"]


class TestCalendarErrorHandling:
    """Test error handling."""

    @patch.object(Calendar, "_request")
    def test_network_error_returns_failed(self, mock_request):
        """Test network error returns failed status."""
        mock_request.return_value = (None, "Network error: Connection refused")
        cal = Calendar()

        result = cal.get_dividends()

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Network error" in result["error"]

    @patch.object(Calendar, "_request")
    def test_empty_response_handled(self, mock_request):
        """Test empty response is handled correctly."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        result = cal.get_dividends()

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] == []

    @patch.object(Calendar, "_request")
    def test_non_list_data_handled(self, mock_request):
        """Test non-list data is converted to empty list."""
        mock_request.return_value = ({"data": "not a list"}, None)
        cal = Calendar()

        result = cal.get_dividends()

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] == []


class TestCalendarResponseEnvelope:
    """Test standardized response envelope."""

    @patch.object(Calendar, "_request")
    def test_success_has_all_keys(self, mock_request):
        """Test success response has required keys."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        result = cal.get_dividends()

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None

    @patch.object(Calendar, "_request")
    def test_error_has_all_keys(self, mock_request):
        """Test error response has required keys."""
        mock_request.return_value = (None, "Network error")
        cal = Calendar()

        result = cal.get_dividends()

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    @patch.object(Calendar, "_request")
    def test_metadata_contains_event_type(self, mock_request):
        """Test metadata contains event_type field."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        result = cal.get_dividends()
        assert result["metadata"]["event_type"] == "dividends"

        result = cal.get_earnings()
        assert result["metadata"]["event_type"] == "earnings"

    @patch.object(Calendar, "_request")
    def test_metadata_contains_total(self, mock_request):
        """Test metadata contains total count."""
        mock_data = [{"s": "A", "d": [1]}, {"s": "B", "d": [2]}, {"s": "C", "d": [3]}]
        mock_request.return_value = ({"data": mock_data}, None)
        cal = Calendar()

        result = cal.get_dividends()
        assert result["metadata"]["total"] == 3


class TestCalendarScannerRowMapping:
    """Test scanner row mapping functionality."""

    @patch.object(Calendar, "_request")
    def test_map_scanner_rows(self, mock_request):
        """Test scanner rows are mapped correctly."""
        scanner_rows = [
            {"s": "NASDAQ:AAPL", "d": ["Apple Inc", "tech company", 0.5, "2024-01-15"]},
            {
                "s": "NYSE:MSFT",
                "d": ["Microsoft Corp", "tech company", 0.75, "2024-01-16"],
            },
        ]
        mock_request.return_value = ({"data": scanner_rows}, None)
        cal = Calendar()
        fields = ["name", "description", "dividends_yield", "dividend_ex_date_recent"]

        result = cal.get_dividends(fields=fields)

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 2
        assert result["data"][0]["symbol"] == "NASDAQ:AAPL"
        assert result["data"][0]["name"] == "Apple Inc"
        assert result["data"][1]["symbol"] == "NYSE:MSFT"

    @patch.object(Calendar, "_request")
    def test_map_scanner_rows_handles_missing_values(self, mock_request):
        """Test scanner rows handle missing values."""
        scanner_rows = [
            {"s": "NASDAQ:AAPL", "d": ["Apple Inc"]},
        ]
        mock_request.return_value = ({"data": scanner_rows}, None)
        cal = Calendar()
        fields = ["name", "description", "dividends_yield", "dividend_ex_date_recent"]

        result = cal.get_dividends(fields=fields)

        assert result["status"] == STATUS_SUCCESS
        assert result["data"][0]["symbol"] == "NASDAQ:AAPL"
        assert result["data"][0]["name"] == "Apple Inc"
        assert result["data"][0]["description"] is None
        assert result["data"][0]["dividends_yield"] is None

    @patch.object(Calendar, "_request")
    def test_map_scanner_rows_handles_missing_symbol(self, mock_request):
        """Test scanner rows handle missing symbol."""
        scanner_rows = [
            {"d": ["Apple Inc", "tech company"]},
        ]
        mock_request.return_value = ({"data": scanner_rows}, None)
        cal = Calendar()
        fields = ["name", "description"]

        result = cal.get_dividends(fields=fields)

        assert result["status"] == STATUS_SUCCESS
        assert result["data"][0]["symbol"] == ""


class TestCalendarExport:
    """Test export functionality."""

    @patch.object(Calendar, "_request")
    @patch.object(Calendar, "_export")
    def test_export_called_when_enabled(self, mock_export, mock_request):
        """Test export is called when export_result is True."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar(export="json")

        cal.get_dividends()

        mock_export.assert_called_once()
        call_args = mock_export.call_args
        assert call_args[1]["data_category"] == "calendar"

    @patch.object(Calendar, "_request")
    @patch.object(Calendar, "_export")
    def test_export_not_called_when_disabled(self, mock_export, mock_request):
        """Test export is not called when export_result is False."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar(export=None)

        cal.get_dividends()

        mock_export.assert_not_called()

    @patch.object(Calendar, "_request")
    @patch.object(Calendar, "_export")
    def test_export_data_is_mapped(self, mock_export, mock_request):
        """Test export receives correctly mapped data."""
        scanner_rows = [{"s": "AAPL", "d": ["Apple", "tech", 0.5]}]
        mock_request.return_value = ({"data": scanner_rows}, None)
        cal = Calendar()
        cal.export_result = True

        cal.get_dividends(fields=["name", "description", "dividends_yield"])

        mock_export.assert_called_once()
        export_data = mock_export.call_args[1]["data"]
        assert isinstance(export_data, list)
        assert export_data[0]["symbol"] == "AAPL"


class TestCalendarEdgeCases:
    """Test edge cases."""

    @patch.object(Calendar, "_request")
    def test_empty_timestamps_edge_case(self, mock_request):
        """Test with timestamp 0."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_dividends(timestamp_from=0, timestamp_to=86400)

        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        filter_item = payload.get("filter", [{}])[0]
        assert filter_item["right"] == [0, 86400]

    @patch.object(Calendar, "_request")
    def test_large_timestamps(self, mock_request):
        """Test with very large timestamps."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()
        future_ts = 4102444800

        cal.get_dividends(timestamp_from=future_ts, timestamp_to=future_ts + 86400)

        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        filter_item = payload.get("filter", [{}])[0]
        assert filter_item["right"][0] == future_ts

    @patch.object(Calendar, "_request")
    def test_same_from_and_to_timestamp(self, mock_request):
        """Test with same from and to timestamp."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()
        ts = 1704067200

        cal.get_dividends(timestamp_from=ts, timestamp_to=ts)

        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        filter_item = payload.get("filter", [{}])[0]
        assert filter_item["right"] == [ts, ts]

    @patch.object(Calendar, "_request")
    def test_filter_left_for_dividends(self, mock_request):
        """Test filter_left is set correctly for dividends."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_dividends()

        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        filter_item = payload.get("filter", [{}])[0]
        assert "dividend" in filter_item["left"]

    @patch.object(Calendar, "_request")
    def test_filter_left_for_earnings(self, mock_request):
        """Test filter_left is set correctly for earnings."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        cal.get_earnings()

        call_kwargs = mock_request.call_args[1]
        payload = call_kwargs.get("json_payload", {})
        filter_item = payload.get("filter", [{}])[0]
        assert "earnings" in filter_item["left"]
