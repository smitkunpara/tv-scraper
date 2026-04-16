"""Ideas scraper mock tests.

Tests parsing and handling of saved API responses using fixtures.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.social.ideas import Ideas


def load_from_fixture(name: str) -> dict:
    """Load fixture by name."""
    fixtures_dir = Path(__file__).parent.parent / "fixtures" / "ideas"
    filepath = fixtures_dir / f"{name}.json"
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    pytest.skip(f"Fixture not found: {name}")


@pytest.fixture
def mock_ideas_basic() -> dict:
    """Load basic ideas fixture."""
    return load_from_fixture("basic")


@pytest.fixture
def mock_ideas_popular() -> dict:
    """Load popular sort ideas fixture."""
    return load_from_fixture("popular")


@pytest.fixture
def mock_ideas_recent() -> dict:
    """Load recent sort ideas fixture."""
    return load_from_fixture("recent")


@pytest.fixture
def mock_ideas_multi_page() -> dict:
    """Load multi-page ideas fixture."""
    return load_from_fixture("multi_page")


@pytest.fixture
def mock_ideas_crypto() -> dict:
    """Load crypto ideas fixture."""
    return load_from_fixture("crypto")


@pytest.fixture
def sample_raw_idea() -> dict:
    """Sample raw idea from API."""
    return {
        "name": "Bullish ABC Pattern on AAPL",
        "description": "Potential long setup...",
        "symbol": {"logo_urls": ["https://tradingview.com/logo.png"]},
        "chart_url": "https://tradingview.com/chart/abc123",
        "comments_count": 42,
        "views_count": 1337,
        "user": {"username": "trader123"},
        "likes_count": 99,
        "date_timestamp": 1710000000,
    }


class TestIdeasMapping:
    """Test _map_idea static method."""

    def test_map_idea_full_data(self, sample_raw_idea: dict) -> None:
        """Verify mapping of complete idea data."""
        result = Ideas._map_idea(sample_raw_idea)
        assert result["title"] == "Bullish ABC Pattern on AAPL"
        assert result["description"] == "Potential long setup..."
        assert result["preview_image"] == ["https://tradingview.com/logo.png"]
        assert result["chart_url"] == "https://tradingview.com/chart/abc123"
        assert result["comments_count"] == 42
        assert result["views_count"] == 1337
        assert result["author"] == "trader123"
        assert result["likes_count"] == 99
        assert result["timestamp"] == 1710000000

    def test_map_idea_missing_fields(self) -> None:
        """Verify handling of missing fields with defaults."""
        minimal_idea: dict = {}
        result = Ideas._map_idea(minimal_idea)
        assert result["title"] == ""
        assert result["description"] == ""
        assert result["preview_image"] == []
        assert result["chart_url"] == ""
        assert result["comments_count"] == 0
        assert result["views_count"] == 0
        assert result["author"] == ""
        assert result["likes_count"] == 0
        assert result["timestamp"] == 0

    def test_map_idea_partial_data(self) -> None:
        """Verify handling of partial data."""
        partial_idea: dict = {
            "name": "Test Idea",
            "user": {"username": "testuser"},
        }
        result = Ideas._map_idea(partial_idea)
        assert result["title"] == "Test Idea"
        assert result["author"] == "testuser"
        assert result["comments_count"] == 0


class TestIdeasResponseParsing:
    """Test response parsing logic."""

    def test_parse_successful_response(self, mock_ideas_basic: dict) -> None:
        """Verify successful response structure."""
        assert mock_ideas_basic["status"] == STATUS_SUCCESS
        assert "data" in mock_ideas_basic
        assert "metadata" in mock_ideas_basic
        assert "error" in mock_ideas_basic

    def test_parse_multi_page_metadata(self, mock_ideas_multi_page: dict) -> None:
        """Verify multi-page metadata."""
        assert mock_ideas_multi_page["status"] == STATUS_SUCCESS
        assert mock_ideas_multi_page["metadata"]["pages"] == 2

    def test_parse_error_response(self) -> None:
        """Verify error response structure."""
        error_response = {
            "status": STATUS_FAILED,
            "data": None,
            "metadata": {"exchange": "INVALID", "symbol": "TEST"},
            "error": "Invalid exchange",
        }
        assert error_response["status"] == STATUS_FAILED
        assert error_response["error"] is not None


class TestIdeasMockedRequests:
    """Test ideas scraper with mocked HTTP requests."""

    @patch.object(Ideas, "_request")
    def test_scrape_page_success(self, mock_request: MagicMock) -> None:
        """Verify single page scraping with mock."""
        mock_request.return_value = (
            {
                "data": {
                    "ideas": {
                        "data": {
                            "items": [
                                {"name": "Idea 1", "user": {"username": "user1"}},
                                {"name": "Idea 2", "user": {"username": "user2"}},
                            ]
                        }
                    }
                }
            },
            None,
        )

        scraper = Ideas()
        ideas, error = scraper._scrape_page("NASDAQ-AAPL", 1, "popular")

        assert error is None
        assert ideas is not None
        assert len(ideas) == 2
        assert ideas[0]["title"] == "Idea 1"
        assert ideas[1]["title"] == "Idea 2"

    @patch.object(Ideas, "_request")
    def test_scrape_page_empty_items(self, mock_request: MagicMock) -> None:
        """Verify handling of empty items list."""
        mock_request.return_value = ({"data": {"ideas": {"data": {"items": []}}}}, None)

        scraper = Ideas()
        ideas, error = scraper._scrape_page("NASDAQ-AAPL", 1, "popular")

        assert error is None
        assert ideas == []

    @patch.object(Ideas, "_request")
    def test_scrape_page_network_error(self, mock_request: MagicMock) -> None:
        """Verify network error handling."""
        mock_request.return_value = (None, "Network error: Connection refused")

        scraper = Ideas()
        ideas, error = scraper._scrape_page("NASDAQ-AAPL", 1, "popular")

        assert ideas is None
        assert error is not None
        assert "Network error" in error

    @patch.object(Ideas, "_request")
    def test_scrape_page_http_error(self, mock_request: MagicMock) -> None:
        """Verify HTTP error handling."""
        mock_request.return_value = (None, "Network error: 404 Client Error")

        scraper = Ideas()
        ideas, error = scraper._scrape_page("NASDAQ-AAPL", 1, "popular")

        assert ideas is None
        assert error is not None

    @patch.object(Ideas, "_request")
    def test_scrape_page_captcha(self, mock_request: MagicMock) -> None:
        """Verify captcha detection."""
        mock_request.return_value = (None, "TradingView requested a captcha challenge.")

        scraper = Ideas()
        ideas, error = scraper._scrape_page("NASDAQ-AAPL", 1, "popular")

        assert ideas is None
        assert error is not None
        assert "captcha" in error.lower()


class TestIdeasValidation:
    """Test validation logic."""

    def test_invalid_start_page(self) -> None:
        """Verify validation of start_page < 1."""
        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="NASDAQ", symbol="AAPL", start_page=0, end_page=1
        )
        assert result["status"] == STATUS_FAILED
        assert "start_page must be >= 1" in result["error"]

    def test_end_page_less_than_start_page(self) -> None:
        """Verify validation of end_page < start_page."""
        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="NASDAQ", symbol="AAPL", start_page=3, end_page=1
        )
        assert result["status"] == STATUS_FAILED
        assert "end_page" in result["error"] and "start_page" in result["error"]

    def test_invalid_sort_by(self) -> None:
        """Verify validation of invalid sort_by value."""
        scraper = Ideas()
        result = scraper.get_ideas(exchange="NASDAQ", symbol="AAPL", sort_by="invalid")
        assert result["status"] == STATUS_FAILED
        assert "Invalid value" in result["error"]


class TestIdeasResponseEnvelope:
    """Test standardized response envelope."""

    def test_success_response_structure(self, mock_ideas_basic: dict) -> None:
        """Verify success response has all required fields."""
        result = mock_ideas_basic
        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["error"] is None

    def test_metadata_contains_params(self, mock_ideas_basic: dict) -> None:
        """Verify metadata contains request parameters."""
        meta = mock_ideas_basic["metadata"]
        assert "exchange" in meta
        assert "symbol" in meta
        assert "start_page" in meta
        assert "end_page" in meta
        assert "sort_by" in meta
        assert "total" in meta

    def test_data_is_list(self, mock_ideas_basic: dict) -> None:
        """Verify data field is a list."""
        assert isinstance(mock_ideas_basic["data"], list)

    def test_data_idea_structure(self, mock_ideas_basic: dict) -> None:
        """Verify each idea in data has expected structure."""
        if mock_ideas_basic["data"]:
            idea = mock_ideas_basic["data"][0]
            expected_keys = {
                "title",
                "description",
                "preview_image",
                "chart_url",
                "comments_count",
                "views_count",
                "author",
                "likes_count",
                "timestamp",
            }
            assert expected_keys.issubset(set(idea.keys()))


class TestIdeasConfiguration:
    """Test scraper configuration options."""

    def test_custom_timeout(self) -> None:
        """Verify custom timeout is accepted."""
        scraper = Ideas(timeout=30)
        assert scraper.timeout == 30

    def test_custom_max_workers(self) -> None:
        """Verify custom max_workers is accepted."""
        scraper = Ideas(max_workers=5)
        assert scraper._max_workers == 5

    def test_max_workers_minimum(self) -> None:
        """Verify max_workers minimum is enforced."""
        scraper = Ideas(max_workers=0)
        assert scraper._max_workers == 1

    def test_export_result_enabled(self) -> None:
        """Verify export_result option."""
        scraper = Ideas(export="json")
        assert scraper.export_result is True
        assert scraper.export_type == "json"

    def test_cookie_parameter(self) -> None:
        """Verify cookie parameter is accepted."""
        scraper = Ideas(cookie="test_cookie_123")
        assert scraper.cookie == "test_cookie_123"
