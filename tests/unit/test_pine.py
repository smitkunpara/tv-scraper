"""Unit tests for Pine scripts module.

Tests isolated functions and methods without network calls.
"""

import pytest

from tv_scraper.core.constants import STATUS_FAILED
from tv_scraper.scrapers.scripts.pine import Pine


class TestValidateNonEmpty:
    """Test _validate_non_empty() static method."""

    def test_valid_string(self) -> None:
        """Verify valid string returns None."""
        result = Pine._validate_non_empty("test", "Field")
        assert result is None

    def test_whitespace_only(self) -> None:
        """Verify whitespace-only string returns error."""
        result = Pine._validate_non_empty("   ", "Field")
        assert result is not None
        assert "empty" in result.lower()

    def test_empty_string(self) -> None:
        """Verify empty string returns error."""
        result = Pine._validate_non_empty("", "Field")
        assert result is not None

    def test_field_name_in_error(self) -> None:
        """Verify field name appears in error message."""
        result = Pine._validate_non_empty("", "Script name")
        assert "Script name" in result


class TestValidateCookieRequired:
    """Test _validate_cookie_required() method."""

    def test_with_cookie(self) -> None:
        """Verify valid cookie returns None."""
        scraper = Pine(cookie="valid_cookie")
        result = scraper._validate_cookie_required()
        assert result is None

    def test_without_cookie(self) -> None:
        """Verify missing cookie returns error response."""
        scraper = Pine(cookie=None)
        result = scraper._validate_cookie_required()

        assert result is not None
        assert result["status"] == STATUS_FAILED
        assert "cookie" in result["error"].lower()

    def test_empty_cookie(self) -> None:
        """Verify empty cookie returns error response."""
        scraper = Pine(cookie="")
        result = scraper._validate_cookie_required()

        assert result is not None
        assert result["status"] == STATUS_FAILED


class TestMapScriptItem:
    """Test _map_script_item() static method."""

    def test_maps_complete_item(self) -> None:
        """Verify complete item mapped correctly."""
        item = {
            "scriptIdPart": "USER;abc123",
            "scriptName": "My Indicator",
            "version": "4",
            "modified": 1700000000,
        }
        result = Pine._map_script_item(item)

        assert result["id"] == "USER;abc123"
        assert result["name"] == "My Indicator"
        assert result["version"] == "4"
        assert result["modified"] == 1700000000

    def test_uses_script_title_as_fallback(self) -> None:
        """Verify scriptTitle used when scriptName missing."""
        item = {
            "scriptIdPart": "USER;abc",
            "scriptTitle": "Indicator Title",
            "modified": 1700000000,
        }
        result = Pine._map_script_item(item)

        assert result["name"] == "Indicator Title"

    def test_empty_name_when_both_missing(self) -> None:
        """Verify empty name when both fields missing."""
        item = {
            "scriptIdPart": "USER;abc",
            "modified": 1700000000,
        }
        result = Pine._map_script_item(item)

        assert result["name"] == ""

    def test_version_fallback(self) -> None:
        """Verify scriptVersion used when version missing."""
        item = {
            "scriptIdPart": "USER;abc",
            "scriptName": "Test",
            "scriptVersion": "3",
            "modified": 1700000000,
        }
        result = Pine._map_script_item(item)

        assert result["version"] == "3"

    def test_none_version_when_both_missing(self) -> None:
        """Verify version is None when both version fields missing."""
        item = {
            "scriptIdPart": "USER;abc",
            "scriptName": "Test",
            "modified": 1700000000,
        }
        result = Pine._map_script_item(item)

        assert result["version"] is None

    def test_invalid_modified_string(self) -> None:
        """Verify string modified defaults to 0."""
        item = {
            "scriptIdPart": "USER;abc",
            "modified": "not a number",
        }
        result = Pine._map_script_item(item)

        assert result["modified"] == 0

    def test_invalid_modified_negative(self) -> None:
        """Verify negative modified defaults to 0."""
        item = {
            "scriptIdPart": "USER;abc",
            "modified": -1,
        }
        result = Pine._map_script_item(item)

        assert result["modified"] == 0

    def test_invalid_modified_float(self) -> None:
        """Verify float modified defaults to 0."""
        item = {
            "scriptIdPart": "USER;abc",
            "modified": 1.5,
        }
        result = Pine._map_script_item(item)

        assert result["modified"] == 0

    def test_missing_modified(self) -> None:
        """Verify missing modified defaults to 0."""
        item = {"scriptIdPart": "USER;abc"}
        result = Pine._map_script_item(item)

        assert result["modified"] == 0


