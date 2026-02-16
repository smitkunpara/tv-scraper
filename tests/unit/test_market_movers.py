"""Unit tests for tv_scraper.scrapers.screening.market_movers.MarketMovers."""

from typing import Any, Dict, Iterator, List
from unittest import mock

import pytest

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.exceptions import NetworkError
from tv_scraper.scrapers.screening.market_movers import MarketMovers


@pytest.fixture
def scraper() -> Iterator[MarketMovers]:
    """Create a MarketMovers instance for testing."""
    yield MarketMovers(export_result=False)


def _mock_scanner_response(
    symbols: List[str],
    fields: List[str],
    values: List[List[Any]],
) -> mock.Mock:
    """Build a mock response matching the TradingView scanner format."""
    data = []
    for sym, vals in zip(symbols, values):
        data.append({"s": sym, "d": vals})
    resp = mock.Mock()
    resp.status_code = 200
    resp.json.return_value = {"data": data, "totalCount": len(data)}
    return resp


# ---------- Inheritance ----------


class TestInheritance:
    def test_inherits_base_scraper(self) -> None:
        """MarketMovers must inherit from BaseScraper."""
        assert issubclass(MarketMovers, BaseScraper)


# ---------- Successful scrapes ----------


class TestScrapeSuccess:
    @mock.patch("tv_scraper.core.base.make_request")
    def test_scrape_success_gainers(
        self, mock_req: mock.Mock, scraper: MarketMovers
    ) -> None:
        """Default category (gainers) returns success envelope with data."""
        fields = MarketMovers.DEFAULT_FIELDS
        mock_req.return_value = _mock_scanner_response(
            symbols=["NASDAQ:AAPL", "NASDAQ:MSFT"],
            fields=fields,
            values=[
                ["Apple Inc.", 190.5, 3.2, 5.1, 80_000_000, 3e12, 30.0, 6.5, "apple", "Tech"],
                ["Microsoft", 410.0, 2.1, 8.0, 40_000_000, 3.1e12, 35.0, 11.0, "msft", "Tech"],
            ],
        )

        result = scraper.scrape(market="stocks-usa", category="gainers")

        assert result["status"] == "success"
        assert result["error"] is None
        assert len(result["data"]) == 2
        assert result["data"][0]["symbol"] == "NASDAQ:AAPL"
        assert result["data"][0]["name"] == "Apple Inc."
        assert result["data"][1]["symbol"] == "NASDAQ:MSFT"

    @mock.patch("tv_scraper.core.base.make_request")
    def test_scrape_success_losers(
        self, mock_req: mock.Mock, scraper: MarketMovers
    ) -> None:
        """Losers category returns properly sorted data."""
        fields = MarketMovers.DEFAULT_FIELDS
        mock_req.return_value = _mock_scanner_response(
            symbols=["NYSE:BAC"],
            fields=fields,
            values=[
                ["Bank of America", 32.0, -4.5, -1.5, 60_000_000, 2.5e11, 10.0, 3.0, "bac", "Finance"],
            ],
        )

        result = scraper.scrape(market="stocks-usa", category="losers")

        assert result["status"] == "success"
        assert len(result["data"]) == 1
        assert result["data"][0]["change"] == -4.5

        # Verify the payload sort order was "asc" for losers
        call_kwargs = mock_req.call_args
        payload = call_kwargs.kwargs.get("json_data") or call_kwargs[1].get("json_data")
        assert payload["sort"]["sortOrder"] == "asc"

    @mock.patch("tv_scraper.core.base.make_request")
    def test_scrape_success_active(
        self, mock_req: mock.Mock, scraper: MarketMovers
    ) -> None:
        """Most-active category sorts by volume desc."""
        fields = MarketMovers.DEFAULT_FIELDS
        mock_req.return_value = _mock_scanner_response(
            symbols=["NASDAQ:TSLA"],
            fields=fields,
            values=[
                ["Tesla", 250.0, 0.5, 1.2, 150_000_000, 8e11, 60.0, 4.0, "tsla", "Auto"],
            ],
        )

        result = scraper.scrape(market="stocks-usa", category="most-active")

        assert result["status"] == "success"

        # Verify sort config
        call_kwargs = mock_req.call_args
        payload = call_kwargs.kwargs.get("json_data") or call_kwargs[1].get("json_data")
        assert payload["sort"]["sortBy"] == "volume"
        assert payload["sort"]["sortOrder"] == "desc"


# ---------- Custom fields and limit ----------


