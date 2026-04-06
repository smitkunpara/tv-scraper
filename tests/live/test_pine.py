"""Live API tests for Pine scripts.

Tests real HTTP connections to TradingView Pine facade endpoints.
Requires TRADINGVIEW_COOKIE environment variable.
"""

import os
import time

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.scripts.pine import Pine


def _get_cookie() -> str | None:
    """Get cookie from environment variables."""
    return os.environ.get("TRADINGVIEW_COOKIE") or os.environ.get("TV_COOKIE")


@pytest.fixture
def cookie() -> str | None:
    """Fixture to get cookie or skip test."""
    cookie = _get_cookie()
    if not cookie:
        pytest.skip("TRADINGVIEW_COOKIE environment variable not set")
    return cookie


@pytest.fixture
def scraper(cookie: str) -> Pine:
    """Create Pine scraper instance with valid cookie."""
    return Pine(cookie=cookie)


@pytest.fixture
def scraper_no_cookie() -> Pine:
    """Create Pine scraper instance without cookie."""
    return Pine(cookie=None)


@pytest.mark.live
class TestListSavedScripts:
    """Test list_saved_scripts() method."""

    def test_list_saved_scripts_returns_list(self, scraper: Pine) -> None:
        """Verify list_saved_scripts returns a list of scripts."""
        result = scraper.list_saved_scripts()
        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert isinstance(result["data"], list)

    def test_list_saved_scripts_structure(self, scraper: Pine) -> None:
        """Verify script items have expected structure."""
        result = scraper.list_saved_scripts()
        assert result["status"] == STATUS_SUCCESS
        for script in result["data"]:
            assert "id" in script
            assert "name" in script
            assert "modified" in script

    def test_list_saved_scripts_invalid_cookie(self, cookie: str) -> None:
        """Verify invalid cookie is rejected by API."""
        scraper = Pine(cookie="invalid_cookie_xyz123")
        result = scraper.list_saved_scripts()
        assert "status" in result
        if result["status"] == "failed":
            assert result["error"] is not None
        else:
            pytest.skip("TradingView may not reject invalid cookies immediately")

    def test_list_saved_scripts_no_cookie(self, scraper_no_cookie: Pine) -> None:
        """Verify missing cookie returns error response."""
        result = scraper_no_cookie.list_saved_scripts()
        assert result["status"] == "failed"
        assert "cookie" in result["error"].lower()


@pytest.mark.live
class TestValidateScript:
    """Test validate_script() method."""

    def test_validate_valid_script(self, scraper: Pine) -> None:
        """Verify valid Pine script passes validation."""
        source = "\n".join(
            [
                "//@version=6",
                'indicator("Test Script")',
                "plot(close)",
            ]
        )
        result = scraper.validate_script(source)
        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert "warnings" in result.get("metadata", {})

    def test_validate_script_with_errors(self, scraper: Pine) -> None:
        """Verify script with errors fails validation."""
        source = "\n".join(
            [
                "//@version=6",
                'indicator("Test")',
                "undefined_function_that_does_not_exist()",
            ]
        )
        result = scraper.validate_script(source)
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "errors" in result.get("metadata", {})

    def test_validate_script_with_warnings(self, scraper: Pine) -> None:
        """Verify script with warnings still passes validation."""
        source = "\n".join(
            [
                "//@version=6",
                'indicator("Test")',
                "plot(close)",
                "var x = na",
            ]
        )
        result = scraper.validate_script(source)
        assert result["status"] == STATUS_SUCCESS
        assert len(result.get("metadata", {}).get("warnings", [])) > 0

    def test_validate_empty_source(self, scraper_no_cookie: Pine) -> None:
        """Verify empty source returns error."""
        result = scraper_no_cookie.validate_script("")
        assert result["status"] == "failed"

    def test_validate_no_cookie(self, scraper_no_cookie: Pine) -> None:
        """Verify missing cookie returns error."""
        result = scraper_no_cookie.validate_script("//@version=6\nplot(close)")
        assert result["status"] == "failed"
        assert "cookie" in result["error"].lower()


@pytest.mark.live
class TestCreateScript:
    """Test create_script() method."""

    def test_create_script_success(self, scraper: Pine) -> None:
        """Verify script creation works with unique name."""
        timestamp = int(time.time())
        script_name = f"test_create_{timestamp}"
        source = "\n".join(
            [
                "//@version=6",
                f'indicator("{script_name}")',
                "plot(close)",
            ]
        )
        result = scraper.create_script(name=script_name, source=source)
        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert result["data"] is not None
        assert "id" in result["data"]
        assert result["data"]["name"] == script_name

    def test_create_script_empty_name(self, scraper: Pine) -> None:
        """Verify empty name returns error."""
        result = scraper.create_script(name="", source="//@version=6\nplot(close)")
        assert result["status"] == "failed"
        assert "name" in result["error"].lower()

    def test_create_script_whitespace_name(self, scraper: Pine) -> None:
        """Verify whitespace-only name returns error."""
        result = scraper.create_script(name="   ", source="//@version=6\nplot(close)")
        assert result["status"] == "failed"

    def test_create_script_empty_source(self, scraper: Pine) -> None:
        """Verify empty source returns error."""
        result = scraper.create_script(name="TestScript", source="")
        assert result["status"] == "failed"
        assert "source" in result["error"].lower()

    def test_create_script_no_cookie(self, scraper_no_cookie: Pine) -> None:
        """Verify missing cookie returns error."""
        result = scraper_no_cookie.create_script(
            name="TestScript", source="//@version=6\nplot(close)"
        )
        assert result["status"] == "failed"
        assert "cookie" in result["error"].lower()

    def test_create_script_with_invalid_source(self, scraper: Pine) -> None:
        """Verify script with errors is rejected during creation."""
        timestamp = int(time.time())
        result = scraper.create_script(
            name=f"test_invalid_{timestamp}", source="//@version=6\nundefined()"
        )
        assert result["status"] == "failed"


