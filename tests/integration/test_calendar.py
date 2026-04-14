"""Integration tests for Calendar scraper.

Tests cross-module workflows and combined functionality.
"""

from unittest.mock import patch

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.events.calendar import Calendar
from tv_scraper.scrapers.screening.screener import Screener
from tv_scraper.scrapers.social.news import News


@pytest.fixture
def calendar():
    """Create Calendar instance."""
    return Calendar()


@pytest.fixture
def screener():
    """Create Screener instance."""
    return Screener()


@pytest.fixture
def news():
    """Create News instance."""
    return News()


class TestCalendarWithScreener:
    """Test Calendar combined with Screener workflows."""

    @patch.object(Calendar, "_request")
    @patch.object(Screener, "_request")
    def test_calendar_with_multiple_screener_results(
        self, mock_screener_request, mock_calendar_request
    ):
        """Test calendar works with multiple screener queries."""
        screener_data = [
            {"symbol": f"NYSE:SYM{i}", "name": f"Symbol {i}"} for i in range(10)
        ]
        mock_screener_request.return_value = ({"data": screener_data}, None)
        mock_calendar_request.return_value = ({"data": []}, None)

        screener = Screener()
        cal = Calendar()

        result1 = screener.get_screener(market="america", limit=5)
        assert result1["status"] == STATUS_SUCCESS

        mock_calendar_request.return_value = ({"data": []}, None)
        result2 = cal.get_dividends(markets=["america"])
        assert result2["status"] == STATUS_SUCCESS

        mock_screener_request.return_value = ({"data": screener_data}, None)
        result3 = screener.get_screener(market="uk", limit=5)
        assert result3["status"] == STATUS_SUCCESS

        mock_calendar_request.return_value = ({"data": []}, None)
        result4 = cal.get_earnings(markets=["uk"])
        assert result4["status"] == STATUS_SUCCESS


class TestCalendarWithNews:
    """Test Calendar combined with News workflows."""

    @patch.object(Calendar, "_request")
    @patch.object(News, "_request")
    def test_get_earnings_followed_by_news(
        self, mock_news_request, mock_calendar_request
    ):
        """Test earnings fetching followed by news for earnings symbols."""
        calendar_data = [
            {
                "symbol": "NASDAQ:AAPL",
                "name": "Apple Inc",
                "earnings_release_date": "2024-01-18",
            },
            {
                "symbol": "NYSE:JPM",
                "name": "JPMorgan Chase",
                "earnings_release_date": "2024-01-12",
            },
        ]
        mock_calendar_request.return_value = ({"data": calendar_data}, None)
        mock_news_request.return_value = ({"items": []}, None)

        cal = Calendar()
        news = News()

        earnings_result = cal.get_earnings(markets=["america"])
        assert earnings_result["status"] == STATUS_SUCCESS

        news_result = news.get_news_headlines(exchange="NASDAQ", symbol="AAPL")
        assert "status" in news_result

    @patch.object(Calendar, "_request")
    @patch.object(News, "_request")
    def test_get_dividends_with_related_news(
        self, mock_news_request, mock_calendar_request
    ):
        """Test dividends fetching with related news fetching."""
        calendar_data = [
            {
                "symbol": "NASDAQ:AAPL",
                "name": "Apple Inc",
                "dividend_ex_date_recent": "2024-01-12",
            }
        ]
        mock_calendar_request.return_value = ({"data": calendar_data}, None)
        mock_news_request.return_value = ({"items": []}, None)

        cal = Calendar()
        news = News()

        dividends_result = cal.get_dividends(markets=["america"])
        assert dividends_result["status"] == STATUS_SUCCESS

        news_result = news.get_news_headlines(exchange="NASDAQ", symbol="AAPL")
        assert "status" in news_result


class TestCalendarMultipleInstances:
    """Test multiple Calendar instances working together."""

    @patch.object(Calendar, "_request")
    def test_calendar_instances_independent(self, mock_request):
        """Test multiple Calendar instances work independently."""
        mock_request.return_value = ({"data": []}, None)

        cal1 = Calendar()
        cal2 = Calendar(export="json")

        result1 = cal1.get_dividends(markets=["america"])
        result2 = cal2.get_earnings(markets=["uk"])

        assert result1["status"] == STATUS_SUCCESS
        assert result2["status"] == STATUS_SUCCESS
        assert result1["metadata"]["event_type"] == "dividends"
        assert result2["metadata"]["event_type"] == "earnings"

    @patch.object(Calendar, "_request")
    def test_parallel_dividends_and_earnings(self, mock_request):
        """Test dividends and earnings can be fetched together."""
        mock_request.return_value = ({"data": []}, None)

        cal = Calendar()

        dividends = cal.get_dividends(markets=["america"])
        earnings = cal.get_earnings(markets=["america"])

        assert dividends["status"] == STATUS_SUCCESS
        assert earnings["status"] == STATUS_SUCCESS


