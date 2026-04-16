"""Mock tests for Minds scraper.

Tests using saved JSON fixtures from live API tests.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.social.minds import Minds

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "minds"


def load_fixture(name: str) -> dict:
    """Load a fixture file for testing."""
    filepath = FIXTURES_DIR / f"{name}.json"
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    pytest.skip(f"Fixture not found: {name}.json")


class TestMockMindsFromFixtures:
    """Test minds scraper using saved fixtures."""

    def test_from_basic_fixture(self) -> None:
        """Test parsing from basic fixture."""
        result = load_fixture("basic")
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0
        mind = result["data"][0]
        assert "text" in mind
        assert "url" in mind
        assert "author" in mind
        assert "created" in mind
        assert "total_likes" in mind
        assert "total_comments" in mind

    def test_from_limit_10_fixture(self) -> None:
        """Test parsing from limit=10 fixture."""
        result = load_fixture("limit_10")
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) <= 10
        assert result["metadata"]["limit"] == 10

    def test_from_limit_50_fixture(self) -> None:
        """Test parsing from limit=50 fixture."""
        result = load_fixture("limit_50")
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) <= 50
        assert result["metadata"]["limit"] == 50

    def test_mind_author_structure(self) -> None:
        """Test author structure in mind items."""
        result = load_fixture("basic")
        mind = result["data"][0]
        author = mind["author"]
        assert "username" in author
        assert "profile_url" in author
        assert "is_broker" in author
        assert isinstance(author["is_broker"], bool)

    def test_mind_url_format(self) -> None:
        """Test URL format in mind items."""
        result = load_fixture("basic")
        for mind in result["data"]:
            if mind["url"]:
                assert mind["url"].startswith("/") or mind["url"].startswith("http")

    def test_mind_created_format(self) -> None:
        """Test created timestamp format in mind items."""
        result = load_fixture("basic")
        for mind in result["data"]:
            if mind["created"]:
                assert " " in mind["created"]
                parts = mind["created"].split(" ")
                assert len(parts) == 2
                date_part = parts[0]
                time_part = parts[1]
                assert len(date_part.split("-")) == 3
                assert len(time_part.split(":")) == 3


class TestMockMindsDataValidation:
    """Test data validation using mocked responses."""

    def _mock_request_success(self, results: list, next_cursor: str | None = None):
        """Create a mock request that returns the given results."""
        mock_response = MagicMock()
        response_data = {"results": results}
        if next_cursor:
            response_data["next"] = (
                f"https://www.tradingview.com/api/v1/minds/?c={next_cursor}&other=param"
            )
        else:
            response_data["next"] = ""
        response_data["meta"] = {
            "symbols_info": {"NASDAQ:AAPL": {"name": "Apple Inc", "type": "stock"}}
        }
        mock_response.json.return_value = response_data
        return mock_response

    @patch("tv_scraper.scrapers.social.minds.Minds._verify_symbol_exchange")
    def test_success_response_structure(self, mock_verify) -> None:
        """Test successful response has correct structure."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        scraper = Minds()

        sample_mind = {
            "text": "Test mind text",
            "url": "/symbols/NASDAQ-AAPL/minds/123/",
            "author": {
                "username": "testuser",
                "uri": "/users/testuser/",
                "is_broker": False,
            },
            "created": "2024-01-15T10:30:00Z",
            "total_likes": 5,
            "total_comments": 2,
        }

        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = (
                self._mock_request_success([sample_mind]).json(),
                None,
            )
            result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["error"] is None

    @patch("tv_scraper.scrapers.social.minds.Minds._verify_symbol_exchange")
    def test_empty_results(self, mock_verify) -> None:
        """Test handling of empty results."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        scraper = Minds()

        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = ({"results": [], "next": "", "meta": {}}, None)
            result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 0

    @patch("tv_scraper.scrapers.social.minds.Minds._verify_symbol_exchange")
    def test_limit_truncation(self, mock_verify) -> None:
        """Test that limit properly truncates results."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        scraper = Minds()

        minds = [
            {
                "text": f"Mind {i}",
                "url": f"/mind/{i}",
                "author": {},
                "created": "",
                "total_likes": 0,
                "total_comments": 0,
            }
            for i in range(20)
        ]

        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = ({"results": minds, "next": "", "meta": {}}, None)
            result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL", limit=5)

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 5

    @patch("tv_scraper.scrapers.social.minds.Minds._verify_symbol_exchange")
    def test_pagination_cursor_extraction(self, mock_verify) -> None:
        """Test cursor extraction from next URL."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        scraper = Minds()

        page1_results = [
            {
                "text": "Page 1",
                "url": "/1",
                "author": {},
                "created": "",
                "total_likes": 0,
                "total_comments": 0,
            }
        ]
        page2_results = [
            {
                "text": "Page 2",
                "url": "/2",
                "author": {},
                "created": "",
                "total_likes": 0,
                "total_comments": 0,
            }
        ]

        call_count = 0

        def mock_request_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return (
                    {
                        "results": page1_results,
                        "next": "https://www.tradingview.com/api/v1/minds/?c=page2_cursor&foo=bar",
                        "meta": {},
                    },
                    None,
                )
            else:
                return ({"results": page2_results, "next": "", "meta": {}}, None)

        with patch.object(scraper, "_request", side_effect=mock_request_fn):
            result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 2
        assert result["metadata"]["pages"] == 2

    @patch("tv_scraper.scrapers.social.minds.Minds._verify_symbol_exchange")
    def test_error_response(self, mock_verify) -> None:
        """Test error response structure."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        scraper = Minds()

        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = (None, "Network error: 500")
            result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None
        assert "Network error" in result["error"]


