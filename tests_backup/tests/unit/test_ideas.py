from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.social.ideas import Ideas


def _make_api_response(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a TradingView ideas JSON API response structure."""
    return {
        "data": {
            "ideas": {
                "data": {
                    "items": items,
                }
            }
        }
    }


def _sample_idea(
    title: str = "Test Idea",
    description: str = "Test Description",
    author: str = "testuser",
    comments: int = 10,
    views: int = 500,
    likes: int = 42,
    timestamp: int = 1700000000,
) -> dict[str, Any]:
    """Build a single idea item as returned by the TradingView API."""
    return {
        "name": title,
        "description": description,
        "symbol": {"logo_urls": ["https://example.com/logo.png"]},
        "chart_url": "https://www.tradingview.com/chart/BTCUSD/abc123",
        "comments_count": comments,
        "views_count": views,
        "user": {"username": author},
        "likes_count": likes,
        "date_timestamp": timestamp,
    }


def _mock_response(
    json_data: dict[str, Any],
    status_code: int = 200,
    text: str = "",
) -> MagicMock:
    """Create a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.json.return_value = json_data
    # Success responses should not raise for status
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(f"Error {status_code}")
    else:
        resp.raise_for_status.return_value = None
    return resp


@pytest.fixture
def ideas() -> Iterator[Ideas]:
    """Create an Ideas instance for testing."""
    yield Ideas()


class TestInheritance:
    """Verify Ideas inherits from BaseScraper."""

    def test_inherits_base_scraper(self) -> None:
        """Ideas must be a subclass of BaseScraper."""
        assert issubclass(Ideas, BaseScraper)


class TestScrapeSuccess:
    """Tests for successful idea scraping."""

    @patch("requests.get")
    def test_get_data_success_popular(self, mock_get: MagicMock, ideas: Ideas) -> None:
        """Scrape popular ideas returns success envelope with mapped fields."""
        mock_get.return_value = _mock_response(
            _make_api_response([_sample_idea(title="Bull Run Coming")])
        )

        result = ideas.get_ideas(exchange="CRYPTO", symbol="BTCUSD", sort_by="popular")

        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None
        assert len(result["data"]) == 1

        idea = result["data"][0]
        assert idea["title"] == "Bull Run Coming"
        assert idea["description"] == "Test Description"
        assert idea["author"] == "testuser"
        assert idea["comments_count"] == 10
        assert idea["views_count"] == 500
        assert idea["likes_count"] == 42
        assert idea["timestamp"] == 1700000000
        assert idea["chart_url"] == "https://www.tradingview.com/chart/BTCUSD/abc123"
        assert idea["preview_image"] == ["https://example.com/logo.png"]

    @patch("requests.get")
    def test_get_data_success_recent(self, mock_get: MagicMock, ideas: Ideas) -> None:
        """Scrape recent ideas passes sort=recent to API and returns data."""
        mock_get.return_value = _mock_response(
            _make_api_response([_sample_idea(title="Latest Analysis")])
        )

        result = ideas.get_ideas(exchange="CRYPTO", symbol="BTCUSD", sort_by="recent")

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 1
        assert result["data"][0]["title"] == "Latest Analysis"

        # Verify 'sort=recent' was included in the API call params
        call_kwargs = mock_get.call_args[1]
        params = call_kwargs.get("params", {})
        assert params.get("sort") == "recent"

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_get_data_multiple_pages(
        self, mock_get: MagicMock, mock_verify: MagicMock, ideas: Ideas
    ) -> None:
        """Multi-page get_data with ThreadPoolExecutor returns combined results."""
        mock_get.return_value = _mock_response(_make_api_response([_sample_idea()]))

        result = ideas.get_ideas(
            exchange="CRYPTO",
            symbol="BTCUSD",
            start_page=1,
            end_page=3,
            sort_by="popular",
        )

        assert result["status"] == STATUS_SUCCESS
        # 3 pages x 1 idea each = 3 ideas
        assert len(result["data"]) == 3
        # Direct requests.get called in concurrent threads
        assert mock_get.call_count == 3
        assert result["metadata"]["pages"] == 3

    @patch("requests.get")
    def test_get_data_no_data(self, mock_get: MagicMock, ideas: Ideas) -> None:
        """Empty items list returns success with empty data list."""
        mock_get.return_value = _mock_response(_make_api_response([]))

        result = ideas.get_ideas(exchange="CRYPTO", symbol="BTCUSD")

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] == []
        assert result["error"] is None


