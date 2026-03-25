"""Live API tests for Pine scraper endpoints.

These tests use real TradingView Pine endpoints and require an authenticated
cookie from environment variables.
"""

import os
import time
from typing import Any

import pytest

from tv_scraper import Pine
from tv_scraper.core.constants import STATUS_SUCCESS


def _get_live_cookie() -> str | None:
    """Get cookie from supported environment variables."""
    return os.environ.get("TRADINGVIEW_COOKIE") or os.environ.get("TV_COOKIE")


@pytest.mark.live
class TestLivePine:
    """Live tests for Pine scraper endpoints."""

    @pytest.fixture(autouse=True)
    def _require_cookie(self) -> str:
        cookie = _get_live_cookie()
        if not cookie:
            pytest.skip(
                "Live Pine tests require TRADINGVIEW_COOKIE (or TV_COOKIE) env var."
            )
        return cookie

    def test_live_list_saved_scripts(self, _require_cookie: str) -> None:
        """Verify saved-script listing works with authenticated cookie."""
        scraper = Pine(cookie=_require_cookie)
        result = scraper.list_saved_scripts()

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert isinstance(result["data"], list)

        if result["data"]:
            first: dict[str, Any] = result["data"][0]
            assert "id" in first
            assert "name" in first
            assert "modified" in first

    def test_live_validate_script(self, _require_cookie: str) -> None:
        """Verify Pine source validation endpoint works."""
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

    def test_live_create_edit_list_delete_workflow(self, _require_cookie: str) -> None:
        """Verify create, edit, list, and delete workflow end-to-end."""
        scraper = Pine(cookie=_require_cookie)

        script_name = f"auto_test_{int(time.time())}"
        source_v1 = "\n".join(
            [
                "//@version=6",
                f'indicator("{script_name}")',
                "//test 1 testing file screation",
                "plot(close)",
            ]
        )

        created = scraper.create_script(name=script_name, source=source_v1)
        assert created["status"] == STATUS_SUCCESS, created.get("error")
        script_id = str((created.get("data") or {}).get("id") or "")
        assert script_id

        source_v2 = source_v1.replace(
            "//test 1 testing file screation",
            "//test 1 testing file screation\n//test 2 testing editing file",
        )
        edited = scraper.edit_script(
            pine_id=script_id,
            name=script_name,
            source=source_v2,
        )
        assert edited["status"] == STATUS_SUCCESS, edited.get("error")

        listed = scraper.list_saved_scripts()
        assert listed["status"] == STATUS_SUCCESS, listed.get("error")

        found = any(
            isinstance(item, dict)
            and str(item.get("id") or "") == script_id
            and script_name in str(item.get("name") or "")
            for item in listed["data"]
        )
        assert found, f"Created script not found in saved list: {script_id}"

        deleted = scraper.delete_script(script_id)
        assert deleted["status"] == STATUS_SUCCESS, deleted.get("error")
