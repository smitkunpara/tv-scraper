"""Integration tests for Minds scraper.

Tests cross-module workflows and interactions between components.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.social.minds import Minds

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "minds"


def load_fixture(name: str) -> dict:
    """Load a fixture file for testing."""
    filepath = FIXTURES_DIR / f"{name}.json"
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    pytest.skip(f"Fixture not found: {name}.json")


class TestMindsIntegrationWithValidator:
    """Test minds scraper integration with DataValidator."""

    def test_validator_called_with_correct_params(self) -> None:
        """Test that validator is called with correct exchange and symbol."""
        scraper = Minds()

        with patch.object(scraper.validator, "verify_symbol_exchange") as mock_verify:
            mock_verify.return_value = ("NASDAQ", "AAPL")
            with patch.object(scraper, "_request") as mock_req:
                mock_req.return_value = ({"results": [], "next": "", "meta": {}}, None)
                scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

            mock_verify.assert_called_once_with("NASDAQ", "AAPL")

    def test_validator_error_returns_error_response(self) -> None:
        """Test that validator errors propagate to error response."""
        from tv_scraper.core.exceptions import ValidationError

        scraper = Minds()

        with patch.object(scraper.validator, "verify_symbol_exchange") as mock_verify:
            mock_verify.side_effect = ValidationError("Symbol not found")
            result = scraper.get_minds(exchange="NASDAQ", symbol="INVALID")

            assert result["status"] == "failed"
            assert result["error"] is not None
            assert "Symbol not found" in result["error"]


class TestMindsIntegrationWithBaseScraper:
    """Test minds scraper integration with BaseScraper methods."""

    def test_success_response_includes_metadata(self) -> None:
        """Test that success response includes all metadata."""
        scraper = Minds()

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
                    "meta": {"symbols_info": {"NASDAQ:AAPL": {"name": "Apple"}}},
                },
                None,
            )
            result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert "metadata" in result
        assert result["metadata"]["exchange"] == "NASDAQ"
        assert result["metadata"]["symbol"] == "AAPL"

    def test_error_response_includes_metadata(self) -> None:
        """Test that error response includes metadata even on failure."""
        from tv_scraper.core.exceptions import ValidationError

        scraper = Minds()

        with patch.object(scraper.validator, "verify_symbol_exchange") as mock_verify:
            mock_verify.side_effect = ValidationError("Test error")
            result = scraper.get_minds(exchange="INVALID", symbol="AAPL")

        assert "metadata" in result
        assert result["metadata"]["exchange"] == "INVALID"
        assert result["metadata"]["symbol"] == "AAPL"


class TestMindsIntegrationWithExport:
    """Test minds scraper integration with export functionality."""

    def test_export_enabled_calls_save_json(self) -> None:
        """Test that enabling export calls save_json_file."""
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
            with patch("tv_scraper.core.base.save_json_file") as mock_save:
                result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

                assert result["status"] == STATUS_SUCCESS
                assert mock_save.called

    def test_export_disabled_does_not_call_save(self) -> None:
        """Test that disabling export doesn't call save functions."""
        scraper = Minds(export_result=False)

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
            with patch("tv_scraper.core.base.save_json_file") as mock_save:
                result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

                assert result["status"] == STATUS_SUCCESS
                assert not mock_save.called


class TestMindsPaginationWorkflow:
    """Test complete pagination workflow."""

    def _make_mock_api_response(self, page_num: int, has_next: bool = False) -> dict:
        """Create mock API response for pagination testing."""
        return {
            "results": [
                {
                    "text": f"Page {page_num} Mind",
                    "url": f"/page{page_num}",
                    "author": {
                        "username": "user",
                        "uri": "/u/user",
                        "is_broker": False,
                    },
                    "created": "2024-01-01T00:00:00Z",
                    "total_likes": page_num,
                    "total_comments": page_num,
                }
            ],
            "next": f"https://api?c=page{page_num + 1}" if has_next else "",
            "meta": {},
        }

    def test_full_pagination_cycle(self) -> None:
        """Test complete pagination from first page through last."""
        scraper = Minds()
        pages_received = []

        def mock_request(*args, **kwargs):
            page_num = len(pages_received) + 1
            pages_received.append(page_num)
            has_next = page_num < 3
            return (self._make_mock_api_response(page_num, has_next), None)

        with patch.object(scraper, "_request", side_effect=mock_request):
            result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 3
        assert pages_received == [1, 2, 3]
        assert result["metadata"]["pages"] == 3


