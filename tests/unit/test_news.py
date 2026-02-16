"""Tests for News scraper module."""

from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

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


_ARTICLE_HTML = """
<html>
<body>
<article>
  <nav aria-label="Breadcrumbs">
    <span class="breadcrumb-content-cZAS4vtj">Markets</span>
    <span class="breadcrumb-content-cZAS4vtj">Crypto</span>
  </nav>
  <h1 class="title-KX2tCBZq">Bitcoin Hits New High</h1>
  <time datetime="2025-01-15T10:00:00Z">Jan 15</time>
  <div class="symbolsContainer-cBh_FN2P">
    <a href="/symbols/BTCUSD">
      <span class="description-cBh_FN2P">BTCUSD</span>
      <img src="https://logo.com/btc.png" alt="BTC" />
    </a>
  </div>
  <div class="body-KX2tCBZq">
    <p>Bitcoin surged to a new all-time high today.</p>
    <img src="https://img.com/chart.png" alt="Chart" />
    <p>Market analysts are optimistic.</p>
  </div>
</article>
<div class="rowTags-XYZ">
  <span>Bitcoin</span>
  <span>Crypto</span>
</div>
</body>
</html>
"""


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

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_scrape_headlines_success(self, mock_get: MagicMock, news: News) -> None:
        """Standard headline retrieval returns success envelope."""
        mock_get.return_value = _mock_response(
            json_data=_make_headlines_response([_sample_headline()]),
        )

        result = news.scrape_headlines(exchange="BINANCE", symbol="BTCUSD")

        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 1

        item = result["data"][0]
        # Should contain these fields
        assert item["id"] == "h123"
        assert item["title"] == "Bitcoin Hits New High"
        assert item["shortDescription"] == "Bitcoin reached an all-time high today."
        assert item["published"] == 1678900000
        assert item["storyPath"] == "/news/story/h123"
        # Should NOT contain these fields
        assert "provider" not in item
        assert "urgency" not in item
        assert "relatedSymbols" not in item
        assert "permission" not in item
        assert "sourceLogoid" not in item

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_scrape_headlines_with_provider(
        self, mock_get: MagicMock, news: News
    ) -> None:
        """Provider filter is passed through to the API URL."""
        mock_get.return_value = _mock_response(
            json_data=_make_headlines_response([_sample_headline()]),
        )

        result = news.scrape_headlines(
            exchange="BINANCE",
            symbol="BTCUSD",
            provider="cointelegraph",
        )

        assert result["status"] == STATUS_SUCCESS
        # Verify provider appears in the request URL
        call_url = mock_get.call_args[0][0]
        assert "provider=cointelegraph" in call_url

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_scrape_headlines_with_area(self, mock_get: MagicMock, news: News) -> None:
        """Area filter is converted to area code and passed through."""
        mock_get.return_value = _mock_response(
            json_data=_make_headlines_response([_sample_headline()]),
        )

        result = news.scrape_headlines(
            exchange="BINANCE",
            symbol="BTCUSD",
            area="americas",
        )

        assert result["status"] == STATUS_SUCCESS
        call_url = mock_get.call_args[0][0]
        assert "area=AME" in call_url

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_scrape_headlines_with_language(
        self, mock_get: MagicMock, news: News
    ) -> None:
        """Language filter is passed through to the API URL."""
        mock_get.return_value = _mock_response(
            json_data=_make_headlines_response([_sample_headline()]),
        )

        result = news.scrape_headlines(
            exchange="BINANCE",
            symbol="BTCUSD",
            language="fr",
        )

        assert result["status"] == STATUS_SUCCESS
        call_url = mock_get.call_args[0][0]
        assert "lang=fr" in call_url

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_scrape_headlines_empty_result(
        self, mock_get: MagicMock, news: News
    ) -> None:
        """No headlines returns success with empty list."""
        mock_get.return_value = _mock_response(
            json_data=_make_headlines_response([]),
        )

        result = news.scrape_headlines(exchange="BINANCE", symbol="BTCUSD")

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] == []
        assert result["error"] is None

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_scrape_headlines_combined_symbol(
        self, mock_get: MagicMock, news: News
    ) -> None:
        """Combined EXCHANGE:SYMBOL in symbol parameter is supported."""
        mock_get.return_value = _mock_response(
            json_data=_make_headlines_response([_sample_headline()]),
        )

        # Pass empty exchange and combined symbol
        result = news.scrape_headlines(exchange="", symbol="BINANCE:BTCUSD")

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["exchange"] == "BINANCE"
        assert result["metadata"]["symbol"] == "BTCUSD"

        # Verify URL has correct symbol parameter
        call_url = mock_get.call_args[0][0]
        assert "symbol=BINANCE:BTCUSD" in call_url


