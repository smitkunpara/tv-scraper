"""Pine scraper for TradingView Pine script operations."""

import logging
import os
from typing import Any
from urllib.parse import quote

import requests

from tv_scraper.core.base import BaseScraper

logger = logging.getLogger(__name__)

PINE_FACADE_BASE_URL = "https://pine-facade.tradingview.com/pine-facade"
PINE_ORIGIN = "https://in.tradingview.com"


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

        headers = self._build_pine_headers()

        url = f"{PINE_FACADE_BASE_URL}/list"
        params = {"filter": "saved"}

        try:
            response = requests.get(
                url, headers=headers, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
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

        return self._success_response(scripts)

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

        headers = self._build_pine_headers()

        url = f"{PINE_FACADE_BASE_URL}/translate_light"
        params = {"v": "3"}

        try:
            response = requests.post(
                url,
                headers=headers,
                params=params,
                files={"source": (None, source)},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
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
                source=source,
                errors=errors,
                warnings=warnings,
            )

        if warnings:
            return self._success_response(None, source=source, warnings=warnings)
        return self._success_response(None, source=source)

    def create_script(
        self,
        name: str,
        source: str,
    ) -> dict[str, Any]:
        """Create a new Pine script in the authenticated TradingView account.

        Args:
            name: Script name.
            source: Raw Pine source code.

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

        headers = self._build_pine_headers()

        url = f"{PINE_FACADE_BASE_URL}/save/new"
        params = {
            "name": name,
            "allow_overwrite": "true",
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                params=params,
                files={"source": (None, source)},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
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
            "warnings": validation.get("metadata", {}).get("warnings", []),
        }
        return self._success_response(
            data,
            name=name,
            source=source,
        )

    def edit_script(self, pine_id: str, name: str, source: str) -> dict[str, Any]:
        """Edit an existing Pine script by script ID.

        Args:
            pine_id: Script identifier (for example, ``USER;abc123``).
            name: Updated script name.
            source: Updated Pine source code.

        Returns:
            Standardized response dict.
        """
        cookie_error = self._validate_cookie_required()
        if cookie_error:
            return cookie_error

        if not pine_id.strip():
            return self._error_response("Pine script ID cannot be empty.")
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

        headers = self._build_pine_headers()

        encoded_pine_id = quote(pine_id, safe="")
        url = f"{PINE_FACADE_BASE_URL}/save/next/{encoded_pine_id}"
        params = {
            "allow_create_new": "false",
            "name": name,
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                params=params,
                files={"source": (None, source)},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            logger.error("Failed to edit Pine script '%s': %s", pine_id, exc)
            return self._error_response(self._map_request_error(exc))

        script_result = self._extract_save_result(payload)
        if script_result is None:
            return self._error_response(
                "Unexpected response format from Pine edit endpoint."
            )

        data = {
            "id": script_result.get("scriptIdPart", "") or pine_id,
            "name": script_result.get("shortDescription")
            or script_result.get("description")
            or name,
            "warnings": validation.get("metadata", {}).get("warnings", []),
        }
        return self._success_response(
            data,
            pine_id=pine_id,
            name=name,
            source=source,
        )

    def delete_script(self, pine_id: str) -> dict[str, Any]:
        """Delete an existing Pine script by script ID.

        Args:
            pine_id: Script identifier (for example, ``USER;abc123``).

        Returns:
            Standardized response dict.
        """
        cookie_error = self._validate_cookie_required()
        if cookie_error:
            return cookie_error

        if not pine_id.strip():
            return self._error_response("Pine script ID cannot be empty.")

        headers = self._build_pine_headers()
        encoded_pine_id = quote(pine_id, safe="")
        url = f"{PINE_FACADE_BASE_URL}/delete/{encoded_pine_id}"

        try:
            response = requests.post(
                url,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            response_text = response.text.strip().strip('"').lower()
        except requests.RequestException as exc:
            logger.error("Failed to delete Pine script '%s': %s", pine_id, exc)
            return self._error_response(self._map_request_error(exc))

        if response_text != "ok":
            return self._error_response(
                "Unexpected response from Pine delete endpoint.",
                pine_id=pine_id,
                response=response.text,
            )

        return self._success_response(
            {"id": pine_id, "deleted": True},
            pine_id=pine_id,
        )

    def _validate_cookie_required(self) -> dict[str, Any] | None:
        if self._cookie:
            return None
        return self._error_response(
            "TradingView cookie is required for Pine Script operations. "
            "Provide it via the cookie argument or TRADINGVIEW_COOKIE environment variable."
        )

    def _build_pine_headers(self) -> dict[str, str]:
        """Build headers expected by Pine facade endpoints."""
        headers = dict(self._headers)
        headers["cookie"] = self._cookie or ""
        headers["accept"] = "*/*"
        headers["origin"] = PINE_ORIGIN
        headers["referer"] = f"{PINE_ORIGIN}/"
        return headers

    @staticmethod
    def _map_script_item(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item.get("scriptIdPart", ""),
            "name": item.get("scriptName") or item.get("scriptTitle", ""),
            "version": item.get("version") or item.get("scriptVersion"),
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

    def _map_request_error(self, exc: Exception) -> str:
        status_code = None
        if isinstance(exc, requests.HTTPError) and exc.response is not None:
            status_code = exc.response.status_code

        if status_code in {401, 403}:
            return "Invalid TradingView cookie. Please provide a valid authenticated cookie."
        if status_code == 429:
            return "TradingView rate limit reached. Please try again later."
        if status_code and status_code >= 500:
            return "TradingView Pine service is temporarily unavailable. Please try again later."
        if status_code:
            return f"Pine API request failed with status {status_code}."

        return str(exc) or "Failed to complete Pine API request."