class TestMindsWithDifferentSymbolTypes:
    """Test minds scraper with different symbol types."""

    @pytest.mark.parametrize(
        "exchange,symbol",
        [
            ("NASDAQ", "AAPL"),
            ("NYSE", "JPM"),
            ("BINANCE", "BTCUSDT"),
        ],
    )
    def test_multiple_symbol_combinations(self, exchange: str, symbol: str) -> None:
        """Test multiple exchange/symbol combinations."""
        scraper = Minds()

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
            result = scraper.get_minds(exchange=exchange, symbol=symbol)

        assert "status" in result
        assert result["metadata"]["exchange"] == exchange
        assert result["metadata"]["symbol"] == symbol


class TestMindsCrossModuleWorkflow:
    """Test cross-module workflows combining multiple components."""

    def test_validation_then_fetch_workflow(self) -> None:
        """Test complete workflow: validate -> fetch -> parse -> export."""
        scraper = Minds(export_result=True, export_type="json")

        with patch.object(scraper.validator, "verify_symbol_exchange") as mock_verify:
            mock_verify.return_value = ("NASDAQ", "AAPL")

            with patch.object(scraper, "_request") as mock_req:
                mock_req.return_value = (
                    {
                        "results": [
                            {
                                "text": "Test mind content",
                                "url": "/test",
                                "author": {
                                    "username": "tester",
                                    "uri": "/u/tester",
                                    "is_broker": False,
                                },
                                "created": "2024-06-15T12:00:00Z",
                                "total_likes": 10,
                                "total_comments": 3,
                            }
                        ],
                        "next": "",
                        "meta": {"symbols_info": {"NASDAQ:AAPL": {"name": "Apple"}}},
                    },
                    None,
                )

                result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 1
        assert result["data"][0]["text"] == "Test mind content"
        assert result["data"][0]["author"]["username"] == "tester"
        assert result["metadata"]["total"] == 1

    def test_validation_failure_short_circuits(self) -> None:
        """Test that validation failure prevents API call."""
        from tv_scraper.core.exceptions import ValidationError

        scraper = Minds()

        with patch.object(scraper.validator, "verify_symbol_exchange") as mock_verify:
            mock_verify.side_effect = ValidationError("Invalid")

            with patch.object(scraper, "_request") as mock_req:
                result = scraper.get_minds(exchange="INVALID", symbol="AAPL")

        assert not mock_req.called
        assert result["status"] == "failed"


class TestMindsFixturesWorkflow:
    """Test workflows using saved fixtures."""

    def test_fixture_data_structure(self) -> None:
        """Test that fixture data has correct structure."""
        result = load_fixture("basic")

        assert result["status"] == "success"
        assert "data" in result
        assert "metadata" in result

        if result["data"]:
            mind = result["data"][0]
            assert "text" in mind
            assert "url" in mind
            assert "author" in mind
            assert "created" in mind
            assert "total_likes" in mind
            assert "total_comments" in mind

            assert "username" in mind["author"]
            assert "profile_url" in mind["author"]
            assert "is_broker" in mind["author"]

    def test_fixture_metadata_structure(self) -> None:
        """Test that fixture metadata has correct structure."""
        result = load_fixture("basic")

        assert "exchange" in result["metadata"]
        assert "symbol" in result["metadata"]
        assert "total" in result["metadata"]
        assert "pages" in result["metadata"]
        assert "symbol_info" in result["metadata"]

    def test_limit_fixture_verification(self) -> None:
        """Test limit=10 fixture verification."""
        result = load_fixture("limit_10")

        if result["status"] == STATUS_SUCCESS:
            assert len(result["data"]) <= 10
            assert result["metadata"]["limit"] == 10

    def test_limit_none_fixture_verification(self) -> None:
        """Test limit=None fixture verification."""
        result = load_fixture("limit_none")

        if result["status"] == STATUS_SUCCESS:
            assert "limit" not in result["metadata"]
