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

    def test_missing_cookie_returns_error(self, monkeypatch: Any) -> None:
        monkeypatch.delenv("TRADINGVIEW_COOKIE", raising=False)
        monkeypatch.delenv("TV_COOKIE", raising=False)
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
        assert result["metadata"] == {}
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


class TestValidateScript:
    """Tests for Pine source validation."""

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_validate_script_with_errors_returns_failed(
        self,
        mock_request: MagicMock,
        pine: Pine,
    ) -> None:
        mock_request.return_value = _mock_response(
            {
                "success": True,
                "result": {
                    "errors": [
                        {
                            "message": '"sdf" is not a valid statement.',
                            "start": {"line": 8, "column": 1},
                            "end": {"line": 8, "column": 3},
                        }
                    ],
                    "warnings": [],
                },
            }
        )

        result = pine.validate_script("indicator('x')\nsdf")

        assert result["status"] == STATUS_FAILED
        assert result["error"] == "Pine script validation failed."
        assert len(result["metadata"]["errors"]) == 1

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_validate_script_with_warning_returns_success(
        self,
        mock_request: MagicMock,
        pine: Pine,
    ) -> None:
        mock_request.return_value = _mock_response(
            {
                "success": True,
                "result": {
                    "errors": [],
                    "warnings": [{"message": "sample warning"}],
                },
            }
        )

        result = pine.validate_script("indicator('x')\nplot(close)")

        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None
        assert result["metadata"]["warnings"] == [{"message": "sample warning"}]


class TestCreateScript:
    """Tests for creating new Pine scripts."""

    @patch("tv_scraper.scrapers.scripts.pine.Pine.validate_script")
    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_create_script_success(
        self,
        mock_request: MagicMock,
        mock_validate: MagicMock,
        pine: Pine,
    ) -> None:
        mock_validate.return_value = {
            "status": STATUS_SUCCESS,
            "data": None,
            "metadata": {"warnings": []},
            "error": None,
        }
        mock_request.return_value = _mock_response(
            {
                "success": True,
                "result": {
                    "metaInfo": {
                        "scriptIdPart": "USER;new123",
                        "description": "My Script",
                        "shortDescription": "My Script",
                    }
                },
            }
        )

        result = pine.create_script(name="My Script", source="indicator('My Script')")

        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None
        assert result["data"]["id"] == "USER;new123"
        assert result["data"]["name"] == "My Script"
        assert result["data"]["warnings"] == []
        assert result["metadata"] == {}

    @patch("tv_scraper.scrapers.scripts.pine.Pine.validate_script")
    def test_create_script_stops_when_validation_fails(
        self,
        mock_validate: MagicMock,
        pine: Pine,
    ) -> None:
        mock_validate.return_value = {
            "status": STATUS_FAILED,
            "data": None,
            "metadata": {"errors": [{"message": "invalid"}]},
            "error": "Pine script validation failed.",
        }

        result = pine.create_script(name="My Script", source="bad source")

        assert result["status"] == STATUS_FAILED
        assert result["error"] == "Pine script validation failed."

    def test_create_script_empty_name_returns_error(self, pine: Pine) -> None:
        result = pine.create_script(name="   ", source="indicator('x')")
        assert result["status"] == STATUS_FAILED
        assert "name cannot be empty" in (result["error"] or "").lower()


class TestEditScript:
    """Tests for editing existing Pine scripts."""

    @patch("tv_scraper.scrapers.scripts.pine.Pine.validate_script")
    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_edit_script_success(
        self,
        mock_request: MagicMock,
        mock_validate: MagicMock,
        pine: Pine,
    ) -> None:
        mock_validate.return_value = {
            "status": STATUS_SUCCESS,
            "data": None,
            "metadata": {"warnings": []},
            "error": None,
        }
        mock_request.return_value = _mock_response(
            {
                "success": True,
                "result": {
                    "metaInfo": {
                        "scriptIdPart": "USER;abc123",
                        "description": "My Script Updated",
                        "shortDescription": "My Script Updated",
                    }
                },
            }
        )

        result = pine.edit_script(
            pine_id="USER;abc123",
            name="My Script Updated",
            source="indicator('My Script Updated')",
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None
        assert result["data"]["id"] == "USER;abc123"
        assert result["data"]["name"] == "My Script Updated"
        assert result["data"]["warnings"] == []
        assert result["metadata"] == {}

    @patch("tv_scraper.scrapers.scripts.pine.Pine.validate_script")
    def test_edit_script_stops_on_validation_error(
        self,
        mock_validate: MagicMock,
        pine: Pine,
    ) -> None:
        mock_validate.return_value = {
            "status": STATUS_FAILED,
            "data": None,
            "metadata": {"errors": [{"message": "invalid"}]},
            "error": "Pine script validation failed.",
        }

        result = pine.edit_script(
            pine_id="USER;abc123",
            name="My Script",
            source="bad",
        )

        assert result["status"] == STATUS_FAILED
        assert result["error"] == "Pine script validation failed."


class TestCreateFromFile:
    """Tests for file-based create flow."""

    @patch("tv_scraper.scrapers.scripts.pine.Pine.create_script")
    def test_create_script_from_file_success(
        self,
        mock_create_script: MagicMock,
        tmp_path: Any,
        pine: Pine,
    ) -> None:
        source_file = tmp_path / "sample.pine"
        source_file.write_text("//@version=6\nindicator('x')\nplot(close)\n")

        mock_create_script.return_value = {
            "status": STATUS_SUCCESS,
            "data": {"id": "USER;abc123", "name": "x"},
            "metadata": {},
            "error": None,
        }

        result = pine.create_script_from_file(str(source_file), name="x")

        assert result["status"] == STATUS_SUCCESS
        mock_create_script.assert_called_once()

    def test_create_script_from_file_rejects_binary(
        self,
        tmp_path: Any,
        pine: Pine,
    ) -> None:
        binary_file = tmp_path / "sample.o"
        binary_file.write_bytes(b"\x00\x01\x02")

        result = pine.create_script_from_file(str(binary_file), name="x")

        assert result["status"] == STATUS_FAILED
        assert (
            "binary/object files are not supported" in (result["error"] or "").lower()
        )


class TestDeleteScript:
    """Tests for deleting Pine scripts."""

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_delete_script_success(
        self,
        mock_request: MagicMock,
        pine: Pine,
    ) -> None:
        response = MagicMock()
        response.status_code = 200
        response.text = '"ok"'
        mock_request.return_value = response

        result = pine.delete_script("USER;abc123")

        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None
        assert result["data"] == {"id": "USER;abc123", "deleted": True}
        assert result["metadata"] == {}

    def test_delete_script_empty_id_returns_error(self, pine: Pine) -> None:
        result = pine.delete_script("   ")

        assert result["status"] == STATUS_FAILED
        assert "id cannot be empty" in (result["error"] or "").lower()

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_delete_script_unexpected_response_returns_error(
        self,
        mock_request: MagicMock,
        pine: Pine,
    ) -> None:
        response = MagicMock()
        response.status_code = 200
        response.text = '"not-ok"'
        mock_request.return_value = response

        result = pine.delete_script("USER;abc123")

        assert result["status"] == STATUS_FAILED
        assert "unexpected response" in (result["error"] or "").lower()
