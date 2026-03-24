"""Live API tests for Pine scraper endpoints.

These tests use real TradingView Pine endpoints and require an authenticated
cookie from environment variables.
"""

import os
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
        assert "warnings" in metadata
        assert isinstance(metadata["warnings"], list)
