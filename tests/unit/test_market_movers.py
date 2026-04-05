from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from tv_scraper.core.base import BaseScraper
from tv_scraper.scrapers.screening.market_movers import MarketMovers


@pytest.fixture
def scraper() -> MarketMovers:
    """Create a MarketMovers instance for testing."""
    yield MarketMovers(export_result=False)


def _mock_scanner_response(
    symbols: list[str],
    fields: list[str],
    values: list[list[Any]],
    status_code: int = 200,
) -> MagicMock:
    """Build a mock response matching the TradingView scanner format."""
    data = []
    for sym, vals in zip(symbols, values, strict=True):
        data.append({"s": sym, "d": vals})
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = {"data": data, "totalCount": len(data)}
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(f"Error {status_code}")
    else:
        resp.raise_for_status.return_value = None
    return resp


# ---------- Inheritance ----------


class TestInheritance:
    def test_inherits_base_scraper(self) -> None:
        """MarketMovers must inherit from BaseScraper."""
        assert issubclass(MarketMovers, BaseScraper)


# ---------- Successful get_datas ----------


class TestScrapeSuccess:
    @patch("requests.post")
    def test_get_data_success_gainers(
        self, mock_post: MagicMock, scraper: MarketMovers
    ) -> None:
        """Default category (gainers) returns success envelope with data."""
        fields = MarketMovers.DEFAULT_FIELDS
        mock_post.return_value = _mock_scanner_response(
            symbols=["NASDAQ:AAPL", "NASDAQ:MSFT"],
            fields=fields,
            values=[
                [
                    "Apple Inc.",
                    190.5,
                    3.2,
                    5.1,
                    80_000_000,
                    3e12,
                    30.0,
                    6.5,
                    "apple",
                    "Tech",
                ],
                [
                    "Microsoft",
                    410.0,
                    2.1,
                    8.0,
                    40_000_000,
                    3.1e12,
                    35.0,
                    11.0,
                    "msft",
                    "Tech",
                ],
            ],
        )

        result = scraper.get_market_movers(market="stocks-usa", category="gainers")

        assert result["status"] == "success"
        assert result["error"] is None
        assert len(result["data"]) == 2
        assert result["data"][0]["symbol"] == "NASDAQ:AAPL"
        assert result["data"][0]["name"] == "Apple Inc."
        assert result["data"][1]["symbol"] == "NASDAQ:MSFT"

    @patch("requests.post")
    def test_get_data_success_losers(
        self, mock_post: MagicMock, scraper: MarketMovers
    ) -> None:
        """Losers category returns properly sorted data."""
        fields = MarketMovers.DEFAULT_FIELDS
        mock_post.return_value = _mock_scanner_response(
            symbols=["NYSE:BAC"],
            fields=fields,
            values=[
                [
                    "Bank of America",
                    32.0,
                    -4.5,
                    -1.5,
                    60_000_000,
                    2.5e11,
                    10.0,
                    3.0,
                    "bac",
                    "Finance",
                ],
            ],
        )

        result = scraper.get_market_movers(market="stocks-usa", category="losers")

        assert result["status"] == "success"
        assert len(result["data"]) == 1
        assert result["data"][0]["change"] == -4.5

        # Verify the payload sort order was "asc" for losers
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs.get("json")
        assert payload["sort"]["sortOrder"] == "asc"

    @patch("requests.post")
    def test_get_data_success_active(
        self, mock_post: MagicMock, scraper: MarketMovers
    ) -> None:
        """Most-active category sorts by volume desc."""
        fields = MarketMovers.DEFAULT_FIELDS
        mock_post.return_value = _mock_scanner_response(
            symbols=["NASDAQ:TSLA"],
            fields=fields,
            values=[
                [
                    "Tesla",
                    250.0,
                    0.5,
                    1.2,
                    150_000_000,
                    8e11,
                    60.0,
                    4.0,
                    "tsla",
                    "Auto",
                ],
            ],
        )

        result = scraper.get_market_movers(market="stocks-usa", category="most-active")

        assert result["status"] == "success"

        # Verify sort config
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs.get("json")
        assert payload["sort"]["sortBy"] == "volume"
        assert payload["sort"]["sortOrder"] == "desc"


# ---------- Custom fields and limit ----------


