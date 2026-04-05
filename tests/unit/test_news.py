from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.social.news import News

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sample_headline(
    headline_id: str = "h123",
    title: str = "Bitcoin Hits New High",
    short_description: str = "Bitcoin reached an all-time high today.",
    published: int = 1678900000,
    story_path: str = "/news/story/h123",
) -> dict[str, Any]:
    """Build a headline item as returned by the TradingView news API."""
    return {
        "id": headline_id,
        "title": title,
        "shortDescription": short_description,
        "published": published,
        "storyPath": story_path,
        "urgency": 2,
        "provider": "cointelegraph",
        "relatedSymbols": [],
        "permission": "headline",
        "sourceLogoid": "logo123",
    }


def _sample_cleaned_headline(
    title: str = "Bitcoin Hits New High",
    short_description: str = "Bitcoin reached an all-time high today.",
    published: int = 1678900000,
    story_path: str = "/news/story/h123",
) -> dict[str, Any]:
    """Build a cleaned headline (after filtering)."""
    return {
        "title": title,
        "shortDescription": short_description,
        "published": published,
        "storyPath": story_path,
    }


def _make_headlines_response(
    items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a TradingView news headlines API response."""
    if items is None:
        items = [_sample_headline()]
    return {"items": items}


def _mock_response(
    json_data: dict[str, Any] | None = None,
    text: str = "",
    status_code: int = 200,
) -> MagicMock:
    """Create a mock ``requests.Response``."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    if json_data is not None:
        resp.json.return_value = json_data

    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(f"Error {status_code}")
    else:
        resp.raise_for_status.return_value = None

    return resp


_STORY_JSON = {
    "title": "Bitcoin Hits New High",
    "short_description": "Bitcoin reached new highs today.",
    "ast_description": {
        "type": "root",
        "children": [
            {
                "type": "p",
                "children": ["Bitcoin surged to a new all-time high today."],
            },
            {
                "type": "p",
                "children": [
                    "The price reached ",
                    {
                        "type": "symbol",
                        "params": {"symbol": "BTCUSD", "text": "BTCUSD"},
                    },
                    " levels.",
                ],
            },
            {
                "type": "p",
                "children": ["Market analysts are optimistic."],
            },
        ],
    },
    "published": 1643097623,
    "story_path": "/news/story/h123",
    "id": "tag:reuters.com,2026:newsml_L4N3Z9104:0",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def news() -> Iterator[News]:
    """Create a News instance for testing."""
    yield News()


# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------


class TestInheritance:
    """Verify News inherits from BaseScraper."""

    def test_inherits_base_scraper(self) -> None:
        """News must be a subclass of BaseScraper."""
        assert issubclass(News, BaseScraper)


# ---------------------------------------------------------------------------
# scrape_headlines — success
# ---------------------------------------------------------------------------


class TestScrapeHeadlinesSuccess:
    """Tests for successful headline scraping."""

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_scrape_headlines_success(
        self, mock_get: MagicMock, mock_verify: MagicMock, news: News
    ) -> None:
        """Standard headline retrieval returns success envelope."""
        mock_get.return_value = _mock_response(
            json_data=_make_headlines_response([_sample_headline()]),
        )

        result = news.get_news_headlines(exchange="BINANCE", symbol="BTCUSD")

        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 1

        item = result["data"][0]
        assert item["id"] == "h123"
        assert item["title"] == "Bitcoin Hits New High"
        assert item["shortDescription"] == "Bitcoin reached an all-time high today."
        assert item["published"] == 1678900000
        assert item["storyPath"] == "/news/story/h123"
        assert "provider" not in item
        assert "urgency" not in item
        assert "relatedSymbols" not in item
        assert "permission" not in item
        assert "sourceLogoid" not in item

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_scrape_headlines_with_provider(
        self, mock_get: MagicMock, mock_verify: MagicMock, news: News
    ) -> None:
        """Provider filter is passed through to the API via params."""
        mock_get.return_value = _mock_response(
            json_data=_make_headlines_response([_sample_headline()]),
        )

        result = news.get_news_headlines(
            exchange="BINANCE",
            symbol="BTCUSD",
            provider="cointelegraph",
        )

        assert result["status"] == STATUS_SUCCESS
        call_kwargs = mock_get.call_args[1]
        params = call_kwargs.get("params", {})
        assert params.get("provider") == "cointelegraph"

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_scrape_headlines_with_area(
        self, mock_get: MagicMock, mock_verify: MagicMock, news: News
    ) -> None:
        """Area filter is converted to area code and passed through via params."""
        mock_get.return_value = _mock_response(
            json_data=_make_headlines_response([_sample_headline()]),
        )

        result = news.get_news_headlines(
            exchange="BINANCE",
            symbol="BTCUSD",
            area="americas",
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["area"] == "americas"
        call_kwargs = mock_get.call_args[1]
        params = call_kwargs.get("params", {})
        assert params.get("area") == "AME"

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_scrape_headlines_with_language(
        self, mock_get: MagicMock, mock_verify: MagicMock, news: News
    ) -> None:
        """Language filter is passed through to the API via params."""
        mock_get.return_value = _mock_response(
            json_data=_make_headlines_response([_sample_headline()]),
        )

        result = news.get_news_headlines(
            exchange="BINANCE",
            symbol="BTCUSD",
            language="fr",
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["language"] == "fr"
        call_kwargs = mock_get.call_args[1]
        params = call_kwargs.get("params", {})
        assert params.get("lang") == "fr"

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_scrape_headlines_empty_result(
        self, mock_get: MagicMock, mock_verify: MagicMock, news: News
    ) -> None:
        """No headlines returns success with empty list."""
        mock_get.return_value = _mock_response(
            json_data=_make_headlines_response([]),
        )

        result = news.get_news_headlines(exchange="BINANCE", symbol="BTCUSD")

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] == []
        assert result["error"] is None


# ---------------------------------------------------------------------------
# scrape_headlines — validation errors
# ---------------------------------------------------------------------------


class TestScrapeHeadlinesValidation:
    """Validation failures return error responses — never raise."""

    def test_scrape_headlines_invalid_exchange(self, news: News) -> None:
        """Invalid exchange returns error response."""
        result = news.get_news_headlines(exchange="FAKEXCHANGE", symbol="BTCUSD")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None
        assert (
            "exchange" in result["error"].lower()
            or "invalid" in result["error"].lower()
        )

    def test_scrape_headlines_empty_symbol(self, news: News) -> None:
        """Empty symbol returns error response."""
        result = news.get_news_headlines(exchange="BINANCE", symbol="")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    def test_scrape_headlines_invalid_sort(self, news: News) -> None:
        """Invalid sort_by value returns error response."""
        result = news.get_news_headlines(
            exchange="BINANCE",
            symbol="BTCUSD",
            sort_by="invalid_sort",
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "sort" in result["error"].lower() or "invalid" in result["error"].lower()

    def test_scrape_headlines_invalid_section(self, news: News) -> None:
        """Invalid section value returns error response."""
        result = news.get_news_headlines(
            exchange="BINANCE",
            symbol="BTCUSD",
            section="invalid_section",
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert (
            "section" in result["error"].lower() or "invalid" in result["error"].lower()
        )


# ---------------------------------------------------------------------------
# scrape_headlines — runtime errors
# ---------------------------------------------------------------------------


class TestScrapeHeadlinesErrors:
    """Runtime errors return error responses."""

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_scrape_headlines_network_error(
        self, mock_get: MagicMock, mock_verify: MagicMock, news: News
    ) -> None:
        """Network failure returns error response, does not raise."""
        mock_get.side_effect = requests.RequestException("Connection refused")

        result = news.get_news_headlines(exchange="BINANCE", symbol="BTCUSD")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_scrape_headlines_captcha(
        self, mock_get: MagicMock, mock_verify: MagicMock, news: News
    ) -> None:
        """Captcha challenge returns error response."""
        mock_get.return_value = _mock_response(
            text="<title>Captcha Challenge</title>",
        )

        result = news.get_news_headlines(exchange="BINANCE", symbol="BTCUSD")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "captcha" in result["error"].lower()

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_scrape_headlines_timeout(
        self, mock_get: MagicMock, mock_verify: MagicMock, news: News
    ) -> None:
        """Timeout returns error response."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        result = news.get_news_headlines(exchange="BINANCE", symbol="BTCUSD")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None
        assert "timeout" in result["error"].lower()

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_scrape_headlines_connection_error(
        self, mock_get: MagicMock, mock_verify: MagicMock, news: News
    ) -> None:
        """Connection error returns error response."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        result = news.get_news_headlines(exchange="BINANCE", symbol="BTCUSD")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None
        assert "connection" in result["error"].lower()

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_scrape_headlines_http_error(
        self, mock_get: MagicMock, mock_verify: MagicMock, news: News
    ) -> None:
        """HTTP error returns error response."""
        mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")

        result = news.get_news_headlines(exchange="BINANCE", symbol="BTCUSD")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None
        assert "http" in result["error"].lower()

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_scrape_headlines_invalid_json(
        self, mock_get: MagicMock, mock_verify: MagicMock, news: News
    ) -> None:
        """Invalid JSON response returns error response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status.return_value = None
        mock_resp.text = "not valid json"
        mock_resp.json.side_effect = ValueError("Expecting value")
        mock_get.return_value = mock_resp

        result = news.get_news_headlines(exchange="BINANCE", symbol="BTCUSD")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None
        assert "json" in result["error"].lower()


# ---------------------------------------------------------------------------
# scrape_content — success
# ---------------------------------------------------------------------------


class TestScrapeContentSuccess:
    """Tests for article content scraping using JSON API."""

    @patch("requests.get")
    def test_scrape_content_success(self, mock_get: MagicMock, news: News) -> None:
        """Successfully parse article JSON into structured content."""
        mock_get.return_value = _mock_response(json_data=_STORY_JSON)

        result = news.get_news_content(
            story_id="tag:reuters.com,2026:newsml_L4N3Z9104:0"
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None

        data = result["data"]
        assert data["title"] == "Bitcoin Hits New High"
        assert data["published"] == 1643097623
        assert data["storyPath"] == "/news/story/h123"
        assert data["id"] == "tag:reuters.com,2026:newsml_L4N3Z9104:0"

        description = data["description"]
        assert "Bitcoin surged to a new all-time high today." in description
        assert "BTCUSD" in description
        assert "Market analysts are optimistic." in description
        assert "\n" in description

    @patch("requests.get")
    def test_scrape_content_story_path_without_slash(
        self, mock_get: MagicMock, news: News
    ) -> None:
        """Story path without leading slash should be fixed."""
        story_json = _STORY_JSON.copy()
        story_json["story_path"] = "news/story/h123"

        mock_get.return_value = _mock_response(json_data=story_json)

        result = news.get_news_content(
            story_id="tag:reuters.com,2026:newsml_L4N3Z9104:0"
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"]["storyPath"] == "/news/story/h123"


# ---------------------------------------------------------------------------
# scrape_content — validation errors
# ---------------------------------------------------------------------------


class TestScrapeContentValidation:
    """Validation errors for content scraping."""

    def test_scrape_content_empty_story_id(self, news: News) -> None:
        """Empty story_id returns error response."""
        result = news.get_news_content(story_id="")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "empty" in result["error"].lower()

    def test_scrape_content_whitespace_story_id(self, news: News) -> None:
        """Whitespace-only story_id returns error response."""
        result = news.get_news_content(story_id="   ")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "empty" in result["error"].lower()

    def test_scrape_content_invalid_language(self, news: News) -> None:
        """Invalid language returns error response."""
        result = news.get_news_content(
            story_id="tag:reuters.com,2026:newsml_L4N3Z9104:0",
            language="invalid_lang",
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "language" in result["error"].lower()


# ---------------------------------------------------------------------------
# scrape_content — runtime errors
# ---------------------------------------------------------------------------


class TestScrapeContentErrors:
    """Error handling for content scraping."""

    @patch("requests.get")
    def test_scrape_content_network_error(
        self, mock_get: MagicMock, news: News
    ) -> None:
        """Network failure returns error response."""
        mock_get.side_effect = requests.RequestException("Connection refused")

        result = news.get_news_content(
            story_id="tag:reuters.com,2026:newsml_L4N3Z9104:0"
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    @patch("requests.get")
    def test_scrape_content_timeout(self, mock_get: MagicMock, news: News) -> None:
        """Timeout returns error response."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        result = news.get_news_content(
            story_id="tag:reuters.com,2026:newsml_L4N3Z9104:0"
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "timeout" in result["error"].lower()

    @patch("requests.get")
    def test_scrape_content_connection_error(
        self, mock_get: MagicMock, news: News
    ) -> None:
        """Connection error returns error response."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        result = news.get_news_content(
            story_id="tag:reuters.com,2026:newsml_L4N3Z9104:0"
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "connection" in result["error"].lower()

    @patch("requests.get")
    def test_scrape_content_http_error(self, mock_get: MagicMock, news: News) -> None:
        """HTTP error returns error response."""
        mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")

        result = news.get_news_content(
            story_id="tag:reuters.com,2026:newsml_L4N3Z9104:0"
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "http" in result["error"].lower()

    @patch("requests.get")
    def test_scrape_content_invalid_json(self, mock_get: MagicMock, news: News) -> None:
        """Invalid JSON response returns error response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status.return_value = None
        mock_resp.text = "not valid json"
        mock_resp.json.side_effect = ValueError("Expecting value")
        mock_get.return_value = mock_resp

        result = news.get_news_content(
            story_id="tag:reuters.com,2026:newsml_L4N3Z9104:0"
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "json" in result["error"].lower()


# ---------------------------------------------------------------------------
# Response format
# ---------------------------------------------------------------------------


class TestResponseFormat:
    """Verify the standardized response envelope."""

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_response_has_standard_envelope(
        self, mock_get: MagicMock, mock_verify: MagicMock, news: News
    ) -> None:
        """Response contains exactly status/data/metadata/error keys."""
        mock_get.return_value = _mock_response(
            json_data=_make_headlines_response([_sample_headline()]),
        )

        result = news.get_news_headlines(exchange="BINANCE", symbol="BTCUSD")

        assert set(result.keys()) == {"status", "data", "metadata", "error"}


# ---------------------------------------------------------------------------
# Helper method tests
# ---------------------------------------------------------------------------


class TestHelperMethods:
    """Tests for internal helper methods."""

    def test_normalize_story_path_with_slash(self, news: News) -> None:
        """Story path with leading slash stays unchanged."""
        result = news._normalize_story_path("/news/story/123")
        assert result == "/news/story/123"

    def test_normalize_story_path_without_slash(self, news: News) -> None:
        """Story path without leading slash gets one added."""
        result = news._normalize_story_path("news/story/123")
        assert result == "/news/story/123"

    def test_normalize_story_path_empty(self, news: News) -> None:
        """Empty story path stays empty."""
        result = news._normalize_story_path("")
        assert result == ""

    def test_sort_news_latest(self, news: News) -> None:
        """Latest sort returns newest first."""
        items = [
            _sample_headline(published=1000),
            _sample_headline(published=3000),
            _sample_headline(published=2000),
        ]
        result = news._sort_news(items, "latest")
        assert [r["published"] for r in result] == [3000, 2000, 1000]

    def test_sort_news_oldest(self, news: News) -> None:
        """Oldest sort returns oldest first."""
        items = [
            _sample_headline(published=1000),
            _sample_headline(published=3000),
            _sample_headline(published=2000),
        ]
        result = news._sort_news(items, "oldest")
        assert [r["published"] for r in result] == [1000, 2000, 3000]

    def test_sort_news_most_urgent(self, news: News) -> None:
        """Most urgent sort returns highest urgency first."""
        items = [
            {"published": 1000, "urgency": 2},
            {"published": 2000, "urgency": 5},
            {"published": 3000, "urgency": 1},
        ]
        result = news._sort_news(items, "most_urgent")
        assert [r["urgency"] for r in result] == [5, 2, 1]

    def test_sort_news_least_urgent(self, news: News) -> None:
        """Least urgent sort returns lowest urgency first."""
        items = [
            {"published": 1000, "urgency": 2},
            {"published": 2000, "urgency": 5},
            {"published": 3000, "urgency": 1},
        ]
        result = news._sort_news(items, "least_urgent")
        assert [r["urgency"] for r in result] == [1, 2, 5]