class TestExtractSaveResult:
    """Test _extract_save_result() static method."""

    def test_extracts_complete_result(self) -> None:
        """Verify complete payload extracted correctly."""
        payload = {"result": {"metaInfo": {"scriptIdPart": "USER;new_script"}}}
        result = Pine._extract_save_result(payload)

        assert result is not None
        assert result["scriptIdPart"] == "USER;new_script"

    def test_returns_none_for_string(self) -> None:
        """Verify string payload returns None."""
        result = Pine._extract_save_result("not a dict")
        assert result is None

    def test_returns_none_for_empty_dict(self) -> None:
        """Verify empty dict returns None."""
        result = Pine._extract_save_result({})
        assert result is None

    def test_returns_none_for_empty_result(self) -> None:
        """Verify empty result returns None."""
        result = Pine._extract_save_result({"result": {}})
        assert result is None

    def test_returns_none_for_empty_meta_info(self) -> None:
        """Verify empty metaInfo returns None."""
        result = Pine._extract_save_result({"result": {"metaInfo": {}}})
        assert result is None

    def test_returns_none_when_no_script_id(self) -> None:
        """Verify None when scriptIdPart missing from metaInfo."""
        payload = {"result": {"metaInfo": {"description": "Some description"}}}
        result = Pine._extract_save_result(payload)
        assert result is None

    def test_returns_none_for_none_payload(self) -> None:
        """Verify None payload returns None."""
        result = Pine._extract_save_result(None)
        assert result is None

    def test_returns_none_for_list_payload(self) -> None:
        """Verify list payload returns None."""
        result = Pine._extract_save_result([1, 2, 3])
        assert result is None


class TestBuildPineHeaders:
    """Test _build_pine_headers() method."""

    def test_includes_cookie(self) -> None:
        """Verify cookie included in headers."""
        scraper = Pine(cookie="test_cookie")
        headers = scraper._build_pine_headers()

        assert headers["cookie"] == "test_cookie"

    def test_includes_accept(self) -> None:
        """Verify accept header set."""
        scraper = Pine(cookie="test")
        headers = scraper._build_pine_headers()

        assert headers["accept"] == "*/*"

    def test_includes_origin(self) -> None:
        """Verify origin header set."""
        scraper = Pine(cookie="test")
        headers = scraper._build_pine_headers()

        assert headers["origin"] == "https://in.tradingview.com"

    def test_includes_referer(self) -> None:
        """Verify referer header set."""
        scraper = Pine(cookie="test")
        headers = scraper._build_pine_headers()

        assert headers["referer"] == "https://in.tradingview.com/"

    def test_includes_user_agent(self) -> None:
        """Verify User-Agent included from base."""
        scraper = Pine(cookie="test")
        headers = scraper._build_pine_headers()

        assert "User-Agent" in headers

    def test_returns_new_dict(self) -> None:
        """Verify returned dict is independent."""
        scraper = Pine(cookie="test")
        headers1 = scraper._build_pine_headers()
        headers1["new_key"] = "value"

        headers2 = scraper._build_pine_headers()
        assert "new_key" not in headers2


class TestPineInit:
    """Test Pine class initialization."""

    def test_default_values(self) -> None:
        """Verify default initialization values."""
        scraper = Pine()

        assert scraper.export_result is False
        assert scraper.export_type == "json"
        assert scraper.timeout == 10

    def test_custom_export_result(self) -> None:
        """Verify custom export_result accepted."""
        scraper = Pine(export_result=True)
        assert scraper.export_result is True

    def test_custom_export_type(self) -> None:
        """Verify custom export_type accepted."""
        scraper = Pine(export_type="csv")
        assert scraper.export_type == "csv"

    def test_custom_timeout(self) -> None:
        """Verify custom timeout accepted."""
        scraper = Pine(timeout=30)
        assert scraper.timeout == 30

    def test_cookie_from_argument(self) -> None:
        """Verify cookie from argument."""
        scraper = Pine(cookie="arg_cookie")
        assert scraper.cookie == "arg_cookie"

    def test_cookie_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify cookie from environment variable."""
        monkeypatch.setenv("TRADINGVIEW_COOKIE", "env_cookie")
        scraper = Pine()
        assert scraper.cookie == "env_cookie"

    def test_cookie_argument_overrides_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify argument overrides environment variable."""
        monkeypatch.setenv("TRADINGVIEW_COOKIE", "env_cookie")
        scraper = Pine(cookie="arg_cookie")
        assert scraper.cookie == "arg_cookie"


class TestConstants:
    """Test module constants."""

    def test_pine_facade_base_url(self) -> None:
        """Verify Pine facade base URL."""
        from tv_scraper.scrapers.scripts.pine import PINE_FACADE_BASE_URL

        assert PINE_FACADE_BASE_URL == "https://pine-facade.tradingview.com/pine-facade"

    def test_pine_origin(self) -> None:
        """Verify Pine origin URL."""
        from tv_scraper.scrapers.scripts.pine import PINE_ORIGIN

        assert PINE_ORIGIN == "https://in.tradingview.com"

    def test_pine_filter_saved(self) -> None:
        """Verify Pine filter saved value."""
        from tv_scraper.scrapers.scripts.pine import PINE_FILTER_SAVED

        assert PINE_FILTER_SAVED == "saved"