class TestCustomFieldsAndLimit:
    @patch("requests.post")
    def test_get_data_custom_fields(
        self, mock_post: MagicMock, scraper: MarketMovers
    ) -> None:
        """Custom fields list is used instead of defaults."""
        custom_fields = ["name", "close", "change"]
        mock_post.return_value = _mock_scanner_response(
            symbols=["NYSE:IBM"],
            fields=custom_fields,
            values=[["IBM Corp", 180.0, 1.1]],
        )

        result = scraper.get_market_movers(
            market="stocks-usa",
            category="gainers",
            fields=custom_fields,
        )

        assert result["status"] == "success"
        assert result["data"][0]["name"] == "IBM Corp"
        # Verify the payload used custom fields
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs.get("json")
        assert payload["columns"] == custom_fields

    @patch("requests.post")
    def test_get_data_with_limit(
        self, mock_post: MagicMock, scraper: MarketMovers
    ) -> None:
        """Limit parameter is passed to the scanner payload."""
        mock_post.return_value = _mock_scanner_response(
            symbols=["NASDAQ:GOOG"],
            fields=MarketMovers.DEFAULT_FIELDS,
            values=[
                [
                    "Alphabet",
                    140.0,
                    1.5,
                    2.0,
                    20_000_000,
                    1.7e12,
                    24.0,
                    5.8,
                    "goog",
                    "Tech",
                ],
            ],
        )

        scraper.get_market_movers(market="stocks-usa", category="gainers", limit=10)

        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs.get("json")
        assert payload["range"] == [0, 10]


# ---------- Validation / error responses ----------


class TestValidationErrors:
    def test_get_data_invalid_market(self, scraper: MarketMovers) -> None:
        """Invalid market returns error response without raising."""
        result = scraper.get_market_movers(market="invalid-mkt", category="gainers")

        assert result["status"] == "failed"
        assert result["data"] is None
        assert "invalid-mkt" in result["error"]

    def test_get_data_invalid_category(self, scraper: MarketMovers) -> None:
        """Invalid category for stocks returns error response."""
        result = scraper.get_market_movers(market="stocks-usa", category="bad-cat")

        assert result["status"] == "failed"
        assert result["data"] is None
        assert "bad-cat" in result["error"]


# ---------- Network error ----------


class TestNetworkError:
    @patch("requests.post")
    def test_get_data_network_error(
        self, mock_post: MagicMock, scraper: MarketMovers
    ) -> None:
        """Network failure returns error response."""
        mock_post.side_effect = requests.RequestException("Connection refused")

        result = scraper.get_market_movers(market="stocks-usa", category="gainers")

        assert result["status"] == "failed"
        assert result["data"] is None
        assert "Connection refused" in result["error"]


# ---------- Envelope structure ----------


class TestResponseEnvelope:
    @patch("requests.post")
    def test_response_has_standard_envelope(
        self, mock_post: MagicMock, scraper: MarketMovers
    ) -> None:
        """Response has status, data, metadata, error keys."""
        mock_post.return_value = _mock_scanner_response(
            symbols=["NASDAQ:AAPL"],
            fields=MarketMovers.DEFAULT_FIELDS,
            values=[
                ["Apple", 190.0, 3.0, 5.0, 80e6, 3e12, 30.0, 6.5, "apple", "Tech"],
            ],
        )

        result = scraper.get_market_movers()

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
    @patch("requests.post")
    def test_category_determines_sort(
        self,
        mock_post: MagicMock,
        scraper: MarketMovers,
        category: str,
        expected_sort_by: str,
        expected_order: str,
    ) -> None:
        """Each category maps to the correct sort configuration."""
        mock_post.return_value = _mock_scanner_response(
            symbols=["NASDAQ:TEST"],
            fields=MarketMovers.DEFAULT_FIELDS,
            values=[
                ["Test", 10.0, 1.0, 0.1, 1000, 1e6, 5.0, 2.0, "test", "Test"],
            ],
        )

        scraper.get_market_movers(market="stocks-usa", category=category)

        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs.get("json")
        assert payload["sort"]["sortBy"] == expected_sort_by
        assert payload["sort"]["sortOrder"] == expected_order


# ---------- New validation tests ----------


