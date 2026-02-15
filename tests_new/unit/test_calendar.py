"""Unit tests for tv_scraper.scrapers.events.calendar.Calendar."""

import datetime
from typing import Any, Dict, Iterator, List
from unittest import mock

import pytest

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.exceptions import NetworkError
from tv_scraper.scrapers.events.calendar import Calendar


# ---- Helpers ----

def _mock_calendar_response(
    symbols: List[str],
    values: List[List[Any]],
) -> mock.Mock:
    """Build a mock response matching the TradingView calendar scanner format."""
    data = []
    for sym, vals in zip(symbols, values):
        data.append({"s": sym, "d": vals})
    resp = mock.Mock()
    resp.status_code = 200
    resp.json.return_value = {"data": data, "totalCount": len(data)}
    return resp


# ---- Fixtures ----

@pytest.fixture
def scraper() -> Iterator[Calendar]:
    """Create a Calendar instance for testing."""
    yield Calendar(export_result=False)


# ---------- Inheritance ----------


class TestInheritance:
    def test_inherits_base_scraper(self) -> None:
        """Calendar must inherit from BaseScraper."""
        assert issubclass(Calendar, BaseScraper)


# ---------- get_dividends ----------


class TestGetDividends:
    @mock.patch("tv_scraper.core.base.make_request")
    def test_get_dividends_success(
        self, mock_req: mock.Mock, scraper: Calendar
    ) -> None:
        """Default call returns success envelope with dividend data."""
        mock_req.return_value = _mock_calendar_response(
            symbols=["NASDAQ:AAPL", "NYSE:KO"],
            values=[
                [1700000000, 1700100000, "apple", "Apple Inc.", "Apple Inc.", 0.55, 1700200000, 1700300000, 0.24, 0.25, "USD", "america"],
                [1700000001, 1700100001, "coca-cola", "Coca-Cola", "Coca-Cola Co", 3.1, 1700200001, 1700300001, 0.46, 0.47, "USD", "america"],
            ],
        )

        result = scraper.get_dividends()

        assert result["status"] == "success"
        assert result["error"] is None
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 2
        assert result["data"][0]["symbol"] == "NASDAQ:AAPL"
        assert result["data"][1]["symbol"] == "NYSE:KO"
        # Fields mapped correctly
        assert result["data"][0]["name"] == "Apple Inc."

    @mock.patch("tv_scraper.core.base.make_request")
    def test_get_dividends_custom_fields(
        self, mock_req: mock.Mock, scraper: Calendar
    ) -> None:
        """Custom fields returns only requested fields in data."""
        fields = ["logoid", "name", "dividends_yield"]
        mock_req.return_value = _mock_calendar_response(
            symbols=["NASDAQ:AAPL"],
            values=[["apple", "Apple Inc.", 0.55]],
        )

        result = scraper.get_dividends(fields=fields)

        assert result["status"] == "success"
        assert len(result["data"]) == 1
        assert result["data"][0]["logoid"] == "apple"
        assert result["data"][0]["name"] == "Apple Inc."
        assert result["data"][0]["dividends_yield"] == 0.55

    @mock.patch("tv_scraper.core.base.make_request")
    def test_get_dividends_custom_markets(
        self, mock_req: mock.Mock, scraper: Calendar
    ) -> None:
        """Markets parameter is included in the API payload."""
        mock_req.return_value = _mock_calendar_response(
            symbols=["LSE:SHEL"],
            values=[[1700000000, None, "shell", "Shell", "Shell plc", 3.8, None, None, 0.30, None, "GBP", "uk"]],
        )

        result = scraper.get_dividends(markets=["uk"])

        assert result["status"] == "success"
        # Verify markets was passed in the payload
        call_kwargs = mock_req.call_args
        payload = call_kwargs.kwargs.get("json_data") or call_kwargs[1].get("json_data")
        assert "markets" in payload
        assert payload["markets"] == ["uk"]

    @mock.patch("tv_scraper.core.base.make_request")
    def test_get_dividends_custom_timestamps(
        self, mock_req: mock.Mock, scraper: Calendar
    ) -> None:
        """Custom timestamps are used in the filter payload."""
        mock_req.return_value = _mock_calendar_response(symbols=[], values=[])

        ts_from = 1700000000
        ts_to = 1700600000
        result = scraper.get_dividends(timestamp_from=ts_from, timestamp_to=ts_to)

        assert result["status"] == "success"
        call_kwargs = mock_req.call_args
        payload = call_kwargs.kwargs.get("json_data") or call_kwargs[1].get("json_data")
        filter_right = payload["filter"][0]["right"]
        assert filter_right == [ts_from, ts_to]

    def test_get_dividends_invalid_fields(self, scraper: Calendar) -> None:
        """Invalid fields returns error response."""
        result = scraper.get_dividends(fields=["nonexistent_field"])

        assert result["status"] == "failed"
        assert result["data"] is None
        assert "Invalid" in result["error"]

    @mock.patch("tv_scraper.core.base.make_request")
    def test_get_dividends_network_error(
        self, mock_req: mock.Mock, scraper: Calendar
    ) -> None:
        """Network errors produce error response, never raise."""
        mock_req.side_effect = NetworkError("Connection refused")

        result = scraper.get_dividends()

        assert result["status"] == "failed"
        assert result["data"] is None
        assert "Connection refused" in result["error"]


