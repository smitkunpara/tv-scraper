"""Mock tests for calendar scraper.

Uses saved JSON fixtures from live API tests.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.events.calendar import Calendar

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "calendar"


def load_fixture(name: str) -> dict[str, Any]:
    """Load fixture from file."""
    filepath = FIXTURES_DIR / f"{name}.json"
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    pytest.skip(f"Fixture not found: {filepath}")


@pytest.fixture
def mock_request():
    """Mock the _request method."""
    with patch.object(Calendar, "_request") as mock:
        yield mock


@pytest.fixture
def calendar():
    """Create Calendar instance."""
    return Calendar()


class TestMockDividends:
    """Test dividend calendar with mocked responses."""

    def test_dividends_default_range_mock(self, calendar, mock_request) -> None:
        """Verify dividends with default range using mock."""
        mock_response = load_fixture("dividends_default")
        mock_request.return_value = ({"data": mock_response.get("data", [])[:3]}, None)

        result = calendar.get_dividends()

        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert "calendar-dividends" in call_args[1].get("json_payload", {}).get(
            "label-product", ""
        ) or "calendar-dividends" in str(call_args)

    def test_dividends_with_timestamp_range_mock(self, calendar, mock_request) -> None:
        """Verify dividends with timestamp range using mock."""
        mock_request.return_value = ({"data": []}, None)

        from_timestamp = 1704067200
        to_timestamp = 1735689600
        result = calendar.get_dividends(
            timestamp_from=from_timestamp, timestamp_to=to_timestamp
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["timestamp_from"] == from_timestamp
        assert result["metadata"]["timestamp_to"] == to_timestamp

    def test_dividends_america_market_mock(self, calendar, mock_request) -> None:
        """Verify dividends with America market filter using mock."""
        mock_response = load_fixture("dividends_america")
        mock_request.return_value = ({"data": mock_response.get("data", [])[:5]}, None)

        result = calendar.get_dividends(markets=["america"])

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["markets"] == ["america"]
        assert isinstance(result["data"], list)

    def test_dividends_multi_market_mock(self, calendar, mock_request) -> None:
        """Verify dividends with multiple markets using mock."""
        mock_response = load_fixture("dividends_multi_market")
        mock_request.return_value = ({"data": mock_response.get("data", [])[:5]}, None)

        result = calendar.get_dividends(markets=["america", "uk"])

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["markets"] == ["america", "uk"]

    def test_dividends_custom_fields_mock(self, calendar, mock_request) -> None:
        """Verify dividends with custom fields using mock."""
        mock_data = [
            {
                "symbol": "NASDAQ:AAPL",
                "name": "Apple",
                "description": "Test",
                "market": "america",
            }
        ]
        mock_request.return_value = ({"data": mock_data}, None)

        custom_fields = ["name", "description", "market"]
        result = calendar.get_dividends(fields=custom_fields, markets=["america"])

        assert result["status"] == STATUS_SUCCESS
        for item in result["data"]:
            assert "name" in item
            assert "description" in item
            assert "market" in item

    def test_dividends_with_language_mock(self, calendar, mock_request) -> None:
        """Verify dividends with language using mock."""
        mock_request.return_value = ({"data": []}, None)

        result = calendar.get_dividends(lang="en")

        assert result["status"] == STATUS_SUCCESS
        mock_request.assert_called_once()

    def test_dividends_future_range_mock(self, calendar, mock_request) -> None:
        """Verify dividends with future date range using mock."""
        mock_request.return_value = ({"data": []}, None)

        from_timestamp = 1735689600
        to_timestamp = 1767225600
        result = calendar.get_dividends(
            timestamp_from=from_timestamp, timestamp_to=to_timestamp
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["timestamp_from"] == from_timestamp


class TestMockEarnings:
    """Test earnings calendar with mocked responses."""

    def test_earnings_default_range_mock(self, calendar, mock_request) -> None:
        """Verify earnings with default range using mock."""
        mock_response = load_fixture("earnings_default")
        mock_request.return_value = ({"data": mock_response.get("data", [])[:3]}, None)

        result = calendar.get_earnings()

        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)
        mock_request.assert_called_once()

    def test_earnings_with_timestamp_range_mock(self, calendar, mock_request) -> None:
        """Verify earnings with timestamp range using mock."""
        mock_request.return_value = ({"data": []}, None)

        from_timestamp = 1704067200
        to_timestamp = 1735689600
        result = calendar.get_earnings(
            timestamp_from=from_timestamp, timestamp_to=to_timestamp
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["timestamp_from"] == from_timestamp
        assert result["metadata"]["timestamp_to"] == to_timestamp

    def test_earnings_america_market_mock(self, calendar, mock_request) -> None:
        """Verify earnings with America market filter using mock."""
        mock_response = load_fixture("earnings_america")
        mock_request.return_value = ({"data": mock_response.get("data", [])[:5]}, None)

        result = calendar.get_earnings(markets=["america"])

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["markets"] == ["america"]

    def test_earnings_multi_market_mock(self, calendar, mock_request) -> None:
        """Verify earnings with multiple markets using mock."""
        mock_response = load_fixture("earnings_multi_market")
        mock_request.return_value = ({"data": mock_response.get("data", [])[:5]}, None)

        result = calendar.get_earnings(markets=["america", "uk"])

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["markets"] == ["america", "uk"]

    def test_earnings_custom_fields_mock(self, calendar, mock_request) -> None:
        """Verify earnings with custom fields using mock."""
        mock_data = [
            {
                "symbol": "NASDAQ:AAPL",
                "name": "Apple",
                "earnings_per_share_fq": 1.5,
            }
        ]
        mock_request.return_value = ({"data": mock_data}, None)

        custom_fields = ["name", "earnings_per_share_fq"]
        result = calendar.get_earnings(fields=custom_fields, markets=["america"])

        assert result["status"] == STATUS_SUCCESS
        for item in result["data"]:
            assert "name" in item
            assert "earnings_per_share_fq" in item

    def test_earnings_with_language_mock(self, calendar, mock_request) -> None:
        """Verify earnings with language using mock."""
        mock_request.return_value = ({"data": []}, None)

        result = calendar.get_earnings(lang="en")

        assert result["status"] == STATUS_SUCCESS


class TestMockErrorHandling:
    """Test error handling with mocks."""

    def test_dividends_network_error_mock(self, calendar, mock_request) -> None:
        """Verify network error handling for dividends."""
        mock_request.return_value = (None, "Network error: Connection timeout")

        result = calendar.get_dividends()

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Network error" in result["error"]

    def test_earnings_network_error_mock(self, calendar, mock_request) -> None:
        """Verify network error handling for earnings."""
        mock_request.return_value = (None, "Network error: Connection refused")

        result = calendar.get_earnings()

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Network error" in result["error"]

    def test_dividends_invalid_fields_mock(self, calendar, mock_request) -> None:
        """Verify invalid field validation for dividends."""
        result = calendar.get_dividends(fields=["invalid_field_xyz"])

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "invalid_field_xyz" in result["error"]
        mock_request.assert_not_called()

    def test_earnings_invalid_fields_mock(self, calendar, mock_request) -> None:
        """Verify invalid field validation for earnings."""
        result = calendar.get_earnings(fields=["nonexistent_field_abc"])

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "nonexistent_field_abc" in result["error"]
        mock_request.assert_not_called()


class TestMockResponseEnvelope:
    """Test standardized response envelope with mocks."""

    def test_success_response_structure_mock(self, calendar, mock_request) -> None:
        """Verify success response has correct structure."""
        mock_data = [{"symbol": "NASDAQ:AAPL", "name": "Apple"}]
        mock_request.return_value = ({"data": mock_data}, None)

        result = calendar.get_dividends()

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None

    def test_failed_response_structure_mock(self, calendar, mock_request) -> None:
        """Verify failed response has correct structure."""
        mock_request.return_value = (None, "Network error")

        result = calendar.get_dividends()

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None


class TestMockDataMapping:
    """Test scanner row mapping with mocks."""

    def test_dividends_scanner_row_mapping_mock(self, calendar, mock_request) -> None:
        """Verify scanner rows are correctly mapped."""
        scanner_rows = [
            {"s": "NASDAQ:AAPL", "d": ["2024-01-15", "2024-01-22", "Apple Inc", 0.24]},
            {
                "s": "NYSE:MSFT",
                "d": ["2024-01-16", "2024-01-23", "Microsoft Corp", 0.75],
            },
        ]
        mock_request.return_value = ({"data": scanner_rows}, None)

        result = calendar.get_dividends(
            fields=[
                "dividend_ex_date_recent",
                "dividend_ex_date_upcoming",
                "name",
                "dividend_amount_recent",
            ]
        )

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 2
        assert result["data"][0]["symbol"] == "NASDAQ:AAPL"
        assert result["data"][0]["name"] == "Apple Inc"

    def test_earnings_scanner_row_mapping_mock(self, calendar, mock_request) -> None:
        """Verify earnings scanner rows are correctly mapped."""
        scanner_rows = [
            {"s": "NASDAQ:AAPL", "d": ["2024-01-18", 1.5, 50000000000]},
            {"s": "NYSE:MSFT", "d": ["2024-01-23", 2.9, 75000000000]},
        ]
        mock_request.return_value = ({"data": scanner_rows}, None)

        result = calendar.get_earnings(
            fields=["earnings_release_date", "earnings_per_share_fq", "revenue_fq"]
        )

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 2
        assert result["data"][0]["symbol"] == "NASDAQ:AAPL"
        assert result["data"][0]["earnings_per_share_fq"] == 1.5

    def test_empty_data_response_mock(self, calendar, mock_request) -> None:
        """Verify empty data response is handled correctly."""
        mock_request.return_value = ({"data": []}, None)

        result = calendar.get_dividends()

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] == []
        assert result["metadata"]["total"] == 0


class TestMockExport:
    """Test export functionality with mocks."""

    def test_dividends_export_enabled_mock(self, calendar, mock_request) -> None:
        """Verify export is called when enabled."""
        mock_request.return_value = ({"data": []}, None)
        calendar.export_result = True
        calendar.export_type = "json"

        with patch.object(calendar, "_export") as mock_export:
            calendar.get_dividends()
            mock_export.assert_called_once()

    def test_earnings_export_enabled_mock(self, calendar, mock_request) -> None:
        """Verify export is called for earnings when enabled."""
        mock_request.return_value = ({"data": []}, None)
        calendar.export_result = True
        calendar.export_type = "json"

        with patch.object(calendar, "_export") as mock_export:
            calendar.get_earnings()
            mock_export.assert_called_once()

    def test_export_not_called_when_disabled_mock(self, calendar, mock_request) -> None:
        """Verify export is not called when disabled."""
        mock_request.return_value = ({"data": []}, None)
        calendar.export_result = False

        with patch.object(calendar, "_export") as mock_export:
            calendar.get_dividends()
            mock_export.assert_not_called()
