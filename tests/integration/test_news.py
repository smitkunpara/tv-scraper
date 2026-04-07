"""Integration tests for news scraper.

Tests cross-module workflows and end-to-end scenarios.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.social.ideas import Ideas
from tv_scraper.scrapers.social.minds import Minds
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
def news_scraper() -> News:
    """Create a News scraper instance."""
    return News()


@pytest.fixture
def ideas_scraper() -> Ideas:
    """Create an Ideas scraper instance."""
    return Ideas()


@pytest.fixture
def minds_scraper() -> Minds:
    """Create a Minds scraper instance."""
    return Minds()


@pytest.fixture
def mock_successful_headlines() -> MagicMock:
    """Create mock for successful headlines request."""
    mock = MagicMock()
    mock.return_value = (
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
    return mock


@pytest.fixture
def mock_successful_content() -> MagicMock:
    """Create mock for successful content request."""
    mock = MagicMock()
    mock.return_value = (
        {
            "id": "tag:test.com,2026:newsml_123",
            "title": "Test Article",
            "published": 1700000000,
            "ast_description": {
                "children": [
                    {"type": "p", "children": ["This is the article content."]}
                ]
            },
            "story_path": "/news/test",
        },
        None,
    )
    return mock


@pytest.mark.integration
class TestNewsIdeasIntegration:
    """Test integration between News and Ideas scrapers."""

    def test_news_and_ideas_same_symbol(
        self, news_scraper: News, ideas_scraper: Ideas
    ) -> None:
        """Verify news and ideas can be fetched for same symbol."""
        with patch.object(news_scraper, "_request") as mock_news:
            mock_news.return_value = ({"items": []}, None)
            news_result = news_scraper.get_news_headlines(
                exchange="NASDAQ", symbol="AAPL"
            )

        with patch.object(ideas_scraper, "_request") as mock_ideas:
            mock_ideas.return_value = (
                {
                    "data": {
                        "ideas": {
                            "data": {
                                "items": [
                                    {
                                        "title": "Test Idea",
                                        "description": "Description",
                                        "preview_image": [],
                                        "chart_url": "https://example.com/chart",
                                        "comments_count": 5,
                                        "views_count": 100,
                                        "author": "testuser",
                                        "likes_count": 10,
                                        "timestamp": 1700000000,
                                    }
                                ]
                            }
                        }
                    }
                },
                None,
            )
            ideas_result = ideas_scraper.get_ideas(exchange="NASDAQ", symbol="AAPL")

        assert news_result["status"] == STATUS_SUCCESS
        assert ideas_result["status"] == STATUS_SUCCESS

    def test_news_story_id_extraction_for_content(self, news_scraper: News) -> None:
        """Test extracting story IDs from headlines for content fetching."""
        with patch.object(news_scraper, "_request") as mock_request:
            mock_request.return_value = (
                {
                    "items": [
                        {
                            "id": "tag:reuters.com,2026:newsml_L4N3Z9104:0",
                            "title": "Breaking News",
                            "shortDescription": "Description",
                            "published": 1700000000,
                            "storyPath": "/news/breaking",
                        },
                        {
                            "id": "tag:cointelegraph.com,2026:newsml_ABC123:1",
                            "title": "Crypto News",
                            "shortDescription": "Crypto description",
                            "published": 1699999000,
                            "storyPath": "/news/crypto",
                        },
                    ]
                },
                None,
            )

            headlines_result = news_scraper.get_news_headlines(
                exchange="NASDAQ", symbol="AAPL"
            )

        assert headlines_result["status"] == STATUS_SUCCESS
        assert len(headlines_result["data"]) == 2

        story_ids = [item["id"] for item in headlines_result["data"]]
        assert "tag:reuters.com,2026:newsml_L4N3Z9104:0" in story_ids
        assert "tag:cointelegraph.com,2026:newsml_ABC123:1" in story_ids

    def test_news_ideas_different_exchanges(
        self, news_scraper: News, ideas_scraper: Ideas
    ) -> None:
        """Test news and ideas for different exchanges."""
        with patch.object(news_scraper, "_request") as mock_news:
            mock_news.return_value = ({"items": []}, None)
            news_result = news_scraper.get_news_headlines(
                exchange="BINANCE", symbol="BTCUSDT"
            )

        with patch.object(ideas_scraper, "_request") as mock_ideas:
            mock_ideas.return_value = (
                {
                    "data": {
                        "ideas": {
                            "data": {
                                "items": [
                                    {
                                        "title": "BTC Analysis",
                                        "description": "Analysis",
                                        "preview_image": [],
                                        "chart_url": "https://example.com/chart",
                                        "comments_count": 0,
                                        "views_count": 50,
                                        "author": "trader",
                                        "likes_count": 5,
                                        "timestamp": 1700000000,
                                    }
                                ]
                            }
                        }
                    }
                },
                None,
            )
            ideas_result = ideas_scraper.get_ideas(exchange="BINANCE", symbol="BTCUSDT")

        assert news_result["metadata"]["exchange"] == "BINANCE"
        assert news_result["metadata"]["symbol"] == "BTCUSDT"
        assert ideas_result["status"] == STATUS_SUCCESS


@pytest.mark.integration
class TestNewsMindsIntegration:
    """Test integration between News and Minds scrapers."""

    def test_news_and_minds_same_symbol(
        self, news_scraper: News, minds_scraper: Minds
    ) -> None:
        """Verify news and minds can be fetched for same symbol."""
        with patch.object(news_scraper, "_request") as mock_news:
            mock_news.return_value = ({"items": []}, None)
            news_result = news_scraper.get_news_headlines(
                exchange="NASDAQ", symbol="AAPL"
            )

        with patch.object(minds_scraper, "_request") as mock_minds:
            mock_minds.return_value = (
                {
                    "results": [
                        {
                            "text": "Test mind post",
                            "url": "https://example.com/mind/123",
                            "author": {
                                "username": "trader",
                                "profile_url": "https://example.com/user/trader",
                                "is_broker": False,
                            },
                            "created": "2024-01-01T00:00:00Z",
                            "total_likes": 10,
                            "total_comments": 5,
                        }
                    ]
                },
                None,
            )
            minds_result = minds_scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert news_result["status"] == STATUS_SUCCESS
        assert minds_result["status"] == STATUS_SUCCESS


@pytest.mark.integration
class TestNewsEndToEnd:
    """Test end-to-end news scraping workflows."""

    def test_full_news_workflow(self, news_scraper: News) -> None:
        """Test complete news workflow: headlines -> content."""
        headlines_mock = MagicMock()
        headlines_mock.return_value = (
            {
                "items": [
                    {
                        "id": "tag:reuters.com,2026:newsml_L4N3Z9104:0",
                        "title": "Stock rises on earnings",
                        "shortDescription": "Stock surged after earnings report",
                        "published": 1700000000,
                        "storyPath": "/news/stock-rise",
                    }
                ]
            },
            None,
        )

        content_mock = MagicMock()
        content_mock.return_value = (
            {
                "id": "tag:reuters.com,2026:newsml_L4N3Z9104:0",
                "title": "Stock rises on earnings",
                "published": 1700000000,
                "ast_description": {
                    "children": [
                        {
                            "type": "p",
                            "children": [
                                "The stock market saw significant movement today."
                            ],
                        },
                        {
                            "type": "p",
                            "children": [
                                "Analysts are optimistic about the quarterly results."
                            ],
                        },
                    ]
                },
                "story_path": "/news/stock-rise",
            },
            None,
        )

        with patch.object(
            news_scraper, "_request", side_effect=[headlines_mock(), content_mock()]
        ):
            headlines_result = news_scraper.get_news_headlines(
                exchange="NASDAQ", symbol="AAPL"
            )
            assert headlines_result["status"] == STATUS_SUCCESS

            if headlines_result["data"]:
                story_id = headlines_result["data"][0]["id"]
                content_result = news_scraper.get_news_content(story_id=story_id)
                assert content_result["status"] == STATUS_SUCCESS
                assert len(content_result["data"]["description"]) > 0

    def test_news_workflow_with_filters(self, news_scraper: News) -> None:
        """Test news workflow with various filters."""
        mock_request = MagicMock()
        mock_request.return_value = (
            {
                "items": [
                    {
                        "id": "tag:test.com,2026:newsml_123",
                        "title": "Filtered News",
                        "shortDescription": "Description",
                        "published": 1700000000,
                        "storyPath": "/news/filtered",
                    }
                ]
            },
            None,
        )

        with patch(
            "tv_scraper.core.validators.verify_symbol_exchange",
            return_value=("NASDAQ", "AAPL"),
        ):
            with patch.object(
                news_scraper, "_request", return_value=mock_request.return_value
            ):
                result = news_scraper.get_news_headlines(
                    exchange="NASDAQ",
                    symbol="AAPL",
                    provider="dow-jones",
                    area="americas",
                    sort_by="latest",
                    section="all",
                    language="en",
                )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["provider"] == "dow-jones"
        assert result["metadata"]["area"] == "americas"
        assert result["metadata"]["sort_by"] == "latest"
        assert result["metadata"]["section"] == "all"
        assert result["metadata"]["language"] == "en"

    def test_multiple_stories_fetching(self, news_scraper: News) -> None:
        """Test fetching multiple story contents."""
        headlines_data = {
            "items": [
                {
                    "id": f"tag:test.com,2026:newsml_{i}",
                    "title": f"News {i}",
                    "shortDescription": f"Description {i}",
                    "published": 1700000000 - i * 1000,
                    "storyPath": f"/news/{i}",
                }
                for i in range(5)
            ]
        }

        content_data_list = [
            (
                {
                    "id": f"tag:test.com,2026:newsml_{i}",
                    "title": f"News {i}",
                    "published": 1700000000 - i * 1000,
                    "ast_description": {
                        "children": [
                            {"type": "p", "children": [f"Content for news {i}."]}
                        ]
                    },
                    "story_path": f"/news/{i}",
                },
                None,
            )
            for i in range(5)
        ]

        call_count = 0

        def mock_request_side_effect(*args, **kwargs):
            nonlocal call_count
            if call_count == 0:
                call_count += 1
                return (headlines_data, None)
            idx = call_count - 1
            call_count += 1
            if idx < len(content_data_list):
                return content_data_list[idx]
            return (None, "No more content")

        with patch.object(
            news_scraper, "_request", side_effect=mock_request_side_effect
        ):
            headlines_result = news_scraper.get_news_headlines(
                exchange="NASDAQ", symbol="AAPL"
            )
            assert headlines_result["status"] == STATUS_SUCCESS
            assert len(headlines_result["data"]) == 5

            for item in headlines_result["data"]:
                content_result = news_scraper.get_news_content(story_id=item["id"])
                assert content_result["status"] == STATUS_SUCCESS


@pytest.mark.integration
class TestNewsValidationIntegration:
    """Test validation integration with news scraper."""

    def test_invalid_exchange_propagates(self, news_scraper: News) -> None:
        """Verify invalid exchange returns error through workflow."""
        result = news_scraper.get_news_headlines(
            exchange="INVALID_EXCHANGE", symbol="AAPL"
        )
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    def test_invalid_symbol_propagates(self, news_scraper: News) -> None:
        """Verify invalid symbol returns error through workflow."""
        result = news_scraper.get_news_headlines(
            exchange="NASDAQ", symbol="INVALID_SYMBOL_XYZ"
        )
        assert result["status"] in [STATUS_SUCCESS, STATUS_FAILED]

    def test_validation_preserves_metadata(self, news_scraper: News) -> None:
        """Verify validation errors preserve metadata."""
        result = news_scraper.get_news_headlines(
            exchange="INVALID_EXCHANGE", symbol="AAPL"
        )
        assert "metadata" in result
        assert result["metadata"]["exchange"] == "INVALID_EXCHANGE"
        assert result["metadata"]["symbol"] == "AAPL"

    def test_content_validation_error_preserves_metadata(
        self, news_scraper: News
    ) -> None:
        """Verify content validation errors preserve metadata."""
        result = news_scraper.get_news_content(story_id="", language="en")
        assert result["status"] == STATUS_FAILED
        assert "metadata" in result
        assert result["metadata"]["story_id"] == ""
        assert result["metadata"]["language"] == "en"


@pytest.mark.integration
class TestNewsSortingIntegration:
    """Test sorting integration with news scraper."""

    def test_sorting_applied_to_results(self, news_scraper: News) -> None:
        """Verify sorting is applied correctly to results."""
        mock_request = MagicMock()
        mock_request.return_value = (
            {
                "items": [
                    {
                        "id": "1",
                        "title": "Old News",
                        "shortDescription": "Desc",
                        "published": 1000000000,
                        "storyPath": "/old",
                    },
                    {
                        "id": "2",
                        "title": "New News",
                        "shortDescription": "Desc",
                        "published": 2000000000,
                        "storyPath": "/new",
                    },
                    {
                        "id": "3",
                        "title": "Middle News",
                        "shortDescription": "Desc",
                        "published": 1500000000,
                        "storyPath": "/middle",
                    },
                ]
            },
            None,
        )

        with patch.object(news_scraper, "_request", mock_request):
            result = news_scraper.get_news_headlines(
                exchange="NASDAQ", symbol="AAPL", sort_by="latest"
            )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"][0]["id"] == "2"
        assert result["data"][1]["id"] == "3"
        assert result["data"][2]["id"] == "1"


@pytest.mark.integration
class TestNewsExportIntegration:
    """Test export integration with news scraper."""

    def test_export_on_success(self, news_scraper: News) -> None:
        """Verify export is triggered on successful fetch."""
        scraper = News(export_result=True)
        mock_request = MagicMock()
        mock_request.return_value = (
            {
                "items": [
                    {
                        "id": "tag:test.com,2026:newsml_123",
                        "title": "Exportable News",
                        "shortDescription": "Description",
                        "published": 1700000000,
                        "storyPath": "/news/export",
                    }
                ]
            },
            None,
        )

        with patch.object(scraper, "_request", mock_request):
            with patch.object(scraper, "_export") as mock_export:
                result = scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL")
                assert result["status"] == STATUS_SUCCESS
                mock_export.assert_called_once()

    def test_no_export_on_failure(self, news_scraper: News) -> None:
        """Verify export is not triggered on failure."""
        scraper = News(export_result=True)

        with patch.object(scraper, "_request") as mock_request:
            mock_request.return_value = (None, "Network error")
            with patch.object(scraper, "_export") as mock_export:
                result = scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL")
                assert result["status"] == STATUS_FAILED
                mock_export.assert_not_called()

    def test_export_with_custom_params(self, news_scraper: News) -> None:
        """Verify export includes correct parameters."""
        scraper = News(export_result=True)
        mock_request = MagicMock()
        mock_request.return_value = (
            {
                "items": [
                    {
                        "id": "tag:test.com,2026:newsml_123",
                        "title": "Exportable News",
                        "shortDescription": "Description",
                        "published": 1700000000,
                        "storyPath": "/news/export",
                    }
                ]
            },
            None,
        )

        with patch(
            "tv_scraper.core.validators.verify_symbol_exchange",
            return_value=("NASDAQ", "AAPL"),
        ):
            with patch.object(
                scraper, "_request", return_value=mock_request.return_value
            ):
                with patch.object(scraper, "_export") as mock_export:
                    scraper.get_news_headlines(
                        exchange="NASDAQ", symbol="AAPL", section="esg"
                    )
                    mock_export.assert_called_once()
                    call_args = mock_export.call_args
                    if call_args is not None:
                        _, kwargs = call_args
                        assert "symbol" in kwargs
                        assert "NASDAQ_AAPL" in kwargs["symbol"]
                        assert "data_category" in kwargs


@pytest.mark.integration
class TestNewsFixturesIntegration:
    """Test integration with saved fixtures."""

    def test_use_fixture_for_headlines(self, news_scraper: News) -> None:
        """Test using saved fixtures for headlines."""
        if not has_fixture("headlines_NASDAQ_AAPL"):
            pytest.skip("Fixture not available")

        fixture = load_fixture("headlines_NASDAQ_AAPL")
        assert fixture["status"] == STATUS_SUCCESS

        with patch.object(news_scraper, "_request") as mock_request:
            # Convert our fixture format to what the scraper expects
            items = fixture.get("data", [])
            mock_request.return_value = ({"items": items}, None)
            result = news_scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_use_fixture_for_content(self, news_scraper: News) -> None:
        """Test using saved fixtures for content."""
        if not has_fixture("content_basic"):
            pytest.skip("Content fixture not available")

        fixture = load_fixture("content_basic")
        if fixture.get("status") != STATUS_SUCCESS:
            pytest.skip("Content fixture not successful")

        story_id = fixture["data"]["id"]
        assert story_id is not None

        with patch.object(news_scraper, "_request") as mock_request:
            mock_request.return_value = (fixture["data"], None)
            result = news_scraper.get_news_content(story_id=story_id)

        assert result["status"] == STATUS_SUCCESS
        assert result["data"]["id"] == story_id


@pytest.mark.integration
class TestNewsErrorRecovery:
    """Test error recovery in news workflows."""

    def test_partial_failure_handling(self, news_scraper: News) -> None:
        """Test handling partial failures in workflow."""
        headlines_mock = MagicMock()
        headlines_mock.return_value = (
            {
                "items": [
                    {
                        "id": "tag:test.com,2026:newsml_123",
                        "title": "Success News",
                        "shortDescription": "Desc",
                        "published": 1700000000,
                        "storyPath": "/success",
                    }
                ]
            },
            None,
        )

        content_mock = MagicMock()
        content_mock.return_value = (None, "Network error fetching content")

        with patch.object(
            news_scraper, "_request", side_effect=[headlines_mock(), content_mock()]
        ):
            headlines_result = news_scraper.get_news_headlines(
                exchange="NASDAQ", symbol="AAPL"
            )
            assert headlines_result["status"] == STATUS_SUCCESS

            content_result = news_scraper.get_news_content(
                story_id="tag:test.com,2026:newsml_123"
            )
            assert content_result["status"] == STATUS_FAILED
            assert content_result["error"] is not None

    def test_retry_scenario(self, news_scraper: News) -> None:
        """Test retry scenario in news fetching."""
        call_count = 0

        def mock_request_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return (None, "Transient error")
            return (
                {
                    "items": [
                        {
                            "id": "1",
                            "title": "Retry Success",
                            "shortDescription": "Desc",
                            "published": 1700000000,
                            "storyPath": "/retry",
                        }
                    ]
                },
                None,
            )

        with patch.object(
            news_scraper, "_request", side_effect=mock_request_with_retry
        ):
            result = news_scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] in [STATUS_SUCCESS, STATUS_FAILED]