class TestScrapeErrors:
    """Tests for error handling — returns error responses, never raises."""

    def test_get_data_invalid_sort(self, ideas: Ideas) -> None:
        """Invalid sort_by returns error response without making HTTP calls."""
        result = ideas.get_ideas(exchange="CRYPTO", symbol="BTCUSD", sort_by="invalid")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert (
            "sort_by" in result["error"].lower() or "invalid" in result["error"].lower()
        )

    def test_get_data_empty_symbol(self, ideas: Ideas) -> None:
        """Empty symbol returns error response."""
        result = ideas.get_ideas(exchange="CRYPTO", symbol="")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    @patch("requests.get")
    def test_get_data_network_error(self, mock_get: MagicMock, ideas: Ideas) -> None:
        """Network/request failure returns error response, does not raise."""
        mock_get.side_effect = requests.RequestException("Connection refused")

        result = ideas.get_ideas(exchange="CRYPTO", symbol="BTCUSD")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    @patch("requests.get")
    def test_get_data_captcha_detected(self, mock_get: MagicMock, ideas: Ideas) -> None:
        """Captcha challenge in response returns error response."""
        captcha_resp = _mock_response(
            _make_api_response([]),
            text="<title>Captcha Challenge</title>",
        )
        mock_get.return_value = captcha_resp

        result = ideas.get_ideas(exchange="CRYPTO", symbol="BTCUSD")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "captcha" in result["error"].lower()


class TestResponseFormat:
    """Tests for response envelope structure."""

    @patch("requests.get")
    def test_response_has_standard_envelope(
        self, mock_get: MagicMock, ideas: Ideas
    ) -> None:
        """Response contains exactly status/data/metadata/error keys."""
        mock_get.return_value = _mock_response(_make_api_response([_sample_idea()]))

        result = ideas.get_ideas(exchange="CRYPTO", symbol="BTCUSD")

        assert set(result.keys()) == {"status", "data", "metadata", "error"}
        assert result["metadata"]["symbol"] == "BTCUSD"
        assert result["metadata"]["exchange"] == "CRYPTO"
        assert "total" in result["metadata"]

    @patch("requests.get")
    def test_snake_case_params(self, mock_get: MagicMock, ideas: Ideas) -> None:
        """Verify snake_case parameter names are accepted."""
        mock_get.return_value = _mock_response(_make_api_response([_sample_idea()]))

        # These should all be valid snake_case param names (no camelCase)
        result = ideas.get_ideas(
            exchange="CRYPTO",
            symbol="BTCUSD",
            start_page=1,
            end_page=1,
            sort_by="popular",
        )

        assert result["status"] == STATUS_SUCCESS


class TestCookieHandling:
    """Tests for cookie authentication."""

    @patch("requests.get")
    def test_cookie_header_applied(self, mock_get: MagicMock) -> None:
        """Cookie passed in constructor is sent as request header."""
        cookie_value = "sessionid=abc123; _sp_id=xyz789"
        scraper = Ideas(cookie=cookie_value)
        mock_get.return_value = _mock_response(_make_api_response([_sample_idea()]))

        scraper.get_ideas(exchange="CRYPTO", symbol="BTCUSD")

        # Direct requests.get call should have headers with cookie
        call_kwargs = mock_get.call_args[1]
        headers = call_kwargs.get("headers", {})
        assert headers.get("cookie") == cookie_value

    @patch.dict("os.environ", {"TRADINGVIEW_COOKIE": "env_cookie_value"})
    @patch("requests.get")
    def test_cookie_from_env_var(self, mock_get: MagicMock) -> None:
        """Cookie loaded from TRADINGVIEW_COOKIE env var when not passed directly."""
        scraper = Ideas()
        mock_get.return_value = _mock_response(_make_api_response([_sample_idea()]))

        scraper.get_ideas(exchange="CRYPTO", symbol="BTCUSD")

        call_kwargs = mock_get.call_args[1]
        headers = call_kwargs.get("headers", {})
        assert headers.get("cookie") == "env_cookie_value"