class TestMockMindsAuthorParsing:
    """Test author parsing from different formats."""

    def _make_mock_mind(self, uri: str, is_broker: bool = False) -> dict:
        """Create a mock mind item with specified author URI."""
        return {
            "text": "Test",
            "url": "/test",
            "author": {
                "username": "testuser",
                "uri": uri,
                "is_broker": is_broker,
            },
            "created": "2024-01-15T10:30:00Z",
            "total_likes": 0,
            "total_comments": 0,
        }

    def test_author_uri_without_scheme(self) -> None:
        """Test that URIs without http:// are prefixed correctly."""
        scraper = Minds()
        mind = self._make_mock_mind("/users/testuser/")
        parsed = scraper._parse_mind(mind)
        assert (
            parsed["author"]["profile_url"]
            == "https://www.tradingview.com/users/testuser/"
        )

    def test_author_uri_with_scheme(self) -> None:
        """Test that URIs with http:// are kept as-is."""
        scraper = Minds()
        mind = self._make_mock_mind("https://www.tradingview.com/users/testuser/")
        parsed = scraper._parse_mind(mind)
        assert (
            parsed["author"]["profile_url"]
            == "https://www.tradingview.com/users/testuser/"
        )

    def test_author_broker_flag_true(self) -> None:
        """Test broker flag when true."""
        scraper = Minds()
        mind = self._make_mock_mind("/users/broker/", is_broker=True)
        parsed = scraper._parse_mind(mind)
        assert parsed["author"]["is_broker"] is True

    def test_author_broker_flag_false(self) -> None:
        """Test broker flag when false."""
        scraper = Minds()
        mind = self._make_mock_mind("/users/user/", is_broker=False)
        parsed = scraper._parse_mind(mind)
        assert parsed["author"]["is_broker"] is False

    def test_author_broker_flag_missing(self) -> None:
        """Test broker flag defaults to False when missing."""
        scraper = Minds()
        mind = {
            "text": "Test",
            "url": "/test",
            "author": {
                "username": "testuser",
                "uri": "/users/testuser/",
            },
            "created": "2024-01-15T10:30:00Z",
            "total_likes": 0,
            "total_comments": 0,
        }
        parsed = scraper._parse_mind(mind)
        assert parsed["author"]["is_broker"] is False


class TestMockMindsTimestampParsing:
    """Test timestamp parsing from different formats."""

    def test_iso_format_with_z(self) -> None:
        """Test parsing ISO format with Z suffix."""
        scraper = Minds()
        mind = {
            "text": "Test",
            "url": "/test",
            "author": {},
            "created": "2024-01-15T10:30:00Z",
            "total_likes": 0,
            "total_comments": 0,
        }
        parsed = scraper._parse_mind(mind)
        assert parsed["created"] == "2024-01-15 10:30:00"

    def test_iso_format_with_offset(self) -> None:
        """Test parsing ISO format with +00:00 offset."""
        scraper = Minds()
        mind = {
            "text": "Test",
            "url": "/test",
            "author": {},
            "created": "2024-01-15T10:30:00+00:00",
            "total_likes": 0,
            "total_comments": 0,
        }
        parsed = scraper._parse_mind(mind)
        assert parsed["created"] == "2024-01-15 10:30:00"

    def test_empty_created(self) -> None:
        """Test handling of empty created field."""
        scraper = Minds()
        mind = {
            "text": "Test",
            "url": "/test",
            "author": {},
            "created": "",
            "total_likes": 0,
            "total_comments": 0,
        }
        parsed = scraper._parse_mind(mind)
        assert parsed["created"] == ""

    def test_invalid_date_format(self) -> None:
        """Test handling of invalid date format."""
        scraper = Minds()
        mind = {
            "text": "Test",
            "url": "/test",
            "author": {},
            "created": "not-a-date",
            "total_likes": 0,
            "total_comments": 0,
        }
        parsed = scraper._parse_mind(mind)
        assert parsed["created"] == "not-a-date"


class TestMockMindsMissingFields:
    """Test handling of missing fields in API response."""

    def test_missing_text(self) -> None:
        """Test handling of missing text field."""
        scraper = Minds()
        mind = {
            "url": "/test",
            "author": {},
            "created": "",
            "total_likes": 0,
            "total_comments": 0,
        }
        parsed = scraper._parse_mind(mind)
        assert parsed["text"] == ""

    def test_missing_url(self) -> None:
        """Test handling of missing URL field."""
        scraper = Minds()
        mind = {
            "text": "Test",
            "author": {},
            "created": "",
            "total_likes": 0,
            "total_comments": 0,
        }
        parsed = scraper._parse_mind(mind)
        assert parsed["url"] == ""

    def test_missing_author(self) -> None:
        """Test handling of missing author field."""
        scraper = Minds()
        mind = {
            "text": "Test",
            "url": "/test",
            "created": "",
            "total_likes": 0,
            "total_comments": 0,
        }
        parsed = scraper._parse_mind(mind)
        assert parsed["author"]["username"] is None

    def test_missing_likes_and_comments(self) -> None:
        """Test handling of missing likes and comments fields."""
        scraper = Minds()
        mind = {
            "text": "Test",
            "url": "/test",
            "author": {},
            "created": "",
        }
        parsed = scraper._parse_mind(mind)
        assert parsed["total_likes"] == 0
        assert parsed["total_comments"] == 0