@pytest.mark.live
class TestEditScript:
    """Test edit_script() method."""

    def test_edit_script_success(self, scraper: Pine) -> None:
        """Verify script editing works."""
        timestamp = int(time.time())
        script_name = f"edit_test_{timestamp}"
        source_v1 = "\n".join(
            [
                "//@version=6",
                f'indicator("{script_name}")',
                "plot(close)",
            ]
        )
        source_v2 = source_v1 + "\n// Edited version"

        created = scraper.create_script(name=script_name, source=source_v1)
        if created["status"] == STATUS_SUCCESS:
            script_id = created["data"].get("id", "")
            if script_id:
                result = scraper.edit_script(
                    pine_id=script_id, name=script_name, source=source_v2
                )
                assert result["status"] == STATUS_SUCCESS, result.get("error")

    def test_edit_nonexistent_script(self, scraper: Pine) -> None:
        """Verify editing non-existent script fails."""
        result = scraper.edit_script(
            pine_id="USER;nonexistent_script_xyz",
            name="NonExistent",
            source="//@version=6\nplot(close)",
        )
        assert result["status"] == "failed"

    def test_edit_script_empty_id(self, scraper_no_cookie: Pine) -> None:
        """Verify empty script ID returns error."""
        result = scraper_no_cookie.edit_script(
            pine_id="", name="Test", source="//@version=6\nplot(close)"
        )
        assert result["status"] == "failed"

    def test_edit_script_empty_name(self, scraper_no_cookie: Pine) -> None:
        """Verify empty name returns error."""
        result = scraper_no_cookie.edit_script(
            pine_id="USER;test", name="", source="//@version=6\nplot(close)"
        )
        assert result["status"] == "failed"

    def test_edit_script_no_cookie(self, scraper_no_cookie: Pine) -> None:
        """Verify missing cookie returns error."""
        result = scraper_no_cookie.edit_script(
            pine_id="USER;test", name="Test", source="//@version=6\nplot(close)"
        )
        assert result["status"] == "failed"
        assert "cookie" in result["error"].lower()


@pytest.mark.live
class TestDeleteScript:
    """Test delete_script() method."""

    def test_delete_script_success(self, scraper: Pine) -> None:
        """Verify script deletion works."""
        timestamp = int(time.time())
        script_name = f"delete_test_{timestamp}"
        source = "\n".join(
            [
                "//@version=6",
                f'indicator("{script_name}")',
                "plot(close)",
            ]
        )

        created = scraper.create_script(name=script_name, source=source)
        if created["status"] == STATUS_SUCCESS:
            script_id = created["data"].get("id", "")
            if script_id:
                result = scraper.delete_script(script_id)
                assert result["status"] == STATUS_SUCCESS, result.get("error")
                assert result["data"]["id"] == script_id

    def test_delete_nonexistent_script(self, scraper: Pine) -> None:
        """Verify deleting non-existent script fails gracefully."""
        result = scraper.delete_script("USER;nonexistent_script_xyz")
        assert result["status"] == "failed"

    def test_delete_script_empty_id(self, scraper_no_cookie: Pine) -> None:
        """Verify empty script ID returns error."""
        result = scraper_no_cookie.delete_script("")
        assert result["status"] == "failed"

    def test_delete_script_no_cookie(self, scraper_no_cookie: Pine) -> None:
        """Verify missing cookie returns error."""
        result = scraper_no_cookie.delete_script("USER;test")
        assert result["status"] == "failed"
        assert "cookie" in result["error"].lower()


@pytest.mark.live
class TestPineScraperIntegration:
    """Integration tests for full CRUD workflow."""

    def test_full_crud_workflow(self, scraper: Pine) -> None:
        """Verify complete create, read, edit, delete workflow."""
        timestamp = int(time.time())
        script_name = f"crud_test_{timestamp}"
        source_v1 = "\n".join(
            [
                "//@version=6",
                f'indicator("{script_name}")',
                "plot(close)",
            ]
        )
        source_v2 = "\n".join(
            [
                "//@version=6",
                f'indicator("{script_name} v2")',
                "plot(close)",
                "plot(open)",
            ]
        )

        created = scraper.create_script(name=script_name, source=source_v1)
        assert created["status"] == STATUS_SUCCESS
        script_id = created["data"]["id"]

        listed = scraper.list_saved_scripts()
        assert listed["status"] == STATUS_SUCCESS
        assert any(s["id"] == script_id for s in listed["data"])

        edited = scraper.edit_script(
            pine_id=script_id, name=f"{script_name} v2", source=source_v2
        )
        assert edited["status"] == STATUS_SUCCESS

        deleted = scraper.delete_script(script_id)
        assert deleted["status"] == STATUS_SUCCESS
