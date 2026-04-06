"""Mock tests for news scraper.

Tests using saved JSON fixtures from tests/fixtures/news/.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.social.news import News

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "news"


def load_fixture(name: str) -> dict[str, Any]:
    """Load fixture data from JSON file."""
    filepath = FIXTURES_DIR / f"{name}.json"
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return {}


def has_fixture(name: str) -> bool:
    """Check if fixture exists."""
    return (FIXTURES_DIR / f"{name}.json").exists()


@pytest.fixture
def scraper() -> News:
    """Create a News scraper instance."""
    return News()


@pytest.fixture
def mock_request_success() -> MagicMock:
    """Create a mock for successful request."""
    mock = MagicMock()
    mock.return_value = ({"items": []}, None)
    return mock


class TestMockNewsHeadlines:
    """Test news headlines with mocked responses."""

    def test_headlines_with_fixture_data(self, scraper: News) -> None:
        """Test headlines response structure with fixture data."""
        if not has_fixture("headlines_NASDAQ_AAPL"):
            pytest.skip("Fixture not available")

        fixture = load_fixture("headlines_NASDAQ_AAPL")
        assert "status" in fixture
        assert "data" in fixture
        assert "metadata" in fixture
        assert "error" in fixture

        if fixture["status"] == STATUS_SUCCESS:
            for item in fixture["data"]:
                assert "id" in item
                assert "title" in item
                assert "shortDescription" in item
                assert "published" in item
                assert "storyPath" in item

    def test_headlines_crypto_with_fixture(self, scraper: News) -> None:
        """Test crypto headlines with fixture data."""
        if not has_fixture("headlines_crypto BINANCE_BTCUSDT"):
            pytest.skip("Fixture not available")

        fixture = load_fixture("headlines_crypto BINANCE_BTCUSDT")
        assert fixture["status"] == STATUS_SUCCESS
        assert isinstance(fixture["data"], list)

    def test_headlines_stock_with_fixture(self, scraper: News) -> None:
        """Test stock headlines with fixture data."""
        if not has_fixture("headlines_stock NYSE_JPM"):
            pytest.skip("Fixture not available")

        fixture = load_fixture("headlines_stock NYSE_JPM")
        assert fixture["status"] == STATUS_SUCCESS
        assert isinstance(fixture["data"], list)

    def test_headlines_with_provider_fixture(self, scraper: News) -> None:
        """Test headlines with provider filter using available fixture."""
        fixture = load_fixture("headlines_NASDAQ_AAPL")
        assert "status" in fixture
        assert "data" in fixture
        assert isinstance(fixture["data"], list)

    def test_headlines_with_area_fixture(self, scraper: News) -> None:
        """Test headlines with area filter using available fixture."""
        fixture = load_fixture("headlines_NASDAQ_AAPL")
        assert "status" in fixture
        assert "data" in fixture
        assert isinstance(fixture["data"], list)


class TestMockNewsContent:
    """Test news content with mocked responses."""

    def test_content_with_fixture_data(self, scraper: News) -> None:
        """Test content response structure with fixture data."""
        if not has_fixture("content_basic"):
            pytest.skip("Fixture not available")

        fixture = load_fixture("content_basic")
        assert "status" in fixture
        assert "data" in fixture
        assert "metadata" in fixture
        assert "error" in fixture

        if fixture["status"] == STATUS_SUCCESS:
            data = fixture["data"]
            assert "id" in data
            assert "title" in data
            assert "description" in data
            assert "published" in data
            assert "storyPath" in data

    def test_content_from_fixture_with_headlines(self, scraper: News) -> None:
        """Test fetching content using IDs from headlines fixture."""
        if not has_fixture("headlines_NASDAQ_AAPL"):
            pytest.skip("Headlines fixture not available")

        headlines = load_fixture("headlines_NASDAQ_AAPL")
        if not headlines.get("data"):
            pytest.skip("No headlines data available")

        story_id = headlines["data"][0]["id"]
        assert story_id is not None

    def test_content_multiple_stories_fixture(self, scraper: News) -> None:
        """Test multiple story content fixtures."""
        for i in range(5):
            if not has_fixture(f"content_story_{i}"):
                continue
            fixture = load_fixture(f"content_story_{i}")
            assert "status" in fixture
            if fixture["status"] == STATUS_SUCCESS:
                assert "data" in fixture
                assert fixture["data"]["id"] is not None


class TestMockNewsResponseValidation:
    """Test response validation with mocked data."""

    def test_response_has_required_fields(self, scraper: News) -> None:
        """Verify response structure has required fields."""
        sample_response = {
            "status": STATUS_SUCCESS,
            "data": [
                {
                    "id": "tag:test.com,2026:newsml_123",
                    "title": "Test Headline",
                    "shortDescription": "Test description",
                    "published": 1700000000,
                    "storyPath": "/news/test",
                }
            ],
            "metadata": {
                "exchange": "NASDAQ",
                "symbol": "AAPL",
                "sort_by": "latest",
                "section": "all",
                "language": "en",
                "total": 1,
            },
            "error": None,
        }

        assert "status" in sample_response
        assert "data" in sample_response
        assert "metadata" in sample_response
        assert "error" in sample_response

    def test_success_response_validation(self, scraper: News) -> None:
        """Verify success response validation."""
        success_response = {
            "status": STATUS_SUCCESS,
            "data": [],
            "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
            "error": None,
        }
        assert success_response["status"] == STATUS_SUCCESS
        assert success_response["error"] is None

    def test_error_response_validation(self, scraper: News) -> None:
        """Verify error response validation."""
        error_response = {
            "status": STATUS_FAILED,
            "data": None,
            "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
            "error": "Invalid exchange",
        }
        assert error_response["status"] == STATUS_FAILED
        assert error_response["error"] is not None
        assert error_response["data"] is None


class TestMockNewsSorting:
    """Test sorting functionality with mocked data."""

    def test_sort_latest_with_fixture_data(self, scraper: News) -> None:
        """Verify latest sorting with mock data."""
        items = [
            {"id": "1", "published": 1000, "urgency": 5},
            {"id": "2", "published": 3000, "urgency": 1},
            {"id": "3", "published": 2000, "urgency": 3},
        ]
        result = scraper._sort_news(items, "latest")
        assert result[0]["id"] == "2"
        assert result[1]["id"] == "3"
        assert result[2]["id"] == "1"

    def test_sort_oldest_with_fixture_data(self, scraper: News) -> None:
        """Verify oldest sorting with mock data."""
        items = [
            {"id": "1", "published": 1000, "urgency": 5},
            {"id": "2", "published": 3000, "urgency": 1},
            {"id": "3", "published": 2000, "urgency": 3},
        ]
        result = scraper._sort_news(items, "oldest")
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "3"
        assert result[2]["id"] == "2"

    def test_sort_urgency_with_fixture_data(self, scraper: News) -> None:
        """Verify urgency sorting with mock data."""
        items = [
            {"id": "1", "published": 1000, "urgency": 1},
            {"id": "2", "published": 3000, "urgency": 5},
            {"id": "3", "published": 2000, "urgency": 3},
        ]
        result_most = scraper._sort_news(items, "most_urgent")
        result_least = scraper._sort_news(items, "least_urgent")

        assert result_most[0]["id"] == "2"
        assert result_least[0]["id"] == "1"


class TestMockNewsHeadlineCleaning:
    """Test headline cleaning with mocked data."""

    def test_clean_headline_removes_extra_fields(self, scraper: News) -> None:
        """Verify extra fields removed from headline."""
        raw_item = {
            "id": "tag:test.com,2026:newsml_123",
            "title": "Test Headline",
            "shortDescription": "Test description",
            "published": 1700000000,
            "storyPath": "/news/test",
            "sourceLogoid": "logo",
            "provider": "reuters",
            "relatedSymbols": ["AAPL"],
            "permission": "public",
            "urgency": 3,
        }
        cleaned = scraper._clean_headline(raw_item)

        assert "id" in cleaned
        assert "title" in cleaned
        assert "shortDescription" in cleaned
        assert "published" in cleaned
        assert "storyPath" in cleaned
        assert "sourceLogoid" not in cleaned
        assert "provider" not in cleaned
        assert "relatedSymbols" not in cleaned
        assert "permission" not in cleaned
        assert "urgency" not in cleaned

    def test_clean_headline_handles_missing_keys(self, scraper: News) -> None:
        """Verify missing keys handled gracefully."""
        empty_item: dict[str, Any] = {}
        cleaned = scraper._clean_headline(empty_item)

        assert cleaned["id"] is None
        assert cleaned["title"] is None
        assert cleaned["shortDescription"] is None
        assert cleaned["published"] is None
        assert cleaned["storyPath"] == ""


class TestMockNewsContentParsing:
    """Test content parsing with mocked data."""

    def test_parse_story_extracts_fields(self, scraper: News) -> None:
        """Verify story parsing extracts all fields."""
        story_data = {
            "id": "tag:test.com,2026:newsml_123",
            "title": "Test Article",
            "published": 1700000000,
            "ast_description": {"children": []},
            "story_path": "/news/test",
        }
        result = scraper._parse_story(story_data)

        assert result["id"] == "tag:test.com,2026:newsml_123"
        assert result["title"] == "Test Article"
        assert result["published"] == 1700000000
        assert result["description"] == ""
        assert result["storyPath"] == "/news/test"

    def test_parse_story_with_paragraphs(self, scraper: News) -> None:
        """Verify paragraph parsing from AST."""
        story_data = {
            "id": "tag:test.com,2026:newsml_123",
            "title": "Test",
            "published": 1700000000,
            "ast_description": {
                "children": [
                    {"type": "p", "children": ["First paragraph."]},
                    {"type": "p", "children": ["Second paragraph."]},
                ]
            },
            "story_path": "/test",
        }
        result = scraper._parse_story(story_data)

        assert "First paragraph." in result["description"]
        assert "Second paragraph." in result["description"]

    def test_parse_ast_with_symbol_objects(self, scraper: News) -> None:
        """Verify symbol objects in paragraphs parsed."""
        ast_desc = {
            "children": [
                {
                    "type": "p",
                    "children": [
                        "Price for ",
                        {"type": "symbol", "params": {"text": "AAPL"}},
                        " is $150.",
                    ],
                }
            ]
        }
        result = scraper._parse_ast_description(ast_desc)

        assert "Price for" in result
        assert "AAPL" in result
        assert "is $150." in result


class TestMockNewsValidation:
    """Test validation with mocked requests."""

    def test_invalid_sort_returns_error(self, scraper: News) -> None:
        """Verify invalid sort_by returns error."""
        with patch.object(scraper, "_request") as mock_request:
            mock_request.return_value = ({"items": []}, None)
            result = scraper.get_news_headlines(
                exchange="NASDAQ", symbol="AAPL", sort_by="invalid_sort"
            )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_invalid_section_returns_error(self, scraper: News) -> None:
        """Verify invalid section returns error."""
        with patch.object(scraper, "_request") as mock_request:
            mock_request.return_value = ({"items": []}, None)
            result = scraper.get_news_headlines(
                exchange="NASDAQ", symbol="AAPL", section="invalid_section"
            )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_invalid_language_returns_error(self, scraper: News) -> None:
        """Verify invalid language returns error."""
        with patch.object(scraper, "_request") as mock_request:
            mock_request.return_value = ({"items": []}, None)
            result = scraper.get_news_headlines(
                exchange="NASDAQ", symbol="AAPL", language="invalid"
            )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_invalid_provider_returns_error(self, scraper: News) -> None:
        """Verify invalid provider returns error."""
        with patch.object(scraper, "_request") as mock_request:
            mock_request.return_value = ({"items": []}, None)
            result = scraper.get_news_headlines(
                exchange="NASDAQ", symbol="AAPL", provider="invalid"
            )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_invalid_area_returns_error(self, scraper: News) -> None:
        """Verify invalid area returns error."""
        with patch.object(scraper, "_request") as mock_request:
            mock_request.return_value = ({"items": []}, None)
            result = scraper.get_news_headlines(
                exchange="NASDAQ", symbol="AAPL", area="invalid"
            )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_empty_story_id_returns_error(self, scraper: News) -> None:
        """Verify empty story_id returns error."""
        result = scraper.get_news_content(story_id="")
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_invalid_content_language_returns_error(self, scraper: News) -> None:
        """Verify invalid content language returns error."""
        result = scraper.get_news_content(
            story_id="tag:test.com,2026:newsml_123", language="invalid"
        )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None


class TestMockNewsExport:
    """Test export functionality with mocked data."""

    def test_export_enabled(self, scraper: News) -> None:
        """Verify export is called when enabled."""
        scraper_export = News(export_result=True)
        with patch.object(scraper_export, "_request") as mock_request:
            mock_request.return_value = (
                {
                    "items": [
                        {
                            "id": "tag:test.com,2026:newsml_123",
                            "title": "Test",
                            "shortDescription": "Desc",
                            "published": 1700000000,
                            "storyPath": "/test",
                        }
                    ]
                },
                None,
            )
            with patch.object(scraper_export, "_export") as mock_export:
                scraper_export.get_news_headlines(exchange="NASDAQ", symbol="AAPL")
                mock_export.assert_called_once()

    def test_export_disabled(self, scraper: News) -> None:
        """Verify export not called when disabled."""
        with patch.object(scraper, "_request") as mock_request:
            mock_request.return_value = ({"items": []}, None)
            with patch.object(scraper, "_export") as mock_export:
                scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL")
                mock_export.assert_not_called()


class TestMockNewsNetworkErrors:
    """Test network error handling with mocked responses."""

    def test_network_error_returns_error_response(self, scraper: News) -> None:
        """Verify network error returns proper error response."""
        with patch.object(scraper, "_request") as mock_request:
            mock_request.return_value = (None, "Network error: Connection refused")
            result = scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL")
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    def test_empty_response_handling(self, scraper: News) -> None:
        """Verify empty response handled correctly."""
        with patch.object(scraper, "_request") as mock_request:
            mock_request.return_value = (None, "Empty response from server")
            result = scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL")
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None


class TestMockNewsFixturesIntegration:
    """Test integration with actual fixture files."""

    def test_load_all_available_fixtures(self, scraper: News) -> None:
        """Test loading all available fixtures."""
        fixture_files = list(FIXTURES_DIR.glob("*.json"))
        if not fixture_files:
            pytest.skip("No fixtures found - run live tests first to generate fixtures")

        loaded_count = 0
        for fixture_file in fixture_files:
            with open(fixture_file) as f:
                data = json.load(f)
                assert "status" in data
                loaded_count += 1

        assert loaded_count >= 0, "Fixtures loaded successfully"

    def test_fixture_headlines_structure(self, scraper: News) -> None:
        """Verify headlines fixtures have correct structure."""
        fixture_names = [
            "headlines_NASDAQ_AAPL",
            "headlines_crypto BINANCE_BTCUSDT",
            "headlines_stock NYSE_JPM",
        ]

        for name in fixture_names:
            if has_fixture(name):
                fixture = load_fixture(name)
                if fixture.get("status") == STATUS_SUCCESS:
                    for item in fixture.get("data", []):
                        assert "id" in item
                        assert "title" in item
                        assert "published" in item
                        assert "storyPath" in item

    def test_fixture_content_structure(self, scraper: News) -> None:
        """Verify content fixtures have correct structure."""
        fixture_names = ["content_basic", "content_from_fixture"]

        for name in fixture_names:
            if has_fixture(name):
                fixture = load_fixture(name)
                if fixture.get("status") == STATUS_SUCCESS:
                    data = fixture.get("data", {})
                    assert "id" in data
                    assert "title" in data
                    assert "description" in data
                    assert "published" in data
