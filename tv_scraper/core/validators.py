"""Module-level validation functions for exchanges, symbols, indicators, timeframes, etc."""

import logging
import re
from collections.abc import Sequence
from datetime import date
from difflib import get_close_matches
from typing import TypeVar

import requests

from tv_scraper.core.exceptions import ValidationError
from tv_scraper.core.validation_data import (
    AREAS,
    EXCHANGES,
    INDICATORS,
    LANGUAGES,
    NEWS_CORP_ACTIVITIES,
    NEWS_COUNTRIES,
    NEWS_ECONOMIC_CATEGORIES,
    NEWS_MARKETS,
    NEWS_PROVIDERS,
    NEWS_SECTORS,
    TIMEFRAMES,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Pre-computed sets for efficient validation lookups
_EXCHANGES_SET = {e.upper() for e in EXCHANGES}
_INDICATORS_SET = set(INDICATORS)
LANGUAGES_SET = set(LANGUAGES.values())
AREAS_SET = set(AREAS.keys())
NEWS_PROVIDERS_SET = set(NEWS_PROVIDERS)
NEWS_COUNTRIES_SET = set(NEWS_COUNTRIES)
NEWS_CORP_ACTIVITIES_SET = set(NEWS_CORP_ACTIVITIES)
NEWS_ECONOMIC_CATEGORIES_SET = set(NEWS_ECONOMIC_CATEGORIES)
NEWS_MARKETS_SET = set(NEWS_MARKETS)
NEWS_SECTORS_SET = set(NEWS_SECTORS)

# TradingView scanner API for live symbol:exchange combination validation
_SCANNER_SYMBOL_URL = (
    "https://scanner.tradingview.com/symbol"
    "?symbol={exchange}%3A{symbol}&fields=market&no_404=false"
)

# TradingView symbol-search API to check options availability (no hl=1 to avoid <em> tags)
_OPTIONS_SEARCH_URL = (
    "https://symbol-search.tradingview.com/symbol_search/v3/"
    "?text={symbol}&exchange={exchange}&lang=en"
    "&search_type=undefined&only_has_options=true&domain=production"
)

_STRIP_HTML_TAGS = re.compile(r"<[^>]+>")

# Browser-like headers required by the symbol-search endpoint
_OPTIONS_SEARCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.tradingview.com/",
    "Origin": "https://www.tradingview.com",
    "Accept": "application/json",
}

_YYYYMMDD_DATE_PATTERN = re.compile(r"^\d{8}$")


def validate_indicators(indicators: list[str]) -> bool:
    """Validate all indicators exist in known list.

    Args:
        indicators: List of indicator names to validate.

    Returns:
        True if all indicators are valid.

    Raises:
        ValidationError: If any indicator is invalid or list is empty.
    """
    if not indicators:
        raise ValidationError("No indicators provided. Provide at least one indicator.")
    for indicator in indicators:
        if indicator not in _INDICATORS_SET:
            suggestions = get_close_matches(indicator, INDICATORS, n=3, cutoff=0.5)
            suggestion_str = (
                f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
            )
            raise ValidationError(f"Invalid indicator: '{indicator}'.{suggestion_str}")
    return True


def validate_timeframe(timeframe: str) -> bool:
    """Validate timeframe is supported.

    Args:
        timeframe: Timeframe string to validate (e.g. '1d', '1h').

    Returns:
        True if timeframe is valid.

    Raises:
        ValidationError: If timeframe is not supported.
    """
    if timeframe in TIMEFRAMES:
        return True
    valid = ", ".join(TIMEFRAMES.keys())
    raise ValidationError(
        f"Invalid timeframe: '{timeframe}'. Valid timeframes: {valid}"
    )


def validate_choice(
    value: str | None, allowed: set[str] | list[str] | frozenset[str]
) -> bool:
    """Generic validator for choice fields. Handles None for optional params.

    Args:
        value: Value to check.
        allowed: Collection of allowed values.

    Returns:
        True if value is None or in allowed set.

    Raises:
        ValidationError: If value is not in allowed set, including suggestions.
    """
    if value is None:
        return True

    if value in allowed:
        return True

    allowed_list = sorted(list(allowed))
    suggestions = get_close_matches(str(value), allowed_list, n=3, cutoff=0.6)
    suggestion_str = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
    sample = ", ".join(map(str, allowed_list[:5]))
    raise ValidationError(
        f"Invalid value: '{value}'.{suggestion_str} "
        f"Allowed values include: {sample}, ..."
    )


def validate_list(
    values: Sequence[str] | None,
    allowed: set[str] | frozenset[str] | list[str],
) -> bool:
    """Validate all items in `values` exist in `allowed`. Handles None.

    Batch counterpart to :func:`validate_choice` for list parameters.

    Args:
        values: List of strings to validate.
        allowed: Collection of allowed values.

    Returns:
        True if values is None or all values are valid.

    Raises:
        ValidationError: If any value is not in `allowed`.
    """
    if values is None:
        return True
    allowed_set = allowed if isinstance(allowed, (set, frozenset)) else set(allowed)
    invalid = [v for v in values if v not in allowed_set]
    if not invalid:
        return True
    valid = ", ".join(sorted(str(a) for a in list(allowed_set)[:5]))
    raise ValidationError(
        f"Invalid values: {', '.join(repr(v) for v in invalid)}. "
        f"Allowed values include: {valid}, ..."
    )