class TestCustomFieldsAndLimit:
    @mock.patch("tv_scraper.core.base.make_request")
    def test_scrape_custom_fields(
        self, mock_req: mock.Mock, scraper: MarketMovers
    ) -> None:
        """Custom fields list is used instead of defaults."""
        custom_fields = ["name", "close", "change"]
        mock_req.return_value = _mock_scanner_response(
            symbols=["NYSE:IBM"],
            fields=custom_fields,
            values=[["IBM Corp", 180.0, 1.1]],
        )

        result = scraper.scrape(
            market="stocks-usa",
            category="gainers",
            fields=custom_fields,
        )

        assert result["status"] == "success"
        assert result["data"][0]["name"] == "IBM Corp"
        # Verify the payload used custom fields
        call_kwargs = mock_req.call_args
        payload = call_kwargs.kwargs.get("json_data") or call_kwargs[1].get("json_data")
        assert payload["columns"] == custom_fields

    @mock.patch("tv_scraper.core.base.make_request")
    def test_scrape_with_limit(
        self, mock_req: mock.Mock, scraper: MarketMovers
    ) -> None:
        """Limit parameter is passed to the scanner payload."""
        mock_req.return_value = _mock_scanner_response(
            symbols=["NASDAQ:GOOG"],
            fields=MarketMovers.DEFAULT_FIELDS,
            values=[
                ["Alphabet", 140.0, 1.5, 2.0, 20_000_000, 1.7e12, 24.0, 5.8, "goog", "Tech"],
            ],
        )

        scraper.scrape(market="stocks-usa", category="gainers", limit=10)

        call_kwargs = mock_req.call_args
        payload = call_kwargs.kwargs.get("json_data") or call_kwargs[1].get("json_data")
        assert payload["range"] == [0, 10]


# ---------- Validation / error responses ----------


class TestValidationErrors:
    def test_scrape_invalid_market(self, scraper: MarketMovers) -> None:
        """Invalid market returns error response without raising."""
        result = scraper.scrape(market="invalid-mkt", category="gainers")

        assert result["status"] == "failed"
        assert result["data"] is None
        assert "invalid-mkt" in result["error"]

    def test_scrape_invalid_category(self, scraper: MarketMovers) -> None:
        """Invalid category for stocks returns error response."""
        result = scraper.scrape(market="stocks-usa", category="bad-cat")

        assert result["status"] == "failed"
        assert result["data"] is None
        assert "bad-cat" in result["error"]


# ---------- Network error ----------


class TestNetworkError:
    @mock.patch("tv_scraper.core.base.make_request")
    def test_scrape_network_error(
        self, mock_req: mock.Mock, scraper: MarketMovers
    ) -> None:
        """Network failure returns error response."""
        mock_req.side_effect = NetworkError("Connection refused")

        result = scraper.scrape(market="stocks-usa", category="gainers")

        assert result["status"] == "failed"
        assert result["data"] is None
        assert "Connection refused" in result["error"]


# ---------- Envelope structure ----------


class TestResponseEnvelope:
    @mock.patch("tv_scraper.core.base.make_request")
    def test_response_has_standard_envelope(
        self, mock_req: mock.Mock, scraper: MarketMovers
    ) -> None:
        """Response has status, data, metadata, error keys."""
        mock_req.return_value = _mock_scanner_response(
            symbols=["NASDAQ:AAPL"],
            fields=MarketMovers.DEFAULT_FIELDS,
            values=[
                ["Apple", 190.0, 3.0, 5.0, 80e6, 3e12, 30.0, 6.5, "apple", "Tech"],
            ],
        )

        result = scraper.scrape()

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["metadata"]["market"] == "stocks-usa"
        assert result["metadata"]["category"] == "gainers"
        assert result["metadata"]["total"] == 1


# ---------- Category determines sort ----------


class TestCategoryDeterminesSort:
    @pytest.mark.parametrize(
        "category,expected_sort_by,expected_order",
        [
            ("gainers", "change", "desc"),
            ("losers", "change", "asc"),
            ("most-active", "volume", "desc"),
            ("penny-stocks", "volume", "desc"),
            ("pre-market-gainers", "change", "desc"),
            ("pre-market-losers", "change", "asc"),
            ("after-hours-gainers", "change", "desc"),
            ("after-hours-losers", "change", "asc"),
        ],
    )
    @mock.patch("tv_scraper.core.base.make_request")
    def test_category_determines_sort(
        self,
        mock_req: mock.Mock,
        scraper: MarketMovers,
        category: str,
        expected_sort_by: str,
        expected_order: str,
    ) -> None:
        """Each category maps to the correct sort configuration."""
        mock_req.return_value = _mock_scanner_response(
            symbols=["NASDAQ:TEST"],
            fields=MarketMovers.DEFAULT_FIELDS,
            values=[
                ["Test", 10.0, 1.0, 0.1, 1000, 1e6, 5.0, 2.0, "test", "Test"],
            ],
        )

        scraper.scrape(market="stocks-usa", category=category)

        call_kwargs = mock_req.call_args
        payload = call_kwargs.kwargs.get("json_data") or call_kwargs[1].get("json_data")
        assert payload["sort"]["sortBy"] == expected_sort_by
        assert payload["sort"]["sortOrder"] == expected_order
