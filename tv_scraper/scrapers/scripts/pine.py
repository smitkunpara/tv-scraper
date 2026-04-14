"""Pine scraper for TradingView Pine script operations."""

import logging
from typing import Any
from urllib.parse import quote

from tv_scraper.core.base import BaseScraper, catch_errors

logger = logging.getLogger(__name__)

PINE_FACADE_BASE_URL = "https://pine-facade.tradingview.com/pine-facade"
PINE_ORIGIN = "https://in.tradingview.com"
PINE_FILTER_SAVED = "saved"


class Pine(BaseScraper):
    """Scraper for TradingView Pine Script operations.

    Cookie authentication is mandatory for all Pine facade endpoints.

    Args:
        export: Export format, ``"json"`` or ``"csv"``.
            If ``None`` (default), results are not exported.
        timeout: HTTP request timeout in seconds.
        cookie: TradingView session cookie string. Falls back to
            ``TRADINGVIEW_COOKIE`` environment variable if not provided.
    """

    def __init__(
        self,
        export: str | None = None,
        timeout: int = 10,
        cookie: str | None = None,
    ) -> None:
        super().__init__(
            export=export,
            timeout=timeout,
            cookie=cookie,
        )

    @catch_errors
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
        params = {"filter": PINE_FILTER_SAVED}

        payload, error_msg = self._request("GET", url, headers=headers, params=params)

        if error_msg:
            return self._error_response(error_msg)

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

    @catch_errors
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

        source_error = self._validate_non_empty(source, "Source code")
        if source_error:
            return self._error_response(source_error)

        headers = self._build_pine_headers()

        url = f"{PINE_FACADE_BASE_URL}/translate_light"
        params = {"v": "3"}

        payload, error_msg = self._request(
            "POST",
            url,
            headers=headers,
            params=params,
            files={"source": (None, source)},
        )

        if error_msg:
            return self._error_response(error_msg)

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

        if errors:
            return self._error_response(
                "Pine script validation failed.",
                errors=errors,
                warnings=warnings,
            )

        if warnings:
            return self._success_response(None, warnings=warnings)
        return self._success_response(None)

    @catch_errors
    def get_script(self, pine_id: str, version: str) -> dict[str, Any]:
        """Fetch a saved Pine script by script ID and version.

        Args:
            pine_id: Script identifier (for example, ``USER;abc123``).
            version: Script version (for example, ``5.0``).

        Returns:
            Standardized response dict.
        """
        cookie_error = self._validate_cookie_required()
        if cookie_error:
            return cookie_error

        pine_id_error = self._validate_non_empty(pine_id, "Pine script ID")
        if pine_id_error:
            return self._error_response(pine_id_error)

        version_error = self._validate_non_empty(version, "Script version")
        if version_error:
            return self._error_response(version_error)

        headers = self._build_pine_headers()

        encoded_pine_id = quote(pine_id, safe="")
        encoded_version = quote(version, safe="")
        url = f"{PINE_FACADE_BASE_URL}/get/{encoded_pine_id}/{encoded_version}"

        payload, error_msg = self._request("GET", url, headers=headers)

        if error_msg:
            return self._error_response(error_msg)

        if not isinstance(payload, dict):
            return self._error_response(
                "Unexpected response format from Pine get endpoint."
            )

        script_data = self._map_script_details(payload, pine_id, version)
        if script_data is None:
            return self._error_response(
                "Unexpected script payload from Pine get endpoint."
            )

        if self.export_result:
            self._export(data=script_data, symbol=pine_id, data_category="pine_script")

        return self._success_response(script_data)

    @catch_errors
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

        name_error = self._validate_non_empty(name, "Script name")
        if name_error:
            return self._error_response(name_error)
        source_error = self._validate_non_empty(source, "Source code")
        if source_error:
            return self._error_response(source_error)

        original_metadata = self._last_metadata.copy()
        validation = self.validate_script(source)
        self._last_metadata = original_metadata
        if validation["status"] != "success":
            validation_meta = validation.get("metadata", {})
            return self._error_response(
                validation["error"] or "Pine script validation failed.",
                warnings=validation_meta.get("warnings"),
                errors=validation_meta.get("errors"),
            )

        headers = self._build_pine_headers()

        url = f"{PINE_FACADE_BASE_URL}/save/new"
        params = {
            "name": name,
            "allow_overwrite": "true",
        }

        payload, error_msg = self._request(
            "POST",
            url,
            headers=headers,
            params=params,
            files={"source": (None, source)},
        )

        if error_msg:
            return self._error_response(error_msg)

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
        return self._success_response(data)

    @catch_errors
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

        pine_id_error = self._validate_non_empty(pine_id, "Pine script ID")
        if pine_id_error:
            return self._error_response(pine_id_error)
        name_error = self._validate_non_empty(name, "Script name")
        if name_error:
            return self._error_response(name_error)
        source_error = self._validate_non_empty(source, "Source code")
        if source_error:
            return self._error_response(source_error)

        original_metadata = self._last_metadata.copy()
        validation = self.validate_script(source)
        self._last_metadata = original_metadata
        if validation["status"] != "success":
            validation_meta = validation.get("metadata", {})
            return self._error_response(
                validation["error"] or "Pine script validation failed.",
                warnings=validation_meta.get("warnings"),
                errors=validation_meta.get("errors"),
            )

        headers = self._build_pine_headers()

        encoded_pine_id = quote(pine_id, safe="")
        url = f"{PINE_FACADE_BASE_URL}/save/next/{encoded_pine_id}"
        params = {
            "allow_create_new": "false",
            "name": name,
        }

        payload, error_msg = self._request(
            "POST",
            url,
            headers=headers,
            params=params,
            files={"source": (None, source)},
        )

        if error_msg:
            return self._error_response(error_msg)

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
        return self._success_response(data)

    @catch_errors
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

        pine_id_error = self._validate_non_empty(pine_id, "Pine script ID")
        if pine_id_error:
            return self._error_response(pine_id_error)

        headers = self._build_pine_headers()
        encoded_pine_id = quote(pine_id, safe="")
        url = f"{PINE_FACADE_BASE_URL}/delete/{encoded_pine_id}"

        response, error_msg = self._request(
            "POST",
            url,
            headers=headers,
        )

        if error_msg:
            # If the error is JSON decode, but the text is "ok", `_request` might return "Failed to parse API response".
            # We can't access the text here, but if that happens, we'll see it in tests.
            # Assuming TV returns `"ok"`, not `ok`.
            return self._error_response(error_msg)

        if response != "ok":
            return self._error_response(
                f"Pine delete endpoint returned unexpected response: {response}"
            )

        return self._success_response({"id": pine_id})

    def _validate_cookie_required(self) -> dict[str, Any] | None:
        if self.cookie:
            return None
        return self._error_response(
            "TradingView cookie is required for Pine Script operations. "
            "Provide it via the cookie argument or TRADINGVIEW_COOKIE environment variable."
        )

    @staticmethod
    def _validate_non_empty(value: str, field_name: str) -> str | None:
        if value and value.strip():
            return None
        return f"{field_name} cannot be empty."

    def _build_pine_headers(self) -> dict[str, str]:
        """Build headers expected by Pine facade endpoints."""
        headers = dict(self._headers)
        headers["cookie"] = self.cookie if self.cookie is not None else ""
        headers["accept"] = "*/*"
        headers["origin"] = PINE_ORIGIN
        headers["referer"] = f"{PINE_ORIGIN}/"
        return headers

    @staticmethod
    def _map_script_item(item: dict[str, Any]) -> dict[str, Any]:
        modified = item.get("modified", 0)
        if not isinstance(modified, int) or modified < 0:
            modified = 0
        return {
            "id": item.get("scriptIdPart", ""),
            "name": item.get("scriptName") or item.get("scriptTitle", ""),
            "version": item.get("version") or item.get("scriptVersion"),
            "modified": modified,
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
        script_id = meta_info.get("scriptIdPart")
        if not script_id:
            return None
        return meta_info

    @staticmethod
    def _map_script_details(
        payload: dict[str, Any], pine_id: str, version: str
    ) -> dict[str, Any] | None:
        source = payload.get("source")
        if not isinstance(source, str):
            return None

        script_id = payload.get("scriptIdPart")
        if not isinstance(script_id, str) or not script_id:
            script_id = pine_id

        script_version = payload.get("version")
        if not isinstance(script_version, str) or not script_version:
            script_version = version

        script_name = payload.get("scriptName")
        script_title = payload.get("scriptTitle")
        if not isinstance(script_name, str):
            script_name = script_title if isinstance(script_title, str) else ""
        if not isinstance(script_title, str):
            script_title = script_name

        extra = payload.get("extra")
        if not isinstance(extra, dict):
            extra = {}

        return {
            "id": script_id,
            "name": script_name,
            "title": script_title,
            "version": script_version,
            "last_version": payload.get("lastVersionMaj"),
            "created": payload.get("created"),
            "updated": payload.get("updated"),
            "source": source,
            "extra": extra,
        }
