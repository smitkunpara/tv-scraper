"""Unit tests for news scraper.

Tests isolated functions of the News scraper class.
"""

from pathlib import Path
from typing import Any
from unittest.mock import patch

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.social.news import News

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "news"


class TestNewsHeadlinesResponse:
    """Test news headlines response structure."""

    def test_response_has_required_fields(self) -> None:
        """Verify response contains required fields."""
        scraper = News()
        with patch.object(scraper, "_request") as mock_request:
            mock_request.return_value = (
                {
                    "items": [
                        {
                            "id": "tag:test.com,2026:newsml_123",
                            "title": "Test Headline",
                            "shortDescription": "Test description",
                            "published": 1700000000,
                            "storyPath": "/news/test",
                        }
                    ]
                },
                None,
            )
            result = scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL")

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result

    def test_response_metadata_contains_query_params(self) -> None:
        """Verify metadata contains query parameters."""
        scraper = News()
        with patch.object(scraper, "_request") as mock_request:
            mock_request.return_value = ({"items": []}, None)
            result = scraper.get_news_headlines(
                exchange="NASDAQ",
                symbol="AAPL",
                provider="reuters",
                area="us",
                sort_by="latest",
                section="all",
                language="en",
            )

        metadata = result["metadata"]
        assert metadata["exchange"] == "NASDAQ"
        assert metadata["symbol"] == "AAPL"
        assert metadata["sort_by"] == "latest"
        assert metadata["section"] == "all"
        assert metadata["language"] == "en"
        assert metadata["provider"] == "reuters"
        assert metadata["area"] == "us"

    def test_success_response_status(self) -> None:
        """Verify success response has correct status."""
        scraper = News()
        with patch.object(scraper, "_request") as mock_request:
            mock_request.return_value = ({"items": []}, None)
            result = scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL")
        assert result["status"] == STATUS_SUCCESS

    def test_error_response_status(self) -> None:
        """Verify error response has correct status."""
        scraper = News()
        with patch.object(scraper, "_request") as mock_request:
            mock_request.return_value = (None, "Network error")
            result = scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL")
        assert result["status"] == STATUS_FAILED


class TestNewsHeadlinesSorting:
    """Test news sorting functionality."""

    def test_sort_latest(self) -> None:
        """Verify latest sorting (descending by published)."""
        scraper = News()
        items = [
            {"id": "1", "published": 1000, "urgency": 5},
            {"id": "2", "published": 3000, "urgency": 1},
            {"id": "3", "published": 2000, "urgency": 3},
        ]
        result = scraper._sort_news(items, "latest")
        assert result[0]["id"] == "2"
        assert result[1]["id"] == "3"
        assert result[2]["id"] == "1"

    def test_sort_oldest(self) -> None:
        """Verify oldest sorting (ascending by published)."""
        scraper = News()
        items = [
            {"id": "1", "published": 1000, "urgency": 5},
            {"id": "2", "published": 3000, "urgency": 1},
            {"id": "3", "published": 2000, "urgency": 3},
        ]
        result = scraper._sort_news(items, "oldest")
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "3"
        assert result[2]["id"] == "2"

    def test_sort_most_urgent(self) -> None:
        """Verify most urgent sorting (descending by urgency)."""
        scraper = News()
        items = [
            {"id": "1", "published": 1000, "urgency": 1},
            {"id": "2", "published": 3000, "urgency": 5},
            {"id": "3", "published": 2000, "urgency": 3},
        ]
        result = scraper._sort_news(items, "most_urgent")
        assert result[0]["id"] == "2"
        assert result[1]["id"] == "3"
        assert result[2]["id"] == "1"

    def test_sort_least_urgent(self) -> None:
        """Verify least urgent sorting (ascending by urgency)."""
        scraper = News()
        items = [
            {"id": "1", "published": 1000, "urgency": 5},
            {"id": "2", "published": 3000, "urgency": 1},
            {"id": "3", "published": 2000, "urgency": 3},
        ]
        result = scraper._sort_news(items, "least_urgent")
        assert result[0]["id"] == "2"
        assert result[1]["id"] == "3"
        assert result[2]["id"] == "1"


