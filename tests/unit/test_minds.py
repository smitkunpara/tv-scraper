"""Unit tests for Minds scraper.

Isolated tests with mocking - no actual HTTP connections.
"""

from unittest.mock import patch

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.core.exceptions import ValidationError
from tv_scraper.scrapers.social.minds import MAX_PAGES, Minds


class TestMindsInit:
    """Test Minds scraper initialization."""

    def test_default_init(self) -> None:
        """Test default initialization."""
        scraper = Minds()
        assert scraper.export_result is False
        assert scraper.export_type == "json"
        assert scraper.timeout == 10

    def test_custom_init(self) -> None:
        """Test custom initialization."""
        scraper = Minds(export_result=True, export_type="csv", timeout=30)
        assert scraper.export_result is True
        assert scraper.export_type == "csv"
        assert scraper.timeout == 30

    def test_inherits_from_base_scraper(self) -> None:
        """Verify Minds inherits BaseScraper methods."""
        scraper = Minds()
        assert hasattr(scraper, "_success_response")
        assert hasattr(scraper, "_error_response")
        assert hasattr(scraper, "_request")
        assert hasattr(scraper, "_export")


class TestParseMind:
    """Test _parse_mind method."""

    def test_parse_mind_basic(self) -> None:
        """Test basic parsing of a mind item."""
        scraper = Minds()
        item = {
            "text": "Test idea about AAPL",
            "url": "/symbols/NASDAQ-AAPL/minds/123/",
            "author": {
                "username": "trader123",
                "uri": "/users/trader123/",
                "is_broker": False,
            },
            "created": "2024-03-15T14:30:00Z",
            "total_likes": 42,
            "total_comments": 7,
        }
        result = scraper._parse_mind(item)

        assert result["text"] == "Test idea about AAPL"
        assert result["url"] == "/symbols/NASDAQ-AAPL/minds/123/"
        assert result["author"]["username"] == "trader123"
        assert result["author"]["is_broker"] is False
        assert result["created"] == "2024-03-15 14:30:00"
        assert result["total_likes"] == 42
        assert result["total_comments"] == 7

    def test_parse_mind_with_full_url(self) -> None:
        """Test parsing when author URI already has full URL."""
        scraper = Minds()
        item = {
            "text": "Test",
            "url": "/test",
            "author": {
                "username": "user",
                "uri": "https://www.tradingview.com/users/user/",
                "is_broker": True,
            },
            "created": "2024-01-01T00:00:00Z",
            "total_likes": 0,
            "total_comments": 0,
        }
        result = scraper._parse_mind(item)
        assert (
            result["author"]["profile_url"] == "https://www.tradingview.com/users/user/"
        )

    def test_parse_mind_date_formats(self) -> None:
        """Test various date format parsing."""
        scraper = Minds()
        test_cases = [
            ("2024-06-15T10:30:00Z", "2024-06-15 10:30:00"),
            ("2024-12-31T23:59:59+00:00", "2024-12-31 23:59:59"),
            ("2024-01-01T00:00:00.000Z", "2024-01-01 00:00:00"),
        ]
        for created_input, expected_output in test_cases:
            item = {
                "text": "Test",
                "url": "/test",
                "author": {},
                "created": created_input,
                "total_likes": 0,
                "total_comments": 0,
            }
            result = scraper._parse_mind(item)
            assert result["created"] == expected_output


class TestGetMindsValidation:
    """Test validation in get_minds."""

    def test_invalid_exchange_raises_validation_error(self) -> None:
        """Test that invalid exchange returns error response."""
        scraper = Minds()
        result = scraper.get_minds(exchange="INVALID", symbol="AAPL")
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None
        assert "INVALID" in result["error"]

    def test_symbol_not_found_returns_error(self) -> None:
        """Test that non-existent symbol returns error response."""
        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="NOTEXIST999XYZ")
        assert result["status"] == STATUS_FAILED


