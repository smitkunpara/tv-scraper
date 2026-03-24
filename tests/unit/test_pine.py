"""Tests for Pine scraper module."""

from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.scripts.pine import Pine


def _mock_response(json_data: Any, status_code: int = 200) -> MagicMock:
    """Create a mock requests.Response with JSON payload."""
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data
    response.raise_for_status.return_value = None
    return response


@pytest.fixture
def pine() -> Iterator[Pine]:
    """Create a Pine instance with a test cookie."""
    yield Pine(cookie="sessionid=test")


class TestInheritance:
    """Verify Pine inherits from BaseScraper."""

    def test_inherits_base_scraper(self) -> None:
        assert issubclass(Pine, BaseScraper)


class TestCookieValidation:
    """Ensure cookie is required for Pine operations."""

    def test_missing_cookie_returns_error(self) -> None:
        pine = Pine(cookie=None)

        result = pine.list_saved_scripts()

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "cookie is required" in (result["error"] or "").lower()


class TestListSavedScripts:
    """Tests for listing saved scripts."""

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_list_saved_scripts_success(
        self,
        mock_request: MagicMock,
        pine: Pine,
    ) -> None:
        mock_request.return_value = _mock_response(
            [
                {
                    "scriptIdPart": "USER;abc123",
                    "scriptName": "My Script",
                    "scriptTitle": "My Script",
                    "modified": 1774357749,
                }
            ]
        )

        result = pine.list_saved_scripts()

        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None
        assert result["metadata"]["total"] == 1
        assert result["data"] == [
            {"id": "USER;abc123", "name": "My Script", "modified": 1774357749}
        ]

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_list_saved_scripts_invalid_cookie_maps_error(
        self,
        mock_request: MagicMock,
        pine: Pine,
    ) -> None:
        mock_request.side_effect = Exception(
            "HTTP error 401 for https://pine-facade.tradingview.com/pine-facade/list"
        )

        result = pine.list_saved_scripts()

        assert result["status"] == STATUS_FAILED
        assert "invalid tradingview cookie" in (result["error"] or "").lower()

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_list_saved_scripts_unexpected_payload_returns_error(
        self,
        mock_request: MagicMock,
        pine: Pine,
    ) -> None:
        mock_request.return_value = _mock_response({"not": "a-list"})

        result = pine.list_saved_scripts()

        assert result["status"] == STATUS_FAILED
        assert "unexpected response format" in (result["error"] or "").lower()
