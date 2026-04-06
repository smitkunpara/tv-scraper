"""Mock tests for Pine scripts using saved fixtures.

Tests Pine scraper methods with mocked HTTP responses from saved fixtures.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.scripts.pine import Pine

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "pine"
COOKIE = "mock_cookie_123"


def _load_fixture(filename: str) -> dict:
    """Load fixture JSON from file."""
    fixture_path = FIXTURES_DIR / filename
    if fixture_path.exists():
        with open(fixture_path) as f:
            return json.load(f)
    return {}


def _create_mock_response(data: dict, status_code: int = 200) -> MagicMock:
    """Create a mock response object."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.text = json.dumps(data)
    mock_response.json.return_value = data
    mock_response.raise_for_status = MagicMock()
    if status_code >= 400:
        mock_response.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return mock_response


class TestListSavedScriptsMock:
    """Test list_saved_scripts() with mocked responses."""

    @pytest.fixture
    def mock_list_response(self) -> dict:
        """Load list response fixture."""
        return _load_fixture("list_response.json")

    @patch("requests.request")
    def test_list_saved_scripts_success(
        self, mock_request: MagicMock, mock_list_response: dict
    ) -> None:
        """Verify list_saved_scripts parses response correctly."""
        mock_request.return_value = _create_mock_response(
            mock_list_response.get(
                "data",
                [
                    {
                        "scriptIdPart": "USER;abc123",
                        "scriptName": "Test Script",
                        "version": "4",
                        "modified": 1700000000,
                    }
                ],
            )
        )
        scraper = Pine(cookie=COOKIE)
        result = scraper.list_saved_scripts()

        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)

    @patch("requests.request")
    def test_list_saved_scripts_empty(self, mock_request: MagicMock) -> None:
        """Verify empty list handled correctly."""
        mock_request.return_value = _create_mock_response([])
        scraper = Pine(cookie=COOKIE)
        result = scraper.list_saved_scripts()

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] == []

    @patch("requests.request")
    def test_list_saved_scripts_invalid_json(self, mock_request: MagicMock) -> None:
        """Verify invalid JSON response handled."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "not json"
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response

        scraper = Pine(cookie=COOKIE)
        result = scraper.list_saved_scripts()

        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    @patch("requests.request")
    def test_list_saved_scripts_network_error(self, mock_request: MagicMock) -> None:
        """Verify network error handled."""
        import requests

        mock_request.side_effect = requests.RequestException("Connection error")

        scraper = Pine(cookie=COOKIE)
        result = scraper.list_saved_scripts()

        assert result["status"] == STATUS_FAILED
        assert "Network error" in result["error"]

    def test_list_saved_scripts_no_cookie(self) -> None:
        """Verify missing cookie returns error."""
        scraper = Pine(cookie=None)
        result = scraper.list_saved_scripts()

        assert result["status"] == STATUS_FAILED
        assert "cookie" in result["error"].lower()

    @patch("requests.request")
    def test_list_saved_scripts_maps_fields(self, mock_request: MagicMock) -> None:
        """Verify script items mapped to expected structure."""
        raw_items = [
            {
                "scriptIdPart": "USER;xyz789",
                "scriptName": "My Indicator",
                "version": "3",
                "modified": 1700000000,
            }
        ]
        mock_request.return_value = _create_mock_response(raw_items)
        scraper = Pine(cookie=COOKIE)
        result = scraper.list_saved_scripts()

        assert result["status"] == STATUS_SUCCESS
        script = result["data"][0]
        assert script["id"] == "USER;xyz789"
        assert script["name"] == "My Indicator"
        assert script["version"] == "3"
        assert script["modified"] == 1700000000

    @patch("requests.request")
    def test_list_saved_scripts_handles_missing_fields(
        self, mock_request: MagicMock
    ) -> None:
        """Verify missing fields handled gracefully."""
        raw_items = [{"scriptIdPart": "USER;abc"}]
        mock_request.return_value = _create_mock_response(raw_items)
        scraper = Pine(cookie=COOKIE)
        result = scraper.list_saved_scripts()

        assert result["status"] == STATUS_SUCCESS
        script = result["data"][0]
        assert script["id"] == "USER;abc"
        assert script["name"] == ""
        assert script["version"] is None

    @patch("requests.request")
    def test_list_saved_scripts_invalid_modified(self, mock_request: MagicMock) -> None:
        """Verify invalid modified timestamp handled."""
        raw_items = [
            {
                "scriptIdPart": "USER;abc",
                "scriptName": "Test",
                "modified": -1,
            }
        ]
        mock_request.return_value = _create_mock_response(raw_items)
        scraper = Pine(cookie=COOKIE)
        result = scraper.list_saved_scripts()

        assert result["status"] == STATUS_SUCCESS
        assert result["data"][0]["modified"] == 0


class TestValidateScriptMock:
    """Test validate_script() with mocked responses."""

    @patch("requests.request")
    def test_validate_success(self, mock_request: MagicMock) -> None:
        """Verify successful validation."""
        mock_request.return_value = _create_mock_response(
            {"result": {"errors": [], "warnings": []}}
        )
        scraper = Pine(cookie=COOKIE)
        result = scraper.validate_script("//@version=6\nplot(close)")

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is None

    @patch("requests.request")
    def test_validate_with_warnings(self, mock_request: MagicMock) -> None:
        """Verify validation with warnings still succeeds."""
        mock_request.return_value = _create_mock_response(
            {"result": {"errors": [], "warnings": [{"text": "Unused variable"}]}}
        )
        scraper = Pine(cookie=COOKIE)
        result = scraper.validate_script("//@version=6\nvar x = na")

        assert result["status"] == STATUS_SUCCESS
        assert len(result["metadata"]["warnings"]) == 1

    @patch("requests.request")
    def test_validate_with_errors(self, mock_request: MagicMock) -> None:
        """Verify validation with errors fails."""
        mock_request.return_value = _create_mock_response(
            {"result": {"errors": [{"text": "Undefined function"}], "warnings": []}}
        )
        scraper = Pine(cookie=COOKIE)
        result = scraper.validate_script("//@version=6\nundefined()")

        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None
        assert len(result["metadata"]["errors"]) == 1

    def test_validate_empty_source(self) -> None:
        """Verify empty source returns error."""
        scraper = Pine(cookie=COOKIE)
        result = scraper.validate_script("")

        assert result["status"] == STATUS_FAILED
        assert "empty" in result["error"].lower()

    def test_validate_whitespace_source(self) -> None:
        """Verify whitespace-only source returns error."""
        scraper = Pine(cookie=COOKIE)
        result = scraper.validate_script("   \n\t  ")

        assert result["status"] == STATUS_FAILED

    def test_validate_no_cookie(self) -> None:
        """Verify missing cookie returns error."""
        scraper = Pine(cookie=None)
        result = scraper.validate_script("//@version=6\nplot(close)")

        assert result["status"] == STATUS_FAILED
        assert "cookie" in result["error"].lower()

    @patch("requests.request")
    def test_validate_unexpected_response_format(self, mock_request: MagicMock) -> None:
        """Verify unexpected response format handled."""
        mock_request.return_value = _create_mock_response("not a dict")
        scraper = Pine(cookie=COOKIE)
        result = scraper.validate_script("//@version=6\nplot(close)")

        assert result["status"] == STATUS_FAILED


class TestCreateScriptMock:
    """Test create_script() with mocked responses."""

    VALID_SOURCE = "//@version=6\nindicator('Test')\nplot(close)"

    @patch("requests.request")
    def test_create_success(self, mock_request: MagicMock) -> None:
        """Verify successful script creation."""
        validation_response = _create_mock_response(
            {"result": {"errors": [], "warnings": []}}
        )
        create_response = _create_mock_response(
            {
                "result": {
                    "metaInfo": {
                        "scriptIdPart": "USER;new123",
                        "shortDescription": "Test",
                    },
                }
            }
        )
        mock_request.side_effect = [validation_response, create_response]
        scraper = Pine(cookie=COOKIE)
        result = scraper.create_script(name="TestScript", source=self.VALID_SOURCE)

        assert result["status"] == STATUS_SUCCESS
        assert result["data"]["id"] == "USER;new123"
        assert result["data"]["name"] == "Test"

    def test_create_empty_name(self) -> None:
        """Verify empty name returns error."""
        scraper = Pine(cookie=COOKIE)
        result = scraper.create_script(name="", source=self.VALID_SOURCE)

        assert result["status"] == STATUS_FAILED
        assert "name" in result["error"].lower()

    def test_create_empty_source(self) -> None:
        """Verify empty source returns error."""
        scraper = Pine(cookie=COOKIE)
        result = scraper.create_script(name="Test", source="")

        assert result["status"] == STATUS_FAILED
        assert "source" in result["error"].lower()

    def test_create_no_cookie(self) -> None:
        """Verify missing cookie returns error."""
        scraper = Pine(cookie=None)
        result = scraper.create_script(name="Test", source=self.VALID_SOURCE)

        assert result["status"] == STATUS_FAILED
        assert "cookie" in result["error"].lower()

    @patch("requests.request")
    def test_create_invalid_source(self, mock_request: MagicMock) -> None:
        """Verify script with errors is rejected."""
        mock_request.return_value = _create_mock_response(
            {"result": {"errors": [{"text": "Error"}], "warnings": []}}
        )
        scraper = Pine(cookie=COOKIE)
        result = scraper.create_script(name="Test", source="//@version=6\nundefined()")

        assert result["status"] == STATUS_FAILED

    @patch("requests.request")
    def test_create_unexpected_response(self, mock_request: MagicMock) -> None:
        """Verify unexpected response handled."""
        mock_request.return_value = _create_mock_response({})
        scraper = Pine(cookie=COOKIE)
        result = scraper.create_script(name="Test", source=self.VALID_SOURCE)

        assert result["status"] == STATUS_FAILED


class TestEditScriptMock:
    """Test edit_script() with mocked responses."""

    VALID_SOURCE = "//@version=6\nindicator('Test')\nplot(close)"

    @patch("requests.request")
    def test_edit_success(self, mock_request: MagicMock) -> None:
        """Verify successful script edit."""
        validation_response = _create_mock_response(
            {"result": {"errors": [], "warnings": []}}
        )
        edit_response = _create_mock_response(
            {
                "result": {
                    "metaInfo": {
                        "scriptIdPart": "USER;existing123",
                        "shortDescription": "Updated",
                    },
                }
            }
        )
        mock_request.side_effect = [validation_response, edit_response]
        scraper = Pine(cookie=COOKIE)
        result = scraper.edit_script(
            pine_id="USER;existing123", name="UpdatedScript", source=self.VALID_SOURCE
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"]["id"] == "USER;existing123"

    def test_edit_empty_id(self) -> None:
        """Verify empty script ID returns error."""
        scraper = Pine(cookie=COOKIE)
        result = scraper.edit_script(pine_id="", name="Test", source=self.VALID_SOURCE)

        assert result["status"] == STATUS_FAILED
        assert "id" in result["error"].lower()

    def test_edit_empty_name(self) -> None:
        """Verify empty name returns error."""
        scraper = Pine(cookie=COOKIE)
        result = scraper.edit_script(
            pine_id="USER;test", name="", source=self.VALID_SOURCE
        )

        assert result["status"] == STATUS_FAILED
        assert "name" in result["error"].lower()

    def test_edit_no_cookie(self) -> None:
        """Verify missing cookie returns error."""
        scraper = Pine(cookie=None)
        result = scraper.edit_script(
            pine_id="USER;test", name="Test", source=self.VALID_SOURCE
        )

        assert result["status"] == STATUS_FAILED
        assert "cookie" in result["error"].lower()

    @patch("requests.request")
    def test_edit_invalid_source(self, mock_request: MagicMock) -> None:
        """Verify script with errors is rejected."""
        validation_response = _create_mock_response(
            {"result": {"errors": [{"text": "Error"}], "warnings": []}}
        )
        mock_request.side_effect = [validation_response]
        scraper = Pine(cookie=COOKIE)
        result = scraper.edit_script(
            pine_id="USER;test", name="Test", source="//@version=6\nundefined()"
        )

        assert result["status"] == STATUS_FAILED


class TestDeleteScriptMock:
    """Test delete_script() with mocked responses."""

    @patch("requests.request")
    def test_delete_success(self, mock_request: MagicMock) -> None:
        """Verify successful script deletion."""
        mock_request.return_value = _create_mock_response("ok")
        scraper = Pine(cookie=COOKIE)
        result = scraper.delete_script("USER;test123")

        assert result["status"] == STATUS_SUCCESS
        assert result["data"]["id"] == "USER;test123"

    def test_delete_empty_id(self) -> None:
        """Verify empty script ID returns error."""
        scraper = Pine(cookie=COOKIE)
        result = scraper.delete_script("")

        assert result["status"] == STATUS_FAILED
        assert "id" in result["error"].lower()

    def test_delete_no_cookie(self) -> None:
        """Verify missing cookie returns error."""
        scraper = Pine(cookie=None)
        result = scraper.delete_script("USER;test")

        assert result["status"] == STATUS_FAILED
        assert "cookie" in result["error"].lower()

    @patch("requests.request")
    def test_delete_unexpected_response(self, mock_request: MagicMock) -> None:
        """Verify unexpected response handled."""
        mock_request.return_value = _create_mock_response({"status": "error"})
        scraper = Pine(cookie=COOKIE)
        result = scraper.delete_script("USER;test")

        assert result["status"] == STATUS_FAILED

    @patch("requests.request")
    def test_delete_network_error(self, mock_request: MagicMock) -> None:
        """Verify network error handled."""
        import requests

        mock_request.side_effect = requests.RequestException("Connection error")
        scraper = Pine(cookie=COOKIE)
        result = scraper.delete_script("USER;test")

        assert result["status"] == STATUS_FAILED


class TestBuildPineHeaders:
    """Test _build_pine_headers() method."""

    def test_builds_correct_headers(self) -> None:
        """Verify headers include Pine-specific values."""
        scraper = Pine(cookie=COOKIE)
        headers = scraper._build_pine_headers()

        assert headers["cookie"] == COOKIE
        assert headers["accept"] == "*/*"
        assert headers["origin"] == "https://in.tradingview.com"
        assert "referer" in headers

    def test_headers_includes_base_headers(self) -> None:
        """Verify base headers included."""
        scraper = Pine(cookie=COOKIE)
        headers = scraper._build_pine_headers()

        assert "User-Agent" in headers


class TestMapScriptItem:
    """Test _map_script_item() static method."""

    def test_maps_all_fields(self) -> None:
        """Verify all fields mapped correctly."""
        item = {
            "scriptIdPart": "USER;abc",
            "scriptName": "Test Script",
            "version": "5",
            "modified": 1700000000,
        }
        result = Pine._map_script_item(item)

        assert result["id"] == "USER;abc"
        assert result["name"] == "Test Script"
        assert result["version"] == "5"
        assert result["modified"] == 1700000000

    def test_falls_back_to_script_title(self) -> None:
        """Verify scriptTitle used when scriptName missing."""
        item = {
            "scriptIdPart": "USER;abc",
            "scriptTitle": "Fallback Title",
            "modified": 1700000000,
        }
        result = Pine._map_script_item(item)

        assert result["name"] == "Fallback Title"

    def test_handles_missing_name(self) -> None:
        """Verify empty string when no name available."""
        item = {
            "scriptIdPart": "USER;abc",
            "modified": 1700000000,
        }
        result = Pine._map_script_item(item)

        assert result["name"] == ""

    def test_handles_invalid_modified(self) -> None:
        """Verify invalid modified defaults to 0."""
        item = {
            "scriptIdPart": "USER;abc",
            "modified": "invalid",
        }
        result = Pine._map_script_item(item)

        assert result["modified"] == 0

    def test_handles_negative_modified(self) -> None:
        """Verify negative modified defaults to 0."""
        item = {
            "scriptIdPart": "USER;abc",
            "modified": -100,
        }
        result = Pine._map_script_item(item)

        assert result["modified"] == 0


class TestExtractSaveResult:
    """Test _extract_save_result() static method."""

    def test_extracts_result(self) -> None:
        """Verify save result extracted correctly."""
        payload = {"result": {"metaInfo": {"scriptIdPart": "USER;abc"}}}
        result = Pine._extract_save_result(payload)

        assert result is not None
        assert result["scriptIdPart"] == "USER;abc"

    def test_returns_none_for_invalid_payload(self) -> None:
        """Verify None returned for invalid payload."""
        assert Pine._extract_save_result("string") is None
        assert Pine._extract_save_result({}) is None
        assert Pine._extract_save_result({"result": {}}) is None
        assert Pine._extract_save_result({"result": {"metaInfo": {}}}) is None

    def test_returns_none_when_no_script_id(self) -> None:
        """Verify None returned when scriptIdPart missing."""
        payload = {"result": {"metaInfo": {"otherField": "value"}}}
        result = Pine._extract_save_result(payload)

        assert result is None