class TestNewsHeadlineCleaning:
    """Test headline cleaning functionality."""

    def test_clean_headline_removes_unwanted_fields(self) -> None:
        """Verify unwanted fields are removed from headline."""
        scraper = News()
        item = {
            "id": "tag:test.com,2026:newsml_123",
            "title": "Test Headline",
            "shortDescription": "Test description",
            "published": 1700000000,
            "storyPath": "/news/test",
            "sourceLogoid": "source_logo",
            "provider": "reuters",
            "relatedSymbols": ["AAPL", "GOOGL"],
            "permission": "public",
            "urgency": 3,
        }
        result = scraper._clean_legacy_headline(item)
        assert "id" in result
        assert "title" in result
        assert "shortDescription" in result
        assert "published" in result
        assert "storyPath" in result
        assert "sourceLogoid" not in result
        assert "provider" not in result
        assert "relatedSymbols" not in result
        assert "permission" not in result
        assert "urgency" not in result

    def test_clean_headline_handles_missing_fields(self) -> None:
        """Verify missing fields handled gracefully."""
        scraper = News()
        item: dict[str, Any] = {}
        result = scraper._clean_legacy_headline(item)
        assert result["id"] is None
        assert result["title"] is None
        assert result["shortDescription"] is None
        assert result["published"] is None
        assert result["storyPath"] == ""


class TestStoryPathNormalization:
    """Test story path normalization."""

    def test_normalize_story_path_adds_leading_slash(self) -> None:
        """Verify leading slash added when missing."""
        scraper = News()
        result = scraper._normalize_story_path("news/test")
        assert result == "/news/test"

    def test_normalize_story_path_keeps_existing_slash(self) -> None:
        """Verify existing leading slash preserved."""
        scraper = News()
        result = scraper._normalize_story_path("/news/test")
        assert result == "/news/test"

    def test_normalize_story_path_empty_string(self) -> None:
        """Verify empty string remains empty."""
        scraper = News()
        result = scraper._normalize_story_path("")
        assert result == ""


class TestNewsContentParsing:
    """Test news content parsing functionality."""

    def test_parse_story_extracts_required_fields(self) -> None:
        """Verify story parsing extracts required fields."""
        scraper = News()
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

    def test_parse_story_with_paragraphs(self) -> None:
        """Verify paragraph parsing from AST."""
        scraper = News()
        story_data = {
            "id": "tag:test.com,2026:newsml_123",
            "title": "Test Article",
            "published": 1700000000,
            "ast_description": {
                "children": [
                    {
                        "type": "p",
                        "children": ["First paragraph."],
                    },
                    {
                        "type": "p",
                        "children": ["Second paragraph."],
                    },
                ]
            },
            "story_path": "/news/test",
        }
        result = scraper._parse_story(story_data)
        assert "First paragraph." in result["description"]
        assert "Second paragraph." in result["description"]

    def test_parse_ast_description_paragraph_merging(self) -> None:
        """Verify paragraph text merged correctly."""
        scraper = News()
        ast_desc = {
            "children": [
                {
                    "type": "p",
                    "children": ["Text part 1 ", "Text part 2"],
                }
            ]
        }
        result = scraper._parse_ast_description(ast_desc)
        assert "Text part 1" in result
        assert "Text part 2" in result

    def test_parse_ast_description_with_symbol_objects(self) -> None:
        """Verify symbol objects in paragraphs handled."""
        scraper = News()
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

    def test_parse_paragraph_children_string_list(self) -> None:
        """Verify string list children parsed."""
        scraper = News()
        result = scraper._parse_paragraph_children(["Hello", " ", "World"])
        assert result == "Hello World"

    def test_parse_paragraph_children_dict_list(self) -> None:
        """Verify dict children with params.text parsed."""
        scraper = News()
        result = scraper._parse_paragraph_children(
            [
                {"type": "symbol", "params": {"text": "AAPL"}},
                {"type": "other", "params": {"other": "value"}},
                {"type": "symbol", "params": {"text": "GOOGL"}},
            ]
        )
        assert "AAPL" in result
        assert "GOOGL" in result

    def test_parse_paragraph_children_mixed(self) -> None:
        """Verify mixed string and dict children parsed."""
        scraper = News()
        result = scraper._parse_paragraph_children(
            ["Start ", {"type": "symbol", "params": {"text": "AAPL"}}, " end"]
        )
        assert result == "Start AAPL end"