class TestGetMindsSuccess:
    """Test successful get_minds calls with mocking."""

    def _make_mock_api_response(
        self,
        results: list[dict],
        next_cursor: str | None = None,
        symbol_info: dict | None = None,
    ) -> dict:
        """Create a mock API response."""
        default_symbol_info = {"name": "Apple Inc", "type": "stock"}
        if symbol_info is None:
            symbol_info = default_symbol_info
        response = {
            "results": results,
            "next": f"https://www.tradingview.com/api/v1/minds/?c={next_cursor}"
            if next_cursor
            else "",
            "meta": {"symbols_info": {"NASDAQ:AAPL": symbol_info}},
        }
        return response

    @patch.object(Minds, "_request")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_single_page_success(self, mock_verify, mock_request) -> None:
        """Test single page success."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        mock_mind = {
            "text": "Test mind",
            "url": "/mind/1",
            "author": {"username": "user", "uri": "/u/user", "is_broker": False},
            "created": "2024-01-01T00:00:00Z",
            "total_likes": 5,
            "total_comments": 2,
        }
        mock_request.return_value = (self._make_mock_api_response([mock_mind]), None)

        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 1
        assert result["data"][0]["text"] == "Test mind"
        assert result["metadata"]["exchange"] == "NASDAQ"
        assert result["metadata"]["symbol"] == "AAPL"
        assert result["metadata"]["pages"] == 1

    @patch.object(Minds, "_request")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_multi_page_pagination(self, mock_verify, mock_request) -> None:
        """Test multi-page pagination."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        page1 = self._make_mock_api_response(
            [
                {
                    "text": "Page 1",
                    "url": "/1",
                    "author": {},
                    "created": "",
                    "total_likes": 0,
                    "total_comments": 0,
                }
            ],
            next_cursor="cursor_page2",
        )
        page2 = self._make_mock_api_response(
            [
                {
                    "text": "Page 2",
                    "url": "/2",
                    "author": {},
                    "created": "",
                    "total_likes": 0,
                    "total_comments": 0,
                }
            ],
        )

        mock_request.side_effect = [(page1, None), (page2, None)]

        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 2
        assert result["metadata"]["pages"] == 2

    @patch.object(Minds, "_request")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_limit_applied(self, mock_verify, mock_request) -> None:
        """Test limit parameter applied correctly."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        minds = [
            {
                "text": f"Mind {i}",
                "url": f"/{i}",
                "author": {},
                "created": "",
                "total_likes": 0,
                "total_comments": 0,
            }
            for i in range(10)
        ]
        mock_request.return_value = (self._make_mock_api_response(minds), None)

        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL", limit=5)

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 5
        assert result["metadata"]["limit"] == 5

    @patch.object(Minds, "_request")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_symbol_info_extracted(self, mock_verify, mock_request) -> None:
        """Test symbol info extracted from first page."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        symbol_info = {
            "name": "Apple Inc",
            "type": "stock",
            "description": "Tech company",
        }
        mock_request.return_value = (
            self._make_mock_api_response([], symbol_info=symbol_info),
            None,
        )

        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert result["metadata"]["symbol_info"]["name"] == "Apple Inc"