# ---------------------------------------------------------------------------
# scrape_headlines — validation errors
# ---------------------------------------------------------------------------


class TestScrapeHeadlinesValidation:
    """Validation failures return error responses — never raise."""

    def test_scrape_headlines_invalid_exchange(self, news: News) -> None:
        """Invalid exchange returns error response."""
        result = news.scrape_headlines(exchange="FAKEXCHANGE", symbol="BTCUSD")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None
        assert (
            "exchange" in result["error"].lower()
            or "invalid" in result["error"].lower()
        )

    def test_scrape_headlines_empty_symbol(self, news: News) -> None:
        """Empty symbol returns error response."""
        result = news.scrape_headlines(exchange="BINANCE", symbol="")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    def test_scrape_headlines_invalid_sort(self, news: News) -> None:
        """Invalid sort_by value returns error response."""
        result = news.scrape_headlines(
            exchange="BINANCE",
            symbol="BTCUSD",
            sort_by="invalid_sort",
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "sort" in result["error"].lower() or "invalid" in result["error"].lower()

    def test_scrape_headlines_invalid_section(self, news: News) -> None:
        """Invalid section value returns error response."""
        result = news.scrape_headlines(
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

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_scrape_headlines_network_error(
        self, mock_get: MagicMock, news: News
    ) -> None:
        """Network failure returns error response, does not raise."""
        mock_get.side_effect = Exception("Connection refused")

        result = news.scrape_headlines(exchange="BINANCE", symbol="BTCUSD")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_scrape_headlines_captcha(self, mock_get: MagicMock, news: News) -> None:
        """Captcha challenge returns error response."""
        mock_get.return_value = _mock_response(
            text="<title>Captcha Challenge</title>",
        )

        result = news.scrape_headlines(exchange="BINANCE", symbol="BTCUSD")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "captcha" in result["error"].lower()


# ---------------------------------------------------------------------------
# scrape_content — success
# ---------------------------------------------------------------------------


class TestScrapeContentSuccess:
    """Tests for article content scraping using JSON API."""

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_scrape_content_success(self, mock_get: MagicMock, news: News) -> None:
        """Successfully parse article JSON into structured content."""
        mock_get.return_value = _mock_response(json_data=_STORY_JSON)

        result = news.scrape_content(story_id="tag:reuters.com,2026:newsml_L4N3Z9104:0")

        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None

        data = result["data"]
        assert data["title"] == "Bitcoin Hits New High"
        assert data["published"] == 1643097623
        assert data["storyPath"] == "/news/story/h123"

        # Check description is properly merged from ast_description
        description = data["description"]
        assert "Bitcoin surged to a new all-time high today." in description
        assert "BTCUSD" in description
        assert "Market analysts are optimistic." in description
        # Paragraphs should be separated by newlines
        assert "\n" in description

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_scrape_content_story_path_without_slash(
        self, mock_get: MagicMock, news: News
    ) -> None:
        """Story path without leading slash should be fixed."""
        story_json = _STORY_JSON.copy()
        story_json["story_path"] = "news/story/h123"  # No leading slash

        mock_get.return_value = _mock_response(json_data=story_json)

        result = news.scrape_content(story_id="tag:reuters.com,2026:newsml_L4N3Z9104:0")

        assert result["status"] == STATUS_SUCCESS
        assert result["data"]["storyPath"] == "/news/story/h123"


# ---------------------------------------------------------------------------
# scrape_content — errors
# ---------------------------------------------------------------------------


class TestScrapeContentErrors:
    """Error handling for content scraping."""

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_scrape_content_network_error(
        self, mock_get: MagicMock, news: News
    ) -> None:
        """Network failure returns error response."""
        mock_get.side_effect = Exception("Connection refused")

        result = news.scrape_content(story_id="tag:reuters.com,2026:newsml_L4N3Z9104:0")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None


# ---------------------------------------------------------------------------
# Response format
# ---------------------------------------------------------------------------


class TestResponseFormat:
    """Verify the standardized response envelope."""

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_response_has_standard_envelope(
        self, mock_get: MagicMock, news: News
    ) -> None:
        """Response contains exactly status/data/metadata/error keys."""
        mock_get.return_value = _mock_response(
            json_data=_make_headlines_response([_sample_headline()]),
        )

        result = news.scrape_headlines(exchange="BINANCE", symbol="BTCUSD")

        assert set(result.keys()) == {"status", "data", "metadata", "error"}