class TestPageValidation:
    """Tests for page parameter validation."""

    def test_invalid_start_page_zero(self) -> None:
        """start_page=0 returns error response."""
        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="CRYPTO", symbol="BTCUSD", start_page=0, end_page=1
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "start_page" in result["error"]

    def test_invalid_start_page_negative(self) -> None:
        """Negative start_page returns error response."""
        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="CRYPTO", symbol="BTCUSD", start_page=-1, end_page=1
        )

        assert result["status"] == STATUS_FAILED
        assert "start_page" in result["error"]

    def test_invalid_end_page_less_than_start(self) -> None:
        """end_page < start_page returns error response."""
        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="CRYPTO", symbol="BTCUSD", start_page=5, end_page=3
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert (
            "end_page" in result["error"].lower()
            or "start_page" in result["error"].lower()
        )


class TestPartialFailures:
    """Tests for partial failure handling - data should be preserved."""

    @patch("requests.get")
    def test_partial_failure_preserves_data(
        self, mock_get: MagicMock, ideas: Ideas
    ) -> None:
        """Page failures still return successfully scraped data."""
        mock_get.side_effect = [
            _mock_response(_make_api_response([_sample_idea(title="Success 1")])),
            requests.RequestException("Network error on page 2"),
            _mock_response(_make_api_response([_sample_idea(title="Success 3")])),
        ]

        result = ideas.get_ideas(
            exchange="CRYPTO",
            symbol="BTCUSD",
            start_page=1,
            end_page=3,
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Failed pages" in result["error"]
        assert "Articles collected so far" in result["error"]
        assert "1" in result["error"] or "3" in result["error"]

    @patch("requests.get")
    def test_captcha_on_later_page_preserves_earlier_data(
        self, mock_get: MagicMock, ideas: Ideas
    ) -> None:
        """Captcha on later page still returns earlier page data."""
        mock_get.side_effect = [
            _mock_response(_make_api_response([_sample_idea(title="Page 1")])),
            _mock_response(
                _make_api_response([]),
                text="<title>Captcha Challenge</title>",
            ),
            _mock_response(_make_api_response([_sample_idea(title="Page 3")])),
        ]

        result = ideas.get_ideas(
            exchange="CRYPTO",
            symbol="BTCUSD",
            start_page=1,
            end_page=3,
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "captcha" in result["error"].lower()


class TestMaxWorkers:
    """Tests for max_workers configuration."""

    @patch("requests.get")
    def test_custom_max_workers(self, mock_get: MagicMock) -> None:
        """Custom max_workers value is used."""
        scraper = Ideas(max_workers=5)
        mock_get.return_value = _mock_response(_make_api_response([_sample_idea()]))

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
            return_value=True,
        ):
            result = scraper.get_ideas(
                exchange="CRYPTO",
                symbol="BTCUSD",
                start_page=1,
                end_page=3,
            )

        assert result["status"] == STATUS_SUCCESS
        assert mock_get.call_count == 3

    def test_max_workers_clamped_to_one(self) -> None:
        """max_workers < 1 is clamped to 1."""
        scraper = Ideas(max_workers=0)
        assert scraper._max_workers == 1

        scraper = Ideas(max_workers=-5)
        assert scraper._max_workers == 1