class TestGetMindsErrorHandling:
    """Test error handling in get_minds."""

    @patch.object(Minds, "_request")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_network_error(self, mock_verify, mock_request) -> None:
        """Test network error handling."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_request.return_value = (None, "Network error: Connection refused")

        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Network error" in result["error"]

    @patch.object(Minds, "_request")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_empty_results_break_loop(self, mock_verify, mock_request) -> None:
        """Test that empty results break the pagination loop."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_request.return_value = ({"results": [], "next": "", "meta": {}}, None)

        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 0

    @patch.object(Minds, "_request")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_max_pages_limit(self, mock_verify, mock_request) -> None:
        """Test max pages limit is enforced."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        mind = {
            "text": "Mind",
            "url": "/1",
            "author": {},
            "created": "",
            "total_likes": 0,
            "total_comments": 0,
        }
        mock_request.return_value = (
            {"results": [mind], "next": "https://example.com?c=next", "meta": {}},
            None,
        )

        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert result["metadata"]["pages"] == MAX_PAGES
        assert mock_request.call_count == MAX_PAGES


class TestGetMindsExport:
    """Test export functionality."""

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.base.save_json_file")
    def test_export_json(self, mock_save, mock_verify) -> None:
        """Test JSON export."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        scraper = Minds(export_result=True, export_type="json")

        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = (
                {
                    "results": [
                        {
                            "text": "Test",
                            "url": "/1",
                            "author": {},
                            "created": "",
                            "total_likes": 0,
                            "total_comments": 0,
                        }
                    ],
                    "next": "",
                    "meta": {},
                },
                None,
            )
            scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert mock_save.called

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    @patch("tv_scraper.core.base.save_csv_file")
    def test_export_csv(self, mock_save, mock_verify) -> None:
        """Test CSV export."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        scraper = Minds(export_result=True, export_type="csv")

        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = (
                {
                    "results": [
                        {
                            "text": "Test",
                            "url": "/1",
                            "author": {},
                            "created": "",
                            "total_likes": 0,
                            "total_comments": 0,
                        }
                    ],
                    "next": "",
                    "meta": {},
                },
                None,
            )
            scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert mock_save.called


class TestGetMindsResponseEnvelope:
    """Test standardized response envelope."""

    @patch.object(Minds, "_request")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_success_has_all_keys(self, mock_verify, mock_request) -> None:
        """Test success response has required keys."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_request.return_value = (
            {"results": [], "next": "", "meta": {}},
            None,
        )

        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None

    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_error_has_all_keys(self, mock_verify) -> None:
        """Test error response has required keys."""
        mock_verify.side_effect = ValidationError("Invalid exchange")

        scraper = Minds()
        result = scraper.get_minds(exchange="INVALID", symbol="AAPL")

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    @patch.object(Minds, "_request")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_metadata_fields(self, mock_verify, mock_request) -> None:
        """Test metadata contains expected fields."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_request.return_value = (
            {
                "results": [
                    {
                        "text": "Test",
                        "url": "/1",
                        "author": {},
                        "created": "",
                        "total_likes": 0,
                        "total_comments": 0,
                    }
                ],
                "next": "",
                "meta": {},
            },
            None,
        )

        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL", limit=10)

        metadata = result["metadata"]
        assert metadata["exchange"] == "NASDAQ"
        assert metadata["symbol"] == "AAPL"
        assert metadata["total"] == 1
        assert metadata["pages"] == 1
        assert metadata["limit"] == 10
        assert "symbol_info" in metadata


class TestGetMindsEdgeCases:
    """Test edge cases."""

    @patch.object(Minds, "_request")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_cursor_without_c_ignored(self, mock_verify, mock_request) -> None:
        """Test that next URL without '?c=' is treated as no more pages."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        mock_request.return_value = (
            {
                "results": [
                    {
                        "text": "Test",
                        "url": "/1",
                        "author": {},
                        "created": "",
                        "total_likes": 0,
                        "total_comments": 0,
                    }
                ],
                "next": "https://example.com/page?other=value",
                "meta": {},
            },
            None,
        )

        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert result["metadata"]["pages"] == 1

    @patch.object(Minds, "_request")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_empty_cursor_ignored(self, mock_verify, mock_request) -> None:
        """Test that empty cursor is treated as no more pages."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        mock_request.return_value = (
            {
                "results": [
                    {
                        "text": "Test",
                        "url": "/1",
                        "author": {},
                        "created": "",
                        "total_likes": 0,
                        "total_comments": 0,
                    }
                ],
                "next": "https://example.com?c=",
                "meta": {},
            },
            None,
        )

        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert result["metadata"]["pages"] == 1

    @patch.object(Minds, "_request")
    @patch("tv_scraper.core.validators.verify_symbol_exchange")
    def test_limit_none_metadata(self, mock_verify, mock_request) -> None:
        """Test that limit=None doesn't add limit to metadata."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_request.return_value = (
            {"results": [], "next": "", "meta": {}},
            None,
        )

        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL", limit=None)

        assert "limit" not in result["metadata"]
