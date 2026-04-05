"""Streaming utility functions: indicator metadata fetching."""

import logging
from typing import Any

import requests

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS

logger = logging.getLogger(__name__)

_INDICATOR_SEARCH_URL = "https://www.tradingview.com/pubscripts-suggest-json/?search="

_PINE_FACADE_URL = "https://pine-facade.tradingview.com/pine-facade/translate/{script_id}/{script_version}"

_PINE_LIST_URL = "https://pine-facade.tradingview.com/pine-facade/list?filter=standard"

BASE_STUDY_ID = 9


def fetch_tradingview_indicators(query: str) -> dict[str, Any]:
    """Search public TradingView indicators by name or author.

    Args:
        query: Search term to filter indicators.

    Returns:
        Standardized response dict with keys: ``status``, ``data``,
        ``metadata``, ``error``. ``data`` contains list of indicator dicts.
    """
    url = _INDICATOR_SEARCH_URL + query

    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        json_data = resp.json()

        results = json_data.get("results", [])
        filtered: list[dict[str, Any]] = []

        for indicator in results:
            name = indicator.get("scriptName", "")
            author = indicator.get("author", {}).get("username", "")
            if query.lower() in name.lower() or query.lower() in author.lower():
                filtered.append(
                    {
                        "scriptName": name,
                        "imageUrl": indicator.get("imageUrl", ""),
                        "author": author,
                        "agreeCount": indicator.get("agreeCount", 0),
                        "isRecommended": indicator.get("isRecommended", False),
                        "scriptIdPart": indicator.get("scriptIdPart", ""),
                        "version": indicator.get("version"),
                    }
                )
        return {
            "status": STATUS_SUCCESS,
            "data": filtered,
            "metadata": {"query": query},
            "error": None,
        }

    except requests.RequestException as exc:
        logger.error("Error fetching TradingView indicators: %s", exc)
        return {
            "status": STATUS_FAILED,
            "data": None,
            "metadata": {"query": query},
            "error": str(exc),
        }


def fetch_indicator_metadata(
    script_id: str,
    script_version: str,
    chart_session: str,
    cookie: str | None = None,
) -> dict[str, Any]:
    """Fetch and prepare indicator metadata from the pine-facade API.

    Args:
        script_id: Unique indicator script identifier (e.g. ``"STD;RSI"``).
        script_version: Script version string (e.g. ``"37.0"``).
        chart_session: Chart session identifier.
        cookie: Optional TradingView session cookies.

    Returns:
        Standardized response dict with status and metadata payload.
    """
    url = _PINE_FACADE_URL.format(script_id=script_id, script_version=script_version)
    headers = {}
    if cookie:
        headers["cookie"] = cookie

    try:
        resp = requests.get(url, timeout=5, headers=headers)
        resp.raise_for_status()
        json_data = resp.json()

        metainfo = json_data.get("result", {}).get("metaInfo")
        if metainfo:
            data = prepare_indicator_metadata(script_id, metainfo, chart_session)
            return {
                "status": STATUS_SUCCESS,
                "data": data,
                "metadata": {"script_id": script_id, "script_version": script_version},
                "error": None,
            }
        return {
            "status": STATUS_FAILED,
            "data": None,
            "metadata": {"script_id": script_id, "script_version": script_version},
            "error": "No metaInfo found in response",
        }

    except requests.RequestException as exc:
        logger.error("Error fetching indicator metadata: %s", exc)
        return {
            "status": STATUS_FAILED,
            "data": None,
            "metadata": {"script_id": script_id, "script_version": script_version},
            "error": str(exc),
        }


def prepare_indicator_metadata(
    script_id: str,
    metainfo: dict[str, Any],
    chart_session: str,
) -> dict[str, Any]:
    """Build the ``create_study`` WebSocket payload from indicator metainfo.

    Args:
        script_id: Indicator script identifier.
        metainfo: Metadata dict from the pine-facade API.
        chart_session: Chart session identifier.

    Returns:
        Dict with ``"m"`` and ``"p"`` keys ready for ``send_message("create_study", ...)``.
    """
    pine_version = metainfo.get("pine", {}).get("version", "1.0")
    first_input = metainfo.get("inputs", [{}])[0].get("defval", "")

    output_data: dict[str, Any] = {
        "m": "create_study",
        "p": [
            chart_session,
            f"st{BASE_STUDY_ID}",
            "st1",
            "sds_1",
            "Script@tv-scripting-101!",
            {
                "text": first_input,
                "pineId": script_id,
                "pineVersion": pine_version,
                "pineFeatures": {
                    "v": '{"indicator":1,"plot":1,"ta":1}',
                    "f": True,
                    "t": "text",
                },
                "__profile": {
                    "v": False,
                    "f": True,
                    "t": "bool",
                },
            },
        ],
    }

    # Collect in_* input overrides
    in_x: dict[str, Any] = {}
    for input_item in metainfo.get("inputs", []):
        if input_item["id"].startswith("in_"):
            in_x[input_item["id"]] = {
                "v": input_item["defval"],
                "f": True,
                "t": input_item["type"],
            }

    # Merge into the dict parameter
    for item in output_data["p"]:
        if isinstance(item, dict):
            item.update(in_x)

    return output_data


def fetch_available_indicators() -> dict[str, Any]:
    """Fetch the list of standard built-in indicators from TradingView.

    Note:
        These IDs and versions are specifically for use with candle streaming.

    Returns:
        Standardized response dict with keys: ``status``, ``data``,
        ``metadata``, ``error``.

    Raises:
        RuntimeError: If request or JSON parsing fails.
        ValueError: If response payload format is unexpected.
    """
    try:
        resp = requests.get(_PINE_LIST_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if not isinstance(data, list):
            return {
                "status": STATUS_FAILED,
                "data": None,
                "metadata": {},
                "error": "Unexpected available indicators response format",
            }

        indicators = [
            {
                "name": item.get("scriptName"),
                "id": item.get("scriptIdPart"),
                "version": item.get("version"),
            }
            for item in data
            if isinstance(item, dict)
        ]
        return {
            "status": STATUS_SUCCESS,
            "data": indicators,
            "metadata": {},
            "error": None,
        }

    except requests.RequestException as exc:
        logger.error("Error fetching available indicators: %s", exc)
        return {
            "status": STATUS_FAILED,
            "data": None,
            "metadata": {},
            "error": str(exc),
        }
    except ValueError as exc:
        logger.error("Error parsing available indicators response: %s", exc)
        return {
            "status": STATUS_FAILED,
            "data": None,
            "metadata": {},
            "error": f"Failed to parse available indicators response as JSON: {exc}",
        }