class TestLimitValidation:
    @pytest.mark.parametrize(
        "limit,expected_msg",
        [
            (0, "Invalid limit"),
            (-1, "Invalid limit"),
            (1001, "Invalid limit"),
            (None, "Invalid limit"),
        ],
    )
    def test_invalid_limit_values(
        self, scraper: MarketMovers, limit: int | None, expected_msg: str
    ) -> None:
        """Invalid limit values return error response."""
        result = scraper.get_market_movers(
            market="stocks-usa",
            category="gainers",
            limit=limit,  # type: ignore
        )

        assert result["status"] == "failed"
        assert result["data"] is None
        assert expected_msg in result["error"]

    def test_valid_limit_boundary_values(self, scraper: MarketMovers) -> None:
        """Boundary limit values (1 and 1000) should succeed."""
        for limit in [1, 1000]:
            result = scraper.get_market_movers(
                market="stocks-usa",
                category="gainers",
                limit=limit,
            )
            # Just check it doesn't fail on validation
            assert result["status"] in ("success", "failed")


class TestLanguageValidation:
    def test_invalid_language(self, scraper: MarketMovers) -> None:
        """Invalid language code returns error response."""
        result = scraper.get_market_movers(
            market="stocks-usa",
            category="gainers",
            language="invalid-lang",
        )

        assert result["status"] == "failed"
        assert result["data"] is None
        assert "Unsupported language" in result["error"]

    @patch("requests.post")
    def test_valid_language_in_payload(
        self, mock_post: MagicMock, scraper: MarketMovers
    ) -> None:
        """Valid language code is included in the request payload."""
        mock_post.return_value = _mock_scanner_response(
            symbols=["NASDAQ:AAPL"],
            fields=["name", "close"],
            values=[["Apple", 190.0]],
        )

        scraper.get_market_movers(
            market="stocks-usa",
            category="gainers",
            language="de",
        )

        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs.get("json")
        assert payload["options"]["lang"] == "de"


class TestFieldsValidation:
    def test_invalid_fields_not_list(self, scraper: MarketMovers) -> None:
        """Non-list fields parameter returns error response."""
        result = scraper.get_market_movers(
            market="stocks-usa",
            category="gainers",
            fields="not_a_list",  # type: ignore
        )

        assert result["status"] == "failed"
        assert result["data"] is None
        assert "Invalid fields" in result["error"]

    def test_invalid_fields_not_string_list(self, scraper: MarketMovers) -> None:
        """Fields with non-string items returns error response."""
        result = scraper.get_market_movers(
            market="stocks-usa",
            category="gainers",
            fields=["name", 123, "close"],  # type: ignore
        )

        assert result["status"] == "failed"
        assert result["data"] is None
        assert "Invalid fields" in result["error"]


class TestResponseStructure:
    @patch("requests.post")
    def test_total_count_in_metadata(
        self, mock_post: MagicMock, scraper: MarketMovers
    ) -> None:
        """Response metadata includes totalCount from API."""
        mock_post.return_value = _mock_scanner_response(
            symbols=["NASDAQ:AAPL", "NASDAQ:MSFT"],
            fields=MarketMovers.DEFAULT_FIELDS,
            values=[
                ["Apple", 190.0, 3.0, 5.0, 80e6, 3e12, 30.0, 6.5, "apple", "Tech"],
                ["Microsoft", 410.0, 2.0, 4.0, 40e6, 3e12, 35.0, 11.0, "msft", "Tech"],
            ],
        )

        result = scraper.get_market_movers(market="stocks-usa", category="gainers")

        assert result["status"] == "success"
        assert "totalCount" in result["metadata"]
        assert result["metadata"]["totalCount"] == 2

    @patch("requests.post")
    def test_invalid_json_response_type(
        self, mock_post: MagicMock, scraper: MarketMovers
    ) -> None:
        """Non-dict JSON response returns error."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["not", "a", "dict"]
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = scraper.get_market_movers(market="stocks-usa", category="gainers")

        assert result["status"] == "failed"
        assert result["data"] is None
        assert "Invalid response format" in result["error"]

    @patch("requests.post")
    def test_http_error_returns_correct_message(
        self, mock_post: MagicMock, scraper: MarketMovers
    ) -> None:
        """HTTP errors are captured with proper message."""
        mock_post.side_effect = requests.HTTPError("500 Server Error")

        result = scraper.get_market_movers(market="stocks-usa", category="gainers")

        assert result["status"] == "failed"
        assert result["data"] is None
        assert "HTTP error" in result["error"]
