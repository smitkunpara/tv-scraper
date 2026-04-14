"""Ideas scraper unit tests.

Isolated tests for Ideas class methods without network calls.
"""

from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.social.ideas import ALLOWED_SORT_VALUES, Ideas


class TestIdeasInstantiation:
    """Test Ideas class instantiation."""

    def test_default_instantiation(self) -> None:
        """Verify default initialization."""
        scraper = Ideas()
        assert scraper.timeout == 10
        assert scraper.export_result is False
        assert scraper.export_type == "json"
        assert scraper._max_workers == 3

    def test_custom_timeout(self) -> None:
        """Verify custom timeout initialization."""
        scraper = Ideas(timeout=30)
        assert scraper.timeout == 30

    def test_custom_max_workers(self) -> None:
        """Verify custom max_workers initialization."""
        scraper = Ideas(max_workers=5)
        assert scraper._max_workers == 5

    def test_max_workers_clamped_to_minimum(self) -> None:
        """Verify max_workers cannot be less than 1."""
        scraper = Ideas(max_workers=0)
        assert scraper._max_workers == 1

    def test_export_options(self) -> None:
        """Verify export configuration."""
        scraper = Ideas(export="csv")
        assert scraper.export_result is True
        assert scraper.export_type == "csv"

    def test_cookie_initialization(self) -> None:
        """Verify cookie initialization."""
        scraper = Ideas(cookie="session_id=abc123")
        assert scraper.cookie == "session_id=abc123"

    def test_invalid_export_type_raises(self) -> None:
        """Verify invalid export_type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid export"):
            Ideas(export="invalid")

    def test_invalid_timeout_raises(self) -> None:
        """Verify invalid timeout raises ValueError."""
        with pytest.raises(ValueError, match="Timeout must be"):
            Ideas(timeout=0)
        with pytest.raises(ValueError, match="Timeout must be"):
            Ideas(timeout=500)


class TestIdeasMapIdea:
    """Test _map_idea static method."""

    def test_full_data_mapping(self) -> None:
        """Verify complete data mapping."""
        raw = {
            "name": "Test Title",
            "description": "Test description",
            "symbol": {"logo_urls": ["url1", "url2"]},
            "chart_url": "/chart/abc",
            "comments_count": 10,
            "views_count": 100,
            "user": {"username": "testuser"},
            "likes_count": 50,
            "date_timestamp": 1234567890,
        }
        result = Ideas._map_idea(raw)
        assert result["title"] == "Test Title"
        assert result["description"] == "Test description"
        assert result["preview_image"] == ["url1", "url2"]
        assert result["chart_url"] == "/chart/abc"
        assert result["comments_count"] == 10
        assert result["views_count"] == 100
        assert result["author"] == "testuser"
        assert result["likes_count"] == 50
        assert result["timestamp"] == 1234567890

    def test_empty_data_mapping(self) -> None:
        """Verify default values for empty data."""
        result = Ideas._map_idea({})
        assert result["title"] == ""
        assert result["description"] == ""
        assert result["preview_image"] == []
        assert result["chart_url"] == ""
        assert result["comments_count"] == 0
        assert result["views_count"] == 0
        assert result["author"] == ""
        assert result["likes_count"] == 0
        assert result["timestamp"] == 0

    def test_partial_data_mapping(self) -> None:
        """Verify partial data handling."""
        result = Ideas._map_idea({"name": "Only Title"})
        assert result["title"] == "Only Title"
        assert result["description"] == ""
        assert result["author"] == ""

    def test_none_nested_dict_handled(self) -> None:
        """Verify missing nested dictionary is handled gracefully."""
        raw = {
            "name": "Test",
        }
        result = Ideas._map_idea(raw)
        assert result["preview_image"] == []
        assert result["title"] == "Test"

    def test_missing_nested_keys(self) -> None:
        """Verify missing nested dictionary keys handled."""
        raw = {
            "name": "Test",
            "symbol": {},
            "user": {},
        }
        result = Ideas._map_idea(raw)
        assert result["preview_image"] == []
        assert result["author"] == ""


class TestIdeasScrapePage:
    """Test _scrape_page method."""

    @patch.object(Ideas, "_request")
    def test_first_page_url_construction(self, mock_request: MagicMock) -> None:
        """Verify correct URL for first page."""
        mock_request.return_value = ({"data": {"ideas": {"data": {"items": []}}}}, None)

        scraper = Ideas()
        scraper._scrape_page("NASDAQ-AAPL", 1, "popular")

        call_args = mock_request.call_args
        url = call_args[0][1]
        assert "/page-1/" not in url
        params = call_args[1]["params"]
        assert params.get("component-data-only") == "1"

    @patch.object(Ideas, "_request")
    def test_second_page_url_construction(self, mock_request: MagicMock) -> None:
        """Verify correct URL for page > 1."""
        mock_request.return_value = ({"data": {"ideas": {"data": {"items": []}}}}, None)

        scraper = Ideas()
        scraper._scrape_page("NASDAQ-AAPL", 2, "popular")

        call_args = mock_request.call_args
        url = call_args[0][1]
        assert "/page-2/" in url

    @patch.object(Ideas, "_request")
    def test_recent_sort_adds_param(self, mock_request: MagicMock) -> None:
        """Verify 'sort=recent' param for recent sort."""
        mock_request.return_value = ({"data": {"ideas": {"data": {"items": []}}}}, None)

        scraper = Ideas()
        scraper._scrape_page("NASDAQ-AAPL", 1, "recent")

        call_args = mock_request.call_args
        params = call_args[1]["params"]
        assert "sort" in params
        assert params["sort"] == "recent"

    @patch.object(Ideas, "_request")
    def test_popular_sort_no_extra_param(self, mock_request: MagicMock) -> None:
        """Verify 'sort' param not added for popular sort."""
        mock_request.return_value = ({"data": {"ideas": {"data": {"items": []}}}}, None)

        scraper = Ideas()
        scraper._scrape_page("NASDAQ-AAPL", 1, "popular")

        call_args = mock_request.call_args
        params = call_args[1]["params"]
        assert "sort" not in params

    @patch.object(Ideas, "_request")
    def test_empty_items_returns_empty_list(self, mock_request: MagicMock) -> None:
        """Verify empty items list returns empty list."""
        mock_request.return_value = ({"data": {"ideas": {"data": {"items": []}}}}, None)

        scraper = Ideas()
        ideas, error = scraper._scrape_page("NASDAQ-AAPL", 1, "popular")

        assert ideas == []
        assert error is None

    @patch.object(Ideas, "_request")
    def test_malformed_json_returns_error(self, mock_request: MagicMock) -> None:
        """Verify malformed JSON returns error."""
        mock_request.return_value = (
            None,
            "Failed to parse API response: Expecting value",
        )

        scraper = Ideas()
        ideas, error = scraper._scrape_page("NASDAQ-AAPL", 1, "popular")

        assert ideas is None
        assert error is not None
        assert "parse" in error.lower()

    @patch.object(Ideas, "_request")
    def test_missing_nested_data(self, mock_request: MagicMock) -> None:
        """Verify missing nested data structures handled."""
        mock_request.return_value = ({"data": {}}, None)

        scraper = Ideas()
        ideas, error = scraper._scrape_page("NASDAQ-AAPL", 1, "popular")

        assert ideas == []
        assert error is None

    @patch.object(Ideas, "_request")
    def test_network_error(self, mock_request: MagicMock) -> None:
        """Verify network errors handled."""
        mock_request.return_value = (None, "Network error: Connection refused")

        scraper = Ideas()
        ideas, error = scraper._scrape_page("NASDAQ-AAPL", 1, "popular")

        assert ideas is None
        assert error is not None
        assert "Network error" in error


class TestIdeasGetIdeas:
    """Test get_ideas method."""

    @patch.object(Ideas, "_scrape_page")
    def test_validation_invalid_start_page(self, mock_scrape: MagicMock) -> None:
        """Verify start_page < 1 is rejected."""
        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="NASDAQ", symbol="AAPL", start_page=0, end_page=1
        )
        assert result["status"] == STATUS_FAILED
        assert "start_page must be >= 1" in result["error"]
        mock_scrape.assert_not_called()

    @patch.object(Ideas, "_scrape_page")
    def test_validation_end_page_before_start(self, mock_scrape: MagicMock) -> None:
        """Verify end_page < start_page is rejected."""
        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="NASDAQ", symbol="AAPL", start_page=5, end_page=3
        )
        assert result["status"] == STATUS_FAILED
        assert "end_page" in result["error"]
        mock_scrape.assert_not_called()

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch.object(Ideas, "_scrape_page")
    def test_validation_invalid_exchange(
        self, mock_scrape: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Verify invalid exchange is rejected."""
        from tv_scraper.core.exceptions import ValidationError

        mock_verify.side_effect = ValidationError("Invalid exchange")

        scraper = Ideas()
        result = scraper.get_ideas(exchange="INVALID", symbol="AAPL")
        assert result["status"] == STATUS_FAILED
        mock_scrape.assert_not_called()

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch.object(Ideas, "_scrape_page")
    def test_validation_invalid_symbol(
        self, mock_scrape: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Verify invalid symbol is rejected."""
        from tv_scraper.core.exceptions import ValidationError

        mock_verify.side_effect = ValidationError("Invalid symbol")

        scraper = Ideas()
        result = scraper.get_ideas(exchange="NASDAQ", symbol="INVALID")
        assert result["status"] == STATUS_FAILED
        mock_scrape.assert_not_called()

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch.object(Ideas, "_scrape_page")
    def test_validation_invalid_sort_by(
        self, mock_scrape: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Verify invalid sort_by is rejected."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        scraper = Ideas()
        result = scraper.get_ideas(exchange="NASDAQ", symbol="AAPL", sort_by="bad")
        assert result["status"] == STATUS_FAILED
        assert "sort_by" in result["error"]

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch.object(Ideas, "_scrape_page")
    def test_successful_single_page(
        self, mock_scrape: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Verify successful single page fetch."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_scrape.return_value = (
            [
                {"title": "Idea 1"},
                {"title": "Idea 2"},
            ],
            None,
        )

        scraper = Ideas()
        result = scraper.get_ideas(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 2
        assert result["metadata"]["total"] == 2
        assert result["metadata"]["pages"] == 1

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch.object(Ideas, "_scrape_page")
    def test_multi_page_fetching(
        self, mock_scrape: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Verify multi-page fetching."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        def scrape_side_effect(url_slug: str, page: int, sort_by: str):
            if page == 1:
                return ([{"title": "Page1-Idea"}], None)
            return ([{"title": "Page2-Idea"}], None)

        mock_scrape.side_effect = scrape_side_effect

        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="NASDAQ", symbol="AAPL", start_page=1, end_page=2
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["total"] == 2
        assert result["metadata"]["pages"] == 2

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch.object(Ideas, "_scrape_page")
    def test_partial_page_failure(
        self, mock_scrape: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Verify handling when some pages fail."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        def scrape_side_effect(url_slug: str, page: int, sort_by: str):
            if page == 1:
                return ([{"title": "Success"}], None)
            return (None, "Network error on page 2")

        mock_scrape.side_effect = scrape_side_effect

        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="NASDAQ", symbol="AAPL", start_page=1, end_page=2
        )

        assert result["status"] == STATUS_FAILED
        assert "Failed pages" in result["error"]
        assert "Network error on page 2" in result["error"]

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch.object(Ideas, "_scrape_page")
    def test_all_pages_fail(
        self, mock_scrape: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Verify handling when all pages fail."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_scrape.return_value = (None, "Connection refused")

        scraper = Ideas()
        result = scraper.get_ideas(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None


class TestIdeasExport:
    """Test export functionality."""

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch.object(Ideas, "_scrape_page")
    def test_export_enabled(
        self, mock_scrape: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Verify export is triggered when enabled."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_scrape.return_value = ([{"title": "Idea"}], None)

        scraper = Ideas(export="json")
        with patch.object(scraper, "_export") as mock_export:
            scraper.get_ideas(exchange="NASDAQ", symbol="AAPL")
            mock_export.assert_called_once()

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch.object(Ideas, "_scrape_page")
    def test_export_disabled(
        self, mock_scrape: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Verify export is not triggered when disabled."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_scrape.return_value = ([{"title": "Idea"}], None)

        scraper = Ideas(export=None)
        with patch.object(scraper, "_export") as mock_export:
            scraper.get_ideas(exchange="NASDAQ", symbol="AAPL")
            mock_export.assert_not_called()


class TestIdeasConstants:
    """Test module constants."""

    def test_allowed_sort_values(self) -> None:
        """Verify allowed sort values."""
        assert "popular" in ALLOWED_SORT_VALUES
        assert "recent" in ALLOWED_SORT_VALUES
        assert len(ALLOWED_SORT_VALUES) == 2