def validate_range(value: int | float | None, min_val: int, max_val: int) -> bool:
    """Validate numeric range. Handles None.

    Args:
        value: Value to check.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.

    Returns:
        True if value is None or within range.

    Raises:
        ValidationError: If value is outside [min_val, max_val].
    """
    if value is None:
        return True
    if not isinstance(value, (int, float)):
        raise ValidationError(f"Invalid value: {value}. Must be a number.")
    if min_val <= value <= max_val:
        return True
    raise ValidationError(
        f"Invalid value: {value}. Must be between {min_val} and {max_val}."
    )


def validate_yyyymmdd_date(value: int | None) -> bool:
    """Validate date integer in YYYYMMDD format with calendar checks. Handles None.

    Args:
        value: Date value in YYYYMMDD format.

    Returns:
        True if value is None or a valid calendar date.

    Raises:
        ValidationError: If value is not a valid YYYYMMDD date.
    """
    if value is None:
        return True
    if not isinstance(value, int):
        raise ValidationError(
            f"Invalid date value: {value!r}. Must be int in YYYYMMDD format."
        )

    value_str = str(value)
    if not _YYYYMMDD_DATE_PATTERN.fullmatch(value_str):
        raise ValidationError(
            f"Invalid date value: {value!r}. Must be in YYYYMMDD format."
        )

    year = int(value_str[:4])
    month = int(value_str[4:6])
    day = int(value_str[6:8])

    if not 1 <= month <= 12:
        raise ValidationError(
            f"Invalid date value: {value!r}. Month must satisfy 0 < MM <= 12."
        )

    if not 1 <= day <= 31:
        raise ValidationError(
            f"Invalid date value: {value!r}. Day must satisfy 0 < DD <= 31."
        )

    try:
        date(year, month, day)
    except ValueError as exc:
        raise ValidationError(f"Invalid date value: {value!r}. {exc}.") from exc

    return True


def verify_symbol_exchange(
    exchange: str | None,
    symbol: str | None,
) -> tuple[str, str]:
    """Verify exchange/symbol existence on TradingView.

    Returns (exchange, symbol) in uppercase.
    """
    if (
        not exchange
        or not symbol
        or not isinstance(exchange, str)
        or not isinstance(symbol, str)
    ):
        raise ValidationError("Both exchange and symbol must be provided together.")

    exchange_up, symbol_up = exchange.strip().upper(), symbol.strip().upper()
    if not exchange_up or not symbol_up:
        raise ValidationError("Both exchange and symbol must be provided together.")

    validate_choice(exchange_up, _EXCHANGES_SET)

    url = _SCANNER_SYMBOL_URL.format(exchange=exchange_up, symbol=symbol_up)
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 404:
            raise ValidationError(
                f"Symbol '{symbol_up}' not found on exchange '{exchange_up}'."
            )
        resp.raise_for_status()
    except (requests.RequestException, ValidationError) as exc:
        if isinstance(exc, ValidationError):
            raise
        # Silently pass network errors during verification to avoid blocking
        pass

    return exchange_up, symbol_up


def verify_options_symbol(exchange: str, symbol: str) -> tuple[str, str]:
    """Verify the symbol:exchange combination exists and has options.

    First validates via :meth:`verify_symbol_exchange`, then queries the
    TradingView symbol-search API with ``only_has_options=true`` to confirm
    options are available. Returns the uppercased (exchange, symbol) if valid.

    Args:
        exchange: Exchange name (e.g. ``"NSE"``).
        symbol: Symbol name (e.g. ``"RELIANCE"``).

    Returns:
        A tuple of (exchange, symbol) in uppercase.

    Raises:
        ValidationError: If the combination is invalid or no options exist.
    """
    exchange_up, symbol_up = verify_symbol_exchange(exchange, symbol)

    url = _OPTIONS_SEARCH_URL.format(symbol=symbol_up, exchange=exchange_up)
    try:
        resp = requests.get(url, headers=_OPTIONS_SEARCH_HEADERS, timeout=5)
        # A 403 means the endpoint rejected the request for this combination
        # (e.g. exchange has no options market); treat as "no options".
        if resp.status_code == 403:
            raise ValidationError(
                f"Symbol '{symbol}' has no options available on exchange '{exchange}'. "
                "Check the symbol name or try a different exchange."
            )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("symbols", [])

        for item in items:
            # Strip any HTML highlight tags (e.g. <em>RELIANCE</em> → RELIANCE)
            clean_sym = _STRIP_HTML_TAGS.sub("", item.get("symbol", ""))
            if clean_sym.upper() == symbol_up:
                return exchange_up, symbol_up

        raise ValidationError(
            f"Symbol '{symbol}' has no options available on exchange '{exchange}'. "
            "Check the symbol name or try a different exchange."
        )
    except requests.RequestException as exc:
        raise ValidationError(
            f"Network error while checking options for '{exchange}:{symbol}': {exc}"
        ) from exc