# ---------- get_earnings ----------


class TestGetEarnings:
    @mock.patch("tv_scraper.core.base.make_request")
    def test_get_earnings_success(
        self, mock_req: mock.Mock, scraper: Calendar
    ) -> None:
        """Default call returns success envelope with earnings data."""
        mock_req.return_value = _mock_calendar_response(
            symbols=["NASDAQ:AAPL"],
            values=[
                [1700000000, 1700100000, "apple", "Apple Inc.", "Apple Inc.",
                 1.46, 1.50, 0.05, 3.5, 90_000_000_000, 95_000_000_000,
                 3_000_000_000_000, 0, 1, 1.45, 89_000_000_000,
                 "USD", "america", 0, 1, 1_000_000_000, 1.2],
            ],
        )

        result = scraper.get_earnings()

        assert result["status"] == "success"
        assert result["error"] is None
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 1
        assert result["data"][0]["symbol"] == "NASDAQ:AAPL"
        assert result["data"][0]["name"] == "Apple Inc."

    @mock.patch("tv_scraper.core.base.make_request")
    def test_get_earnings_custom_fields(
        self, mock_req: mock.Mock, scraper: Calendar
    ) -> None:
        """Custom fields returns only requested fields."""
        fields = ["logoid", "name", "earnings_per_share_fq"]
        mock_req.return_value = _mock_calendar_response(
            symbols=["NASDAQ:MSFT"],
            values=[["microsoft", "Microsoft", 2.93]],
        )

        result = scraper.get_earnings(fields=fields)

        assert result["status"] == "success"
        assert result["data"][0]["logoid"] == "microsoft"
        assert result["data"][0]["earnings_per_share_fq"] == 2.93

    @mock.patch("tv_scraper.core.base.make_request")
    def test_get_earnings_network_error(
        self, mock_req: mock.Mock, scraper: Calendar
    ) -> None:
        """Network errors produce error response, never raise."""
        mock_req.side_effect = NetworkError("Timeout")

        result = scraper.get_earnings()

        assert result["status"] == "failed"
        assert result["data"] is None
        assert "Timeout" in result["error"]


# ---------- Response envelope ----------


class TestResponseEnvelope:
    @mock.patch("tv_scraper.core.base.make_request")
    def test_response_has_standard_envelope(
        self, mock_req: mock.Mock, scraper: Calendar
    ) -> None:
        """All responses must have status, data, metadata, error keys."""
        mock_req.return_value = _mock_calendar_response(
            symbols=["NASDAQ:AAPL"],
            values=[[1700000000, None, "apple", "Apple", "Apple Inc.", 0.55, None, None, 0.24, None, "USD", "america"]],
        )

        result = scraper.get_dividends()

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result


# ---------- Default timestamp range ----------


class TestDefaultTimestampRange:
    @mock.patch("tv_scraper.core.base.make_request")
    def test_default_timestamp_range(
        self, mock_req: mock.Mock, scraper: Calendar
    ) -> None:
        """Default timestamps should be ±3 days from now (midnight-aligned)."""
        mock_req.return_value = _mock_calendar_response(symbols=[], values=[])

        scraper.get_dividends()

        call_kwargs = mock_req.call_args
        payload = call_kwargs.kwargs.get("json_data") or call_kwargs[1].get("json_data")
        ts_from = payload["filter"][0]["right"][0]
        ts_to = payload["filter"][0]["right"][1]

        now = datetime.datetime.now().timestamp()
        midnight = now - (now % 86400)

        expected_from = int(midnight - 3 * 86400)
        expected_to = int(midnight + 3 * 86400 + 86399)

        # Allow 1-second tolerance for execution time
        assert abs(ts_from - expected_from) <= 1
        assert abs(ts_to - expected_to) <= 1