class TestCalendarParameterCombinations:
    """Test Calendar with complex parameter combinations."""

    @patch.object(Calendar, "_request")
    def test_dividends_multiple_markets_with_fields(self, mock_request):
        """Test dividends with multiple markets and custom fields."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        result = cal.get_dividends(
            timestamp_from=1704067200,
            timestamp_to=1735689600,
            markets=["america", "uk", "europe"],
            fields=["name", "description", "dividend_amount_recent", "market"],
            lang="en",
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["markets"] == ["america", "uk", "europe"]
        assert result["metadata"]["timestamp_from"] == 1704067200
        assert result["metadata"]["timestamp_to"] == 1735689600

    @patch.object(Calendar, "_request")
    def test_earnings_multiple_markets_with_fields(self, mock_request):
        """Test earnings with multiple markets and custom fields."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        result = cal.get_earnings(
            timestamp_from=1704067200,
            timestamp_to=1735689600,
            markets=["america", "uk"],
            fields=["name", "earnings_per_share_fq", "revenue_fq", "market"],
            lang="en",
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["markets"] == ["america", "uk"]
        assert result["metadata"]["timestamp_from"] == 1704067200
        assert result["metadata"]["timestamp_to"] == 1735689600

    @patch.object(Calendar, "_request")
    def test_dividends_future_only(self, mock_request):
        """Test fetching only future dividends."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()
        future_ts = 1735689600

        result = cal.get_dividends(
            timestamp_from=future_ts, timestamp_to=future_ts + 86400 * 30
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["timestamp_from"] >= future_ts

    @patch.object(Calendar, "_request")
    def test_earnings_past_only(self, mock_request):
        """Test fetching only past earnings."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()
        past_ts = 1577836800

        result = cal.get_earnings(
            timestamp_from=past_ts, timestamp_to=past_ts + 86400 * 30
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["timestamp_from"] == past_ts


class TestCalendarExportWorkflows:
    """Test Calendar export in various workflows."""

    @patch.object(Calendar, "_request")
    @patch.object(Calendar, "_export")
    def test_export_dividends_to_json(self, mock_export, mock_request):
        """Test exporting dividends to JSON."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar(export="json")

        cal.get_dividends(markets=["america"])

        mock_export.assert_called_once()
        call_kwargs = mock_export.call_args[1]
        assert call_kwargs["data_category"] == "calendar"
        assert call_kwargs["symbol"] == "dividends"

    @patch.object(Calendar, "_request")
    @patch.object(Calendar, "_export")
    def test_export_earnings_to_json(self, mock_export, mock_request):
        """Test exporting earnings to JSON."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar(export="json")

        cal.get_earnings(markets=["america"])

        mock_export.assert_called_once()
        call_kwargs = mock_export.call_args[1]
        assert call_kwargs["data_category"] == "calendar"
        assert call_kwargs["symbol"] == "earnings"

    @patch.object(Calendar, "_request")
    @patch.object(Calendar, "_export")
    def test_export_multiple_calendar_calls(self, mock_export, mock_request):
        """Test multiple calendar calls with export enabled."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar(export="json")

        cal.get_dividends(markets=["america"])
        cal.get_earnings(markets=["america"])
        cal.get_dividends(markets=["uk"])

        assert mock_export.call_count == 3


class TestCalendarDataMapping:
    """Test Calendar data mapping in workflows."""

    @patch.object(Calendar, "_request")
    def test_dividends_data_structure(self, mock_request):
        """Test dividends data has correct structure."""
        scanner_rows = [
            {
                "s": "NASDAQ:AAPL",
                "d": ["Apple Inc", "tech", 0.5, "2024-01-15", 0.24],
            }
        ]
        mock_request.return_value = ({"data": scanner_rows}, None)
        cal = Calendar()

        result = cal.get_dividends(
            fields=["name", "description", "dividends_yield", "market"]
        )

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 1
        item = result["data"][0]
        assert "symbol" in item
        assert "name" in item
        assert "description" in item
        assert "dividends_yield" in item
        assert "market" in item

    @patch.object(Calendar, "_request")
    def test_earnings_data_structure(self, mock_request):
        """Test earnings data has correct structure."""
        scanner_rows = [
            {
                "s": "NASDAQ:AAPL",
                "d": ["Apple Inc", "2024-01-18", 1.5, 120000000],
            }
        ]
        mock_request.return_value = ({"data": scanner_rows}, None)
        cal = Calendar()

        result = cal.get_earnings(
            fields=[
                "name",
                "earnings_release_date",
                "earnings_per_share_fq",
                "revenue_fq",
            ]
        )

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 1
        item = result["data"][0]
        assert "symbol" in item
        assert "name" in item
        assert "earnings_release_date" in item
        assert "earnings_per_share_fq" in item
        assert "revenue_fq" in item

    @patch.object(Calendar, "_request")
    def test_earnings_with_forecast_data(self, mock_request):
        """Test earnings data includes forecast information."""
        scanner_rows = [
            {
                "s": "NASDAQ:AAPL",
                "d": [
                    "2024-01-18",
                    "2024-04-18",
                    "Apple Inc",
                    1.5,
                    1.6,
                    120000000,
                    125000000,
                ],
            }
        ]
        mock_request.return_value = ({"data": scanner_rows}, None)
        cal = Calendar()

        result = cal.get_earnings(
            fields=[
                "earnings_release_date",
                "earnings_release_next_date",
                "name",
                "earnings_per_share_fq",
                "earnings_per_share_forecast_next_fq",
                "revenue_fq",
                "revenue_forecast_next_fq",
            ]
        )

        assert result["status"] == STATUS_SUCCESS
        item = result["data"][0]
        assert "earnings_per_share_fq" in item
        assert "earnings_per_share_forecast_next_fq" in item


class TestCalendarMetadataConsistency:
    """Test Calendar metadata consistency across methods."""

    @patch.object(Calendar, "_request")
    def test_dividends_metadata_complete(self, mock_request):
        """Test dividends metadata is complete."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        result = cal.get_dividends(
            timestamp_from=1704067200,
            timestamp_to=1735689600,
            markets=["america"],
        )

        metadata = result["metadata"]
        assert "event_type" in metadata
        assert "total" in metadata
        assert "timestamp_from" in metadata
        assert "timestamp_to" in metadata
        assert "markets" in metadata
        assert metadata["event_type"] == "dividends"
        assert metadata["timestamp_from"] == 1704067200
        assert metadata["timestamp_to"] == 1735689600
        assert metadata["markets"] == ["america"]

    @patch.object(Calendar, "_request")
    def test_earnings_metadata_complete(self, mock_request):
        """Test earnings metadata is complete."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        result = cal.get_earnings(
            timestamp_from=1704067200,
            timestamp_to=1735689600,
            markets=["america", "uk"],
        )

        metadata = result["metadata"]
        assert "event_type" in metadata
        assert "total" in metadata
        assert "timestamp_from" in metadata
        assert "timestamp_to" in metadata
        assert "markets" in metadata
        assert metadata["event_type"] == "earnings"
        assert metadata["timestamp_from"] == 1704067200
        assert metadata["timestamp_to"] == 1735689600
        assert metadata["markets"] == ["america", "uk"]

    @patch.object(Calendar, "_request")
    def test_metadata_no_markets_when_none_provided(self, mock_request):
        """Test markets not in metadata when not provided."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        result = cal.get_dividends()

        assert "markets" not in result["metadata"]