class TestNewsContentResponse:
    """Test news content response structure."""

    def test_content_response_has_required_fields(self) -> None:
        """Verify content response has required fields."""
        scraper = News()
        with patch.object(scraper, "_request") as mock_request:
            mock_request.return_value = (
                {
                    "id": "tag:test.com,2026:newsml_123",
                    "title": "Test Article",
                    "published": 1700000000,
                    "ast_description": {"children": []},
                    "story_path": "/news/test",
                },
                None,
            )
            result = scraper.get_news_content(story_id="tag:test.com,2026:newsml_123")

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result

    def test_content_success_response(self) -> None:
        """Verify content success response."""
        scraper = News()
        with patch.object(scraper, "_request") as mock_request:
            mock_request.return_value = (
                {
                    "id": "tag:test.com,2026:newsml_123",
                    "title": "Test",
                    "published": 1700000000,
                    "ast_description": {"children": []},
                    "story_path": "/test",
                },
                None,
            )
            result = scraper.get_news_content(story_id="tag:test.com,2026:newsml_123")
        assert result["status"] == STATUS_SUCCESS

    def test_content_error_on_empty_story_id(self) -> None:
        """Verify empty story ID returns error."""
        scraper = News()
        result = scraper.get_news_content(story_id="")
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_content_error_on_whitespace_story_id(self) -> None:
        """Verify whitespace story ID returns error."""
        scraper = News()
        result = scraper.get_news_content(story_id="   ")
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_content_error_on_invalid_language(self) -> None:
        """Verify invalid language returns error."""
        scraper = News()
        result = scraper.get_news_content(
            story_id="tag:test.com,2026:newsml_123", language="invalid"
        )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None


class TestNewsValidation:
    """Test news scraper validation."""

    def test_invalid_sort_by_returns_error(self) -> None:
        """Verify invalid sort_by returns error."""
        scraper = News()
        result = scraper.get_news_headlines(
            exchange="NASDAQ", symbol="AAPL", sort_by="invalid_sort"
        )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_invalid_section_returns_error(self) -> None:
        """Verify invalid section returns error."""
        scraper = News()
        result = scraper.get_news_headlines(
            exchange="NASDAQ", symbol="AAPL", section="invalid_section"
        )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_invalid_language_returns_error(self) -> None:
        """Verify invalid language returns error."""
        scraper = News()
        result = scraper.get_news_headlines(
            exchange="NASDAQ", symbol="AAPL", language="invalid_lang"
        )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_invalid_provider_returns_error(self) -> None:
        """Verify invalid provider returns error."""
        scraper = News()
        result = scraper.get_news_headlines(
            exchange="NASDAQ", symbol="AAPL", provider="invalid_provider"
        )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_invalid_area_returns_error(self) -> None:
        """Verify invalid area returns error."""
        scraper = News()
        result = scraper.get_news_headlines(
            exchange="NASDAQ", symbol="AAPL", area="invalid_area"
        )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None


class TestNewsExport:
    """Test news export functionality."""

    def test_export_called_when_enabled(self) -> None:
        """Verify export is called when export_result is True."""
        scraper = News(export_result=True)
        with patch.object(scraper, "_request") as mock_request:
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
            with patch.object(scraper, "_export") as mock_export:
                scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL")
                mock_export.assert_called_once()

    def test_export_not_called_when_disabled(self) -> None:
        """Verify export is not called when export_result is False."""
        scraper = News(export_result=False)
        with patch.object(scraper, "_request") as mock_request:
            mock_request.return_value = ({"items": []}, None)
            with patch.object(scraper, "_export") as mock_export:
                scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL")
                mock_export.assert_not_called()


class TestNewsEmptyResults:
    """Test empty results handling."""

    def test_empty_items_returns_empty_list(self) -> None:
        """Verify empty items returns empty list."""
        scraper = News()
        with patch.object(scraper, "_request") as mock_request:
            mock_request.return_value = ({"items": []}, None)
            result = scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL")
        assert result["data"] == []
        assert result["metadata"]["total"] == 0

    def test_missing_items_field_returns_empty_list(self) -> None:
        """Verify missing items field returns empty list."""
        scraper = News()
        with patch.object(scraper, "_request") as mock_request:
            mock_request.return_value = ({}, None)
            result = scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL")
        assert result["data"] == []
        assert result["metadata"]["total"] == 0
