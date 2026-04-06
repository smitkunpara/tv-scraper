"""Live API tests for calendar scraper.

Tests real HTTP connections to TradingView calendar endpoint.
Requires live TradingView connection.
"""

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.events.calendar import Calendar


@pytest.mark.live
class TestLiveDividends:
    """Test dividend calendar with real API calls."""

    def test_live_dividends_default_range(self) -> None:
        """Verify basic dividends fetching with default date range."""
        scraper = Calendar()
        result = scraper.get_dividends()
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)
        assert result["error"] is None
        assert "timestamp_from" in result["metadata"]
        assert "timestamp_to" in result["metadata"]
        assert "event_type" in result["metadata"]
        assert result["metadata"]["event_type"] == "dividends"

    def test_live_dividends_with_timestamp_range(self) -> None:
        """Verify dividends with specific timestamp range."""
        scraper = Calendar()
        from_timestamp = 1704067200
        to_timestamp = 1735689600
        result = scraper.get_dividends(
            timestamp_from=from_timestamp, timestamp_to=to_timestamp
        )
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)
        assert result["metadata"]["timestamp_from"] == from_timestamp
        assert result["metadata"]["timestamp_to"] == to_timestamp

    def test_live_dividends_america_market(self) -> None:
        """Verify dividends filtering by America market."""
        scraper = Calendar()
        result = scraper.get_dividends(markets=["america"])
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)
        assert result["metadata"]["markets"] == ["america"]

    def test_live_dividends_multiple_markets(self) -> None:
        """Verify dividends with multiple market filters."""
        scraper = Calendar()
        result = scraper.get_dividends(markets=["america", "uk"])
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)
        assert result["metadata"]["markets"] == ["america", "uk"]

    def test_live_dividends_custom_fields(self) -> None:
        """Verify dividends with custom field selection."""
        scraper = Calendar()
        custom_fields = ["name", "description", "market", "dividend_amount_recent"]
        result = scraper.get_dividends(fields=custom_fields, markets=["america"])
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)
        for item in result["data"]:
            assert "name" in item
            assert "description" in item
            assert "market" in item

    def test_live_dividends_with_language(self) -> None:
        """Verify dividends with language parameter."""
        scraper = Calendar()
        result = scraper.get_dividends(markets=["america"], lang="en")
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)

    def test_live_dividends_future_date_range(self) -> None:
        """Verify dividends with future date range."""
        scraper = Calendar()
        from_timestamp = 1735689600
        to_timestamp = 1767225600
        result = scraper.get_dividends(
            timestamp_from=from_timestamp, timestamp_to=to_timestamp
        )
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)


@pytest.mark.live
class TestLiveEarnings:
    """Test earnings calendar with real API calls."""

    def test_live_earnings_default_range(self) -> None:
        """Verify basic earnings fetching with default date range."""
        scraper = Calendar()
        result = scraper.get_earnings()
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)
        assert result["error"] is None
        assert "timestamp_from" in result["metadata"]
        assert "timestamp_to" in result["metadata"]
        assert "event_type" in result["metadata"]
        assert result["metadata"]["event_type"] == "earnings"

    def test_live_earnings_with_timestamp_range(self) -> None:
        """Verify earnings with specific timestamp range."""
        scraper = Calendar()
        from_timestamp = 1704067200
        to_timestamp = 1735689600
        result = scraper.get_earnings(
            timestamp_from=from_timestamp, timestamp_to=to_timestamp
        )
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)
        assert result["metadata"]["timestamp_from"] == from_timestamp
        assert result["metadata"]["timestamp_to"] == to_timestamp

    def test_live_earnings_america_market(self) -> None:
        """Verify earnings filtering by America market."""
        scraper = Calendar()
        result = scraper.get_earnings(markets=["america"])
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)
        assert result["metadata"]["markets"] == ["america"]

    def test_live_earnings_multiple_markets(self) -> None:
        """Verify earnings with multiple market filters."""
        scraper = Calendar()
        result = scraper.get_earnings(markets=["america", "uk"])
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)
        assert result["metadata"]["markets"] == ["america", "uk"]

    def test_live_earnings_custom_fields(self) -> None:
        """Verify earnings with custom field selection."""
        scraper = Calendar()
        custom_fields = [
            "name",
            "description",
            "market",
            "earnings_per_share_fq",
            "earnings_release_date",
        ]
        result = scraper.get_earnings(fields=custom_fields, markets=["america"])
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)
        for item in result["data"]:
            assert "name" in item
            assert "description" in item

    def test_live_earnings_with_language(self) -> None:
        """Verify earnings with language parameter."""
        scraper = Calendar()
        result = scraper.get_earnings(markets=["america"], lang="en")
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)

    def test_live_earnings_future_date_range(self) -> None:
        """Verify earnings with future date range."""
        scraper = Calendar()
        from_timestamp = 1735689600
        to_timestamp = 1767225600
        result = scraper.get_earnings(
            timestamp_from=from_timestamp, timestamp_to=to_timestamp
        )
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)


