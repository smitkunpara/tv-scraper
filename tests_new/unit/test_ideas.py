"""Tests for Ideas scraper module."""

from typing import Any, Dict, Iterator, List
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.core.exceptions import NetworkError
from tv_scraper.scrapers.social.ideas import Ideas


def _make_api_response(items: List[Dict[str, Any]]) -> Dict[str, Any]:
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
) -> Dict[str, Any]:
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
    json_data: Dict[str, Any],
    status_code: int = 200,
    text: str = "",
) -> MagicMock:
    """Create a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.json.return_value = json_data
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

    @patch("tv_scraper.scrapers.social.ideas.requests.get")
    def test_scrape_success_popular(self, mock_get: MagicMock, ideas: Ideas) -> None:
        """Scrape popular ideas returns success envelope with mapped fields."""
        mock_get.return_value = _mock_response(
            _make_api_response([_sample_idea(title="Bull Run Coming")])
        )

        result = ideas.scrape(exchange="CRYPTO", symbol="BTCUSD", sort_by="popular")

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

    @patch("tv_scraper.scrapers.social.ideas.requests.get")
    def test_scrape_success_recent(self, mock_get: MagicMock, ideas: Ideas) -> None:
        """Scrape recent ideas passes sort=recent to API and returns data."""
        mock_get.return_value = _mock_response(
            _make_api_response([_sample_idea(title="Latest Analysis")])
        )

        result = ideas.scrape(exchange="CRYPTO", symbol="BTCUSD", sort_by="recent")

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 1
        assert result["data"][0]["title"] == "Latest Analysis"

        # Verify 'sort=recent' was included in the API call params
        call_kwargs = mock_get.call_args
        params = call_kwargs[1].get("params", call_kwargs.kwargs.get("params", {}))
        assert params.get("sort") == "recent"

    @patch("tv_scraper.scrapers.social.ideas.requests.get")
    def test_scrape_multiple_pages(self, mock_get: MagicMock, ideas: Ideas) -> None:
        """Multi-page scrape with ThreadPoolExecutor returns combined results."""
        mock_get.return_value = _mock_response(
            _make_api_response([_sample_idea()])
        )

        result = ideas.scrape(
            exchange="CRYPTO", symbol="BTCUSD",
            start_page=1, end_page=3, sort_by="popular",
        )

        assert result["status"] == STATUS_SUCCESS
        # 3 pages × 1 idea each = 3 ideas
        assert len(result["data"]) == 3
        assert mock_get.call_count == 3
        assert result["metadata"]["pages"] == 3

    @patch("tv_scraper.scrapers.social.ideas.requests.get")
    def test_scrape_no_data(self, mock_get: MagicMock, ideas: Ideas) -> None:
        """Empty items list returns success with empty data list."""
        mock_get.return_value = _mock_response(_make_api_response([]))

        result = ideas.scrape(exchange="CRYPTO", symbol="BTCUSD")

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] == []
        assert result["error"] is None


class TestScrapeErrors:
    """Tests for error handling — returns error responses, never raises."""

    def test_scrape_invalid_sort(self, ideas: Ideas) -> None:
        """Invalid sort_by returns error response without making HTTP calls."""
        result = ideas.scrape(exchange="CRYPTO", symbol="BTCUSD", sort_by="invalid")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "sort_by" in result["error"].lower() or "invalid" in result["error"].lower()

    def test_scrape_empty_symbol(self, ideas: Ideas) -> None:
        """Empty symbol returns error response."""
        result = ideas.scrape(exchange="CRYPTO", symbol="")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    @patch("tv_scraper.scrapers.social.ideas.requests.get")
    def test_scrape_network_error(self, mock_get: MagicMock, ideas: Ideas) -> None:
        """Network/request failure returns error response, does not raise."""
        mock_get.side_effect = Exception("Connection refused")

        result = ideas.scrape(exchange="CRYPTO", symbol="BTCUSD")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    @patch("tv_scraper.scrapers.social.ideas.requests.get")
    def test_scrape_captcha_detected(self, mock_get: MagicMock, ideas: Ideas) -> None:
        """Captcha challenge in response returns error response."""
        captcha_resp = _mock_response(
            _make_api_response([]),
            text="<title>Captcha Challenge</title>",
        )
        mock_get.return_value = captcha_resp

        result = ideas.scrape(exchange="CRYPTO", symbol="BTCUSD")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "captcha" in result["error"].lower()


class TestResponseFormat:
    """Tests for response envelope structure."""

    @patch("tv_scraper.scrapers.social.ideas.requests.get")
    def test_response_has_standard_envelope(
        self, mock_get: MagicMock, ideas: Ideas
    ) -> None:
        """Response contains exactly status/data/metadata/error keys."""
        mock_get.return_value = _mock_response(
            _make_api_response([_sample_idea()])
        )

        result = ideas.scrape(exchange="CRYPTO", symbol="BTCUSD")

        assert set(result.keys()) == {"status", "data", "metadata", "error"}
        assert result["metadata"]["symbol"] == "BTCUSD"
        assert result["metadata"]["exchange"] == "CRYPTO"
        assert "total" in result["metadata"]

    @patch("tv_scraper.scrapers.social.ideas.requests.get")
    def test_snake_case_params(self, mock_get: MagicMock, ideas: Ideas) -> None:
        """Verify snake_case parameter names are accepted."""
        mock_get.return_value = _mock_response(
            _make_api_response([_sample_idea()])
        )

        # These should all be valid snake_case param names (no camelCase)
        result = ideas.scrape(
            exchange="CRYPTO",
            symbol="BTCUSD",
            start_page=1,
            end_page=1,
            sort_by="popular",
        )

        assert result["status"] == STATUS_SUCCESS


class TestCookieHandling:
    """Tests for cookie authentication."""

    @patch("tv_scraper.scrapers.social.ideas.requests.get")
    def test_cookie_header_applied(self, mock_get: MagicMock) -> None:
        """Cookie passed in constructor is sent as request header."""
        cookie_value = "sessionid=abc123; _sp_id=xyz789"
        scraper = Ideas(cookie=cookie_value)
        mock_get.return_value = _mock_response(
            _make_api_response([_sample_idea()])
        )

        scraper.scrape(exchange="CRYPTO", symbol="BTCUSD")

        call_kwargs = mock_get.call_args
        headers = call_kwargs[1].get("headers", call_kwargs.kwargs.get("headers", {}))
        assert headers.get("cookie") == cookie_value

    @patch.dict("os.environ", {"TRADINGVIEW_COOKIE": "env_cookie_value"})
    @patch("tv_scraper.scrapers.social.ideas.requests.get")
    def test_cookie_from_env_var(self, mock_get: MagicMock) -> None:
        """Cookie loaded from TRADINGVIEW_COOKIE env var when not passed directly."""
        scraper = Ideas()
        mock_get.return_value = _mock_response(
            _make_api_response([_sample_idea()])
        )

        scraper.scrape(exchange="CRYPTO", symbol="BTCUSD")

        call_kwargs = mock_get.call_args
        headers = call_kwargs[1].get("headers", call_kwargs.kwargs.get("headers", {}))
        assert headers.get("cookie") == "env_cookie_value"
