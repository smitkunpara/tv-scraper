"""Pine scraper for TradingView Pine script operations."""

import logging
import os
import re
from typing import Any

from tv_scraper.core.base import BaseScraper

logger = logging.getLogger(__name__)

PINE_FACADE_BASE_URL = "https://pine-facade.tradingview.com/pine-facade"


class Pine(BaseScraper):
    """Scraper for TradingView Pine Script operations.

    Cookie authentication is mandatory for all Pine facade endpoints.

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

    def validate_script(self, source: str) -> dict[str, Any]:
        """Validate Pine source code using TradingView translate_light endpoint.

        Args:
            source: Raw Pine source code.

        Returns:
            Standardized response dict. Validation warnings are returned in
            metadata and logged. Validation errors return a failed response.
        """
        cookie_error = self._validate_cookie_required()
        if cookie_error:
            return cookie_error

        if not source.strip():
            return self._error_response("Source code cannot be empty.")

        headers = dict(self._headers)
        headers["cookie"] = self._cookie or ""

        url = f"{PINE_FACADE_BASE_URL}/translate_light"
        params = {"v": "3"}

        try:
            response = self._make_request(
                url,
                method="POST",
                headers=headers,
                params=params,
                files={"source": (None, source)},
            )
            payload = response.json()
        except Exception as exc:
            logger.error("Failed to validate Pine source: %s", exc)
            return self._error_response(self._map_request_error(exc))

        if not isinstance(payload, dict):
            return self._error_response(
                "Unexpected response format from Pine validation endpoint."
            )

        result_obj = payload.get("result")
        if not isinstance(result_obj, dict):
            return self._error_response(
                "Unexpected validation payload from Pine endpoint."
            )

        errors = result_obj.get("errors") or []
        warnings = result_obj.get("warnings") or []

        if warnings:
            logger.warning("Pine validation warnings: %s", warnings)

        if errors:
            return self._error_response(
                "Pine script validation failed.",
                errors=errors,
                warnings=warnings,
            )

        return self._success_response(
            None,
            errors=[],
            warnings=warnings,
        )

    def create_script(
        self,
        name: str,
        source: str,
        allow_overwrite: bool = True,
    ) -> dict[str, Any]:
        """Create a new Pine script in the authenticated TradingView account.

        Args:
            name: Script name.
            source: Raw Pine source code.
            allow_overwrite: Whether to allow overwrite when name already exists.

        Returns:
            Standardized response dict.
        """
        cookie_error = self._validate_cookie_required()
        if cookie_error:
            return cookie_error

        if not name.strip():
            return self._error_response("Script name cannot be empty.")
        if not source.strip():
            return self._error_response("Source code cannot be empty.")

        validation = self.validate_script(source)
        if validation["status"] != "success":
            return self._error_response(
                validation["error"] or "Pine script validation failed.",
                **validation.get("metadata", {}),
            )

        headers = dict(self._headers)
        headers["cookie"] = self._cookie or ""

        url = f"{PINE_FACADE_BASE_URL}/save/new"
        params = {
            "name": name,
            "allow_overwrite": "true" if allow_overwrite else "false",
        }

        try:
            response = self._make_request(
                url,
                method="POST",
                headers=headers,
                params=params,
                files={"source": (None, source)},
            )
            payload = response.json()
        except Exception as exc:
            logger.error("Failed to create Pine script '%s': %s", name, exc)
            return self._error_response(self._map_request_error(exc))

        script_result = self._extract_save_result(payload)
        if script_result is None:
            return self._error_response(
                "Unexpected response format from Pine create endpoint."
            )

        data = {
            "id": script_result.get("scriptIdPart", ""),
            "name": script_result.get("shortDescription")
            or script_result.get("description")
            or name,
            "modified": script_result.get("modified", 0),
        }
        return self._success_response(
            data,
            warnings=validation.get("metadata", {}).get("warnings", []),
        )

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
    def _extract_save_result(payload: Any) -> dict[str, Any] | None:
        if not isinstance(payload, dict):
            return None
        result_obj = payload.get("result")
        if not isinstance(result_obj, dict):
            return None
        meta_info = result_obj.get("metaInfo")
        if not isinstance(meta_info, dict):
            return None

        return {
            "scriptIdPart": meta_info.get("scriptIdPart", ""),
            "description": meta_info.get("description", ""),
            "shortDescription": meta_info.get("shortDescription", ""),
            "modified": result_obj.get("modified", 0),
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
