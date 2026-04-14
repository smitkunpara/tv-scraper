"""Unit tests for the new News Flow (v2) Mediator API.

Tests the new categorical filtering and data cleaning logic.
"""

from unittest.mock import patch

from tv_scraper.core.constants import STATUS_FAILED
from tv_scraper.scrapers.social.news import News


class TestNewsV2Unit:
    """Tests the new Mediator API logic in isolation."""

    def test_clean_mediator_headline_fields(self):
        """Verify all new Mediator fields are correctly mapped."""
        scraper = News()
        raw_item = {
            "id": "tag:reuters.com,2024:newsml_1",
            "title": "Mediator News",
            "published": 1700000000,
            "urgency": 2,
            "permission": "free",
            "relatedSymbols": [{"symbol": "AAPL"}],
            "storyPath": "news/path-1",
            "provider": {"id": "reuters", "name": "Reuters"},
            "is_flash": True,
            "extra_junk": "should be removed",
        }

        cleaned = scraper._clean_headline(raw_item)

        assert cleaned["id"] == "tag:reuters.com,2024:newsml_1"
        assert cleaned["title"] == "Mediator News"
        assert cleaned["published"] == 1700000000
        assert cleaned["urgency"] == 2
        assert cleaned["permission"] == "free"
        assert cleaned["relatedSymbols"] == [{"symbol": "AAPL"}]
        assert cleaned["storyPath"] == "/news/path-1"
        assert cleaned["provider"] == {"id": "reuters", "name": "Reuters"}
        assert cleaned["is_flash"] is True
        assert "extra_junk" not in cleaned

    def test_clean_mediator_headline_missing_fields(self):
        """Verify missing fields handled gracefully in Mediator cleaning."""
        scraper = News()
        cleaned = scraper._clean_headline({})

        assert cleaned["id"] is None
        assert cleaned["title"] is None
        assert cleaned["published"] is None
        assert cleaned["urgency"] is None
        assert cleaned["permission"] is None
        assert cleaned["relatedSymbols"] == []
        assert cleaned["storyPath"] == ""
        assert cleaned["provider"] == {}
        assert cleaned["is_flash"] is False

    @patch("tv_scraper.scrapers.social.news.News._request")
    def test_get_news_filter_building(self, mock_request):
        """Verify complex filter parameters are correctly formatted for the API."""
        scraper = News()
        mock_request.return_value = ({"items": []}, None)

        scraper.get_news(
            market_country=["US", "GB"],
            market=["stock", "crypto"],
            corp_activity=["dividends"],
        )

        # Check that _request was called with the correct params
        _, kwargs = mock_request.call_args
        params = kwargs.get("params", {})

        # The filter values should be joined by commas within each 'filter' key
        # requests.request handles multiple keys with the same name if passed as a list of tuples
        # Our implementation creates a direct list of tuples for filters

        expected_filters = [
            "market_country:US,GB",
            "market:stock,crypto",
            "corp_activity:dividends",
            "lang:en",  # Default
        ]

        # Find filter entries in params
        actual_filters = params.get("filter", [])
        for expected in expected_filters:
            assert expected in actual_filters

    def test_url_length_guard(self):
        """Verify that overly long filter combinations are blocked before request."""
        scraper = News()
        # Create a massive list of countries to trigger the length guard
        long_countries = ["US"] * 1000

        result = scraper.get_news(market_country=long_countries)

        assert result["status"] == STATUS_FAILED
        assert "URL length" in result["error"]
        assert "exceeds" in result["error"]
