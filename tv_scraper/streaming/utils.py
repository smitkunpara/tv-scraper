"""Streaming utility functions: symbol validation, indicator metadata fetching."""

import logging
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)

_VALIDATE_URL = (
    "https://scanner.tradingview.com/symbol?"
    "symbol={exchange}%3A{symbol}&fields=market&no_404=false"
)

_INDICATOR_SEARCH_URL = "https://www.tradingview.com/pubscripts-suggest-json/?search="

_PINE_FACADE_URL = (
    "https://pine-facade.tradingview.com/pine-facade/translate/{script_id}/{script_version}"
)

_PINE_LIST_URL = "https://pine-facade.tradingview.com/pine-facade/list?filter=standard"


def validate_symbols(exchange: str, symbol: str, retries: int = 3) -> bool:
    """Validate an exchange:symbol pair against the TradingView scanner API.

    Args:
        exchange: Exchange name (e.g. ``"BINANCE"``).
        symbol: Symbol name (e.g. ``"BTCUSDT"``).
        retries: Number of HTTP retries.

    Returns:
        ``True`` if the symbol is valid.

    Raises:
        ValueError: If the symbol is invalid or validation fails after all retries.
    """
    if not exchange or not symbol:
        raise ValueError("exchange and symbol cannot be empty")

    url = _VALIDATE_URL.format(exchange=exchange, symbol=symbol)

    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            return True
        except requests.RequestException as exc:
            status = getattr(exc.response, "status_code", None) if hasattr(exc, "response") else None
            if status == 404:
                raise ValueError(
                    f"Invalid exchange:symbol '{exchange}:{symbol}'"
                ) from exc
            logger.warning(
                "Attempt %d failed to validate '%s:%s': %s",
                attempt + 1, exchange, symbol, exc,
            )
            if attempt >= retries - 1:
                raise ValueError(
                    f"Invalid exchange:symbol '{exchange}:{symbol}' after {retries} attempts"
                ) from exc

    return False  # pragma: no cover


def fetch_tradingview_indicators(query: str) -> List[dict]:
    """Search public TradingView indicators by name or author.

    Args:
        query: Search term to filter indicators.

    Returns:
        List of indicator dicts with keys: ``scriptName``, ``imageUrl``,
        ``author``, ``agreeCount``, ``isRecommended``, ``scriptIdPart``, ``version``.
    """
    url = _INDICATOR_SEARCH_URL + query

    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        json_data = resp.json()

        results = json_data.get("results", [])
        filtered: List[dict] = []

        for indicator in results:
            name = indicator.get("scriptName", "")
            author = indicator.get("author", {}).get("username", "")
            if query.lower() in name.lower() or query.lower() in author.lower():
                filtered.append({
                    "scriptName": name,
                    "imageUrl": indicator.get("imageUrl", ""),
                    "author": author,
                    "agreeCount": indicator.get("agreeCount", 0),
                    "isRecommended": indicator.get("isRecommended", False),
                    "scriptIdPart": indicator.get("scriptIdPart", ""),
                    "version": indicator.get("version"),
                })
        return filtered

    except requests.RequestException as exc:
        logger.error("Error fetching TradingView indicators: %s", exc)
        return []


def fetch_indicator_metadata(
    script_id: str,
    script_version: str,
    chart_session: str,
) -> dict:
    """Fetch and prepare indicator metadata from the pine-facade API.

    Args:
        script_id: Unique indicator script identifier (e.g. ``"STD;RSI"``).
        script_version: Script version string (e.g. ``"37.0"``).
        chart_session: Chart session identifier.

    Returns:
        Prepared ``create_study`` payload dict, or empty dict on failure.
    """
    url = _PINE_FACADE_URL.format(script_id=script_id, script_version=script_version)

    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        json_data = resp.json()

        metainfo = json_data.get("result", {}).get("metaInfo")
        if metainfo:
            return prepare_indicator_metadata(script_id, metainfo, chart_session)
        return {}

    except requests.RequestException as exc:
        logger.error("Error fetching indicator metadata: %s", exc)
        return {}


def prepare_indicator_metadata(
    script_id: str,
    metainfo: dict,
    chart_session: str,
) -> dict:
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

    output_data: dict = {
        "m": "create_study",
        "p": [
            chart_session,
            "st9",
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
    in_x: dict = {}
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


def fetch_available_indicators() -> List[dict]:
    """Fetch the list of standard built-in indicators from TradingView.

    Note:
        These IDs and versions are specifically for use with candle streaming.

    Returns:
        List of indicator dicts with: name, id, version.
    """
    try:
        resp = requests.get(_PINE_LIST_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if not isinstance(data, list):
            return []

        return [
            {
                "name": item.get("scriptName"),
                "id": item.get("scriptIdPart"),
                "version": item.get("version"),
            }
            for item in data
        ]
    except Exception as exc:
        logger.error("Error fetching available indicators: %s", exc)
        return []