@pytest.mark.live
class TestLiveCalendarMetadata:
    """Test metadata in calendar responses."""

    def test_metadata_contains_required_fields_dividends(self) -> None:
        """Verify metadata contains all required fields for dividends."""
        scraper = Calendar()
        result = scraper.get_dividends()
        assert result["status"] == STATUS_SUCCESS
        metadata = result["metadata"]
        assert "event_type" in metadata
        assert "total" in metadata
        assert "timestamp_from" in metadata
        assert "timestamp_to" in metadata

    def test_metadata_contains_required_fields_earnings(self) -> None:
        """Verify metadata contains all required fields for earnings."""
        scraper = Calendar()
        result = scraper.get_earnings()
        assert result["status"] == STATUS_SUCCESS
        metadata = result["metadata"]
        assert "event_type" in metadata
        assert "total" in metadata
        assert "timestamp_from" in metadata
        assert "timestamp_to" in metadata

    def test_metadata_total_matches_data_length(self) -> None:
        """Verify total count matches actual data length."""
        scraper = Calendar()
        result = scraper.get_dividends(markets=["america"])
        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["total"] == len(result["data"])

    def test_metadata_markets_included_when_provided(self) -> None:
        """Verify markets appear in metadata when provided."""
        scraper = Calendar()
        result = scraper.get_dividends(markets=["america"])
        assert "markets" in result["metadata"]
        assert result["metadata"]["markets"] == ["america"]


@pytest.mark.live
class TestLiveCalendarEdgeCases:
    """Test edge cases for calendar scraper."""

    def test_live_calendar_empty_date_range(self) -> None:
        """Verify handling of date range with no events."""
        scraper = Calendar()
        from_timestamp = 946684800
        to_timestamp = 946684900
        result = scraper.get_dividends(
            timestamp_from=from_timestamp, timestamp_to=to_timestamp
        )
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)

    def test_live_calendar_invalid_fields(self) -> None:
        """Verify invalid field names are rejected."""
        scraper = Calendar()
        result = scraper.get_dividends(fields=["invalid_field_xyz"])
        assert result["status"] == "failed"
        assert result["data"] is None
        assert result["error"] is not None
        assert "invalid_field_xyz" in result["error"]

    def test_live_earnings_invalid_fields(self) -> None:
        """Verify invalid field names are rejected for earnings."""
        scraper = Calendar()
        result = scraper.get_earnings(fields=["nonexistent_field_abc"])
        assert result["status"] == "failed"
        assert result["data"] is None
        assert result["error"] is not None

    def test_live_calendar_partial_invalid_fields(self) -> None:
        """Verify mix of valid and invalid fields is rejected."""
        scraper = Calendar()
        result = scraper.get_dividends(
            fields=["name", "invalid_field_xyz", "description"]
        )
        assert result["status"] == "failed"
        assert result["data"] is None
        assert "invalid_field_xyz" in result["error"]

    def test_live_calendar_past_date_range(self) -> None:
        """Verify past date range is handled correctly."""
        scraper = Calendar()
        from_timestamp = 1577836800
        to_timestamp = 1577923200
        result = scraper.get_dividends(
            timestamp_from=from_timestamp, timestamp_to=to_timestamp
        )
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)


@pytest.mark.live
class TestLiveCalendarResponseEnvelope:
    """Test standardized response envelope."""

    def test_success_response_has_all_keys(self) -> None:
        """Verify success response has required keys."""
        scraper = Calendar()
        result = scraper.get_dividends()
        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None

    def test_failed_response_has_all_keys(self) -> None:
        """Verify failed response has required keys."""
        scraper = Calendar()
        result = scraper.get_dividends(fields=["invalid_field_xyz"])
        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == "failed"
        assert result["data"] is None
        assert result["error"] is not None
