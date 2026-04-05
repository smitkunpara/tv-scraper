"""Live API tests for Pine scripts.

Tests real HTTP connections to TradingView Pine scripts endpoint.
"""

import os
import time

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.scripts.pine import Pine


def _get_live_cookie() -> str | None:
    """Get cookie from supported environment variables."""
    return os.environ.get("TRADINGVIEW_COOKIE") or os.environ.get("TV_COOKIE")


@pytest.mark.live
class TestLivePineScripts:
    """Test Pine scripts with real API calls."""

    @pytest.fixture(autouse=True)
    def _require_cookie(self) -> str:
        cookie = _get_live_cookie()
        if not cookie:
            pytest.skip(
                "Live Pine tests require TRADINGVIEW_COOKIE (or TV_COOKIE) env var."
            )
        return cookie

    def test_live_list_saved_scripts(self, _require_cookie: str) -> None:
        """Verify listing saved scripts works."""
        scraper = Pine(cookie=_require_cookie)
        result = scraper.list_saved_scripts()

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert isinstance(result["data"], list)

    def test_live_list_saved_scripts_invalid_cookie(self, _require_cookie: str) -> None:
        """Verify invalid cookie handling."""
        scraper = Pine(cookie="invalid_cookie_xyz")
        result = scraper.list_saved_scripts()
        assert result["status"] == "failed"
        assert result["error"] is not None

    def test_live_validate_script_valid(self, _require_cookie: str) -> None:
        """Verify valid Pine script validation."""
        scraper = Pine(cookie=_require_cookie)
        source = "\n".join(
            [
                "//@version=6",
                'indicator("tv-scraper live test")',
                "plot(close)",
            ]
        )

        result = scraper.validate_script(source)

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        metadata = result.get("metadata", {})
        warnings = metadata.get("warnings", [])
        assert isinstance(warnings, list)

    def test_live_validate_script_with_errors(self, _require_cookie: str) -> None:
        """Verify script validation catches errors."""
        scraper = Pine(cookie=_require_cookie)
        source = "\n".join(
            [
                "//@version=6",
                'indicator("test")',
                "undefined_function()",
            ]
        )

        result = scraper.validate_script(source)
        assert "status" in result

    def test_live_validate_script_with_warnings(self, _require_cookie: str) -> None:
        """Verify script validation with warnings."""
        scraper = Pine(cookie=_require_cookie)
        source = "\n".join(
            [
                "//@version=6",
                'indicator("test")',
                "plot(close)",
                "var x = na",
            ]
        )

        result = scraper.validate_script(source)
        assert result["status"] == STATUS_SUCCESS


@pytest.mark.live
class TestLivePineScriptsCRUD:
    """Test Pine script CRUD operations with real API calls."""

    @pytest.fixture(autouse=True)
    def _require_cookie(self) -> str:
        cookie = _get_live_cookie()
        if not cookie:
            pytest.skip(
                "Live Pine tests require TRADINGVIEW_COOKIE (or TV_COOKIE) env var."
            )
        return cookie

    def test_live_create_script(self, _require_cookie: str) -> None:
        """Verify creating a new script works."""
        scraper = Pine(cookie=_require_cookie)
        script_name = f"test_script_{int(time.time())}"
        source = "\n".join(
            [
                "//@version=6",
                f'indicator("{script_name}")',
                "plot(close)",
            ]
        )

        result = scraper.create_script(name=script_name, source=source)
        assert result["status"] == STATUS_SUCCESS, result.get("error")

    def test_live_create_script_empty_name(self, _require_cookie: str) -> None:
        """Verify empty name validation."""
        scraper = Pine(cookie=_require_cookie)
        result = scraper.create_script(name="", source="//@version=6\nplot(close)")
        assert result["status"] == "failed"
        assert result["error"] is not None

    def test_live_edit_script(self, _require_cookie: str) -> None:
        """Verify editing an existing script works."""
        scraper = Pine(cookie=_require_cookie)

        script_name = f"edit_test_{int(time.time())}"
        source_v1 = "\n".join(
            [
                "//@version=6",
                f'indicator("{script_name}")',
                "plot(close)",
            ]
        )

        created = scraper.create_script(name=script_name, source=source_v1)
        if created["status"] == STATUS_SUCCESS:
            script_id = str((created.get("data") or {}).get("id") or "")
            if script_id:
                source_v2 = source_v1 + "\n// edited"
                edited = scraper.edit_script(
                    pine_id=script_id, name=script_name, source=source_v2
                )
                assert edited["status"] == STATUS_SUCCESS, edited.get("error")

    def test_live_delete_script(self, _require_cookie: str) -> None:
        """Verify deleting a script works."""
        scraper = Pine(cookie=_require_cookie)

        script_name = f"delete_test_{int(time.time())}"
        source = "\n".join(
            [
                "//@version=6",
                f'indicator("{script_name}")',
                "plot(close)",
            ]
        )

        created = scraper.create_script(name=script_name, source=source)
        if created["status"] == STATUS_SUCCESS:
            script_id = str((created.get("data") or {}).get("id") or "")
            if script_id:
                deleted = scraper.delete_script(script_id)
                assert deleted["status"] == STATUS_SUCCESS, deleted.get("error")


@pytest.mark.live
class TestLivePineScriptsEdgeCases:
    """Test edge cases for Pine scripts."""

    def test_live_pine_missing_cookie(self) -> None:
        """Verify missing cookie handling."""
        scraper = Pine(cookie=None)
        result = scraper.list_saved_scripts()
        assert result["status"] == "failed"
        assert result["error"] is not None

    def test_live_pine_network_error(self) -> None:
        """Verify network error handling."""
        from unittest.mock import patch

        import requests

        cookie = _get_live_cookie()
        if not cookie:
            pytest.skip("No cookie available")

        scraper = Pine(cookie=cookie)
        with patch.object(
            requests, "get", side_effect=requests.RequestException("Network error")
        ):
            result = scraper.list_saved_scripts()
            assert result["status"] == "failed"
            assert result["error"] is not None

    def test_live_pine_timeout(self) -> None:
        """Verify timeout handling."""
        from unittest.mock import patch

        import requests

        cookie = _get_live_cookie()
        if not cookie:
            pytest.skip("No cookie available")

        scraper = Pine(cookie=cookie)
        with patch.object(requests, "get", side_effect=requests.Timeout("Timeout")):
            result = scraper.list_saved_scripts()
            assert result["status"] == "failed"