class TestCalendarErrorPropagation:
    """Test error propagation in workflows."""

    @patch.object(Calendar, "_request")
    def test_field_error_does_not_affect_second_call(self, mock_request):
        """Test field error in first call doesn't affect second call."""
        mock_request.return_value = ({"data": []}, None)
        cal = Calendar()

        result1 = cal.get_dividends(fields=["invalid_field"])
        assert result1["status"] == "failed"

        result2 = cal.get_dividends()
        assert result2["status"] == STATUS_SUCCESS
        mock_request.assert_called()

    @patch.object(Calendar, "_request")
    def test_network_error_preserves_metadata(self, mock_request):
        """Test network error preserves request metadata."""
        mock_request.return_value = (None, "Network error")
        cal = Calendar()

        result = cal.get_dividends(
            timestamp_from=1704067200,
            timestamp_to=1735689600,
            markets=["america"],
        )

        assert result["status"] == "failed"
        assert "event_type" in result["metadata"]

    @patch.object(Calendar, "_request")
    def test_error_response_has_event_type(self, mock_request):
        """Test error responses include event_type in metadata."""
        mock_request.return_value = (None, "Network error")
        cal = Calendar()

        div_result = cal.get_dividends()
        assert div_result["metadata"]["event_type"] == "dividends"

        earn_result = cal.get_earnings()
        assert earn_result["metadata"]["event_type"] == "earnings"
