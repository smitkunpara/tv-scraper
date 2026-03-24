"""Pine scraper for listing user TradingView Pine scripts."""

import logging
import os
import re
from typing import Any

from tv_scraper.core.base import BaseScraper

logger = logging.getLogger(__name__)

PINE_FACADE_BASE_URL = "https://pine-facade.tradingview.com/pine-facade"


class Pine(BaseScraper):
    """Scraper for TradingView Pine Script operations.

    This class currently supports listing saved scripts. Cookie authentication
    is mandatory for all Pine facade endpoints.

    Args:
        export_result: Whether to export results to file.
        export_type: Export format, ``"json"`` or ``"csv"``.
        timeout: HTTP request timeout in seconds.
        cookie: TradingView session cookie string. Falls back to
            ``TRADINGVIEW_COOKIE`` environment variable if not provided.
    """

    def __init__(
        self,
        export_result: bool = False,
        export_type: str = "json",
        timeout: int = 10,
        cookie: str | None = None,
    ) -> None:
        super().__init__(
            export_result=export_result,
            export_type=export_type,
            timeout=timeout,
        )
        self._cookie: str | None = cookie or os.environ.get("TRADINGVIEW_COOKIE")

    def list_saved_scripts(self) -> dict[str, Any]:
        """List the authenticated user's saved Pine scripts.

        Returns:
            Standardized response dict with keys ``status``, ``data``,
            ``metadata``, ``error``.
        """
        cookie_error = self._validate_cookie_required()
        if cookie_error:
            return cookie_error

        headers = dict(self._headers)
        headers["cookie"] = self._cookie or ""

        url = f"{PINE_FACADE_BASE_URL}/list"
        params = {"filter": "saved"}

        try:
            response = self._make_request(
                url, method="GET", headers=headers, params=params
            )
            payload = response.json()
        except Exception as exc:
            logger.error("Failed to list Pine scripts: %s", exc)
            return self._error_response(self._map_request_error(exc))

        if not isinstance(payload, list):
            logger.error(
                "Unexpected Pine list payload type: %s", type(payload).__name__
            )
            return self._error_response(
                "Unexpected response format from Pine list endpoint."
            )

        scripts = [self._map_script_item(item) for item in payload]

        if self.export_result:
            self._export(
                data=scripts, symbol="pine_saved_scripts", data_category="pine"
            )

        return self._success_response(scripts, total=len(scripts), filter="saved")

    def _validate_cookie_required(self) -> dict[str, Any] | None:
        if self._cookie:
            return None
        return self._error_response(
            "TradingView cookie is required for Pine Script operations. "
            "Provide it via the cookie argument or TRADINGVIEW_COOKIE environment variable."
        )

    @staticmethod
    def _map_script_item(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item.get("scriptIdPart", ""),
            "name": item.get("scriptName") or item.get("scriptTitle", ""),
            "modified": item.get("modified", 0),
        }

    @staticmethod
    def _map_request_error(exc: Exception) -> str:
        message = str(exc)
        status_match = re.search(r"HTTP error\s+(\d+)", message)
        status_code = int(status_match.group(1)) if status_match else None

        if status_code in {401, 403}:
            return "Invalid TradingView cookie. Please provide a valid authenticated cookie."
        if status_code == 429:
            return "TradingView rate limit reached. Please try again later."
        if status_code and status_code >= 500:
            return "TradingView Pine service is temporarily unavailable. Please try again later."
        if status_code:
            return f"Pine API request failed with status {status_code}."

        return message or "Failed to complete Pine API request."
