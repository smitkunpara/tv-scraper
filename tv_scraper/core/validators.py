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
_LANGUAGES_SET = set(LANGUAGES.values())
_AREAS_SET = set(AREAS.values())
_NEWS_PROVIDERS_SET = set(NEWS_PROVIDERS)
_NEWS_COUNTRIES_SET = set(NEWS_COUNTRIES)
_NEWS_CORP_ACTIVITIES_SET = set(NEWS_CORP_ACTIVITIES)
_NEWS_ECONOMIC_CATEGORIES_SET = set(NEWS_ECONOMIC_CATEGORIES)
_NEWS_MARKETS_SET = set(NEWS_MARKETS)
_NEWS_SECTORS_SET = set(NEWS_SECTORS)

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


def validate_exchange(exchange: str) -> bool:
    """Validate exchange exists.

    Args:
        exchange: Exchange name to validate.

    Returns:
        True if exchange is valid.

    Raises:
        ValidationError: If exchange is not found, with suggestions.
    """
    if not exchange or not isinstance(exchange, str):
        raise ValidationError("Exchange must be a non-empty string.")

    exchange_up = exchange.upper()
    if exchange_up in _EXCHANGES_SET:
        return True

    suggestions = get_close_matches(exchange_up, EXCHANGES, n=5, cutoff=0.6)
    suggestion_str = (
        f" Did you mean one of: {', '.join(suggestions)}?" if suggestions else ""
    )
    sample = ", ".join(EXCHANGES[:10])
    raise ValidationError(
        f"Invalid exchange: '{exchange}'.{suggestion_str} "
        f"Valid exchanges include: {sample}, ..."
    )


def validate_symbol(exchange: str, symbol: str) -> bool:
    """Validate symbol is a non-empty string.

    Args:
        exchange: Exchange name (for context in error messages).
        symbol: Symbol to validate.

    Returns:
        True if symbol is valid.

    Raises:
        ValidationError: If symbol is empty or not a string.
    """
    if not symbol or not isinstance(symbol, str) or not symbol.strip():
        raise ValidationError(
            f"Symbol must be a non-empty string for exchange '{exchange}'."
        )
    return True


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


def validate_language(language: str) -> bool:
    """Validate language code exists (e.g. 'en', 'es')."""
    if language in _LANGUAGES_SET:
        return True
    valid = ", ".join(sorted(_LANGUAGES_SET))
    raise ValidationError(f"Invalid language: '{language}'. Allowed values: {valid}")


def validate_area(area: str) -> bool:
    """Validate area code exists (e.g. 'world', 'europe')."""
    if area in _AREAS_SET or area in AREAS:
        return True
    valid = ", ".join(sorted(AREAS.keys()))
    raise ValidationError(f"Invalid area: '{area}'. Allowed values: {valid}")


def validate_news_provider(provider: str) -> bool:
    """Validate news provider exists."""
    if provider in _NEWS_PROVIDERS_SET:
        return True
    valid = ", ".join(sorted(_NEWS_PROVIDERS_SET))
    raise ValidationError(
        f"Invalid news provider: '{provider}'. Allowed values: {valid}"
    )


def validate_news_country(country: str) -> bool:
    """Validate news country code exists."""
    if country in _NEWS_COUNTRIES_SET:
        return True
    valid = ", ".join(sorted(_NEWS_COUNTRIES_SET))
    raise ValidationError(f"Invalid country: '{country}'. Allowed values: {valid}")


def validate_news_corp_activity(activity: str) -> bool:
    """Validate news corporate activity exists."""
    if activity in _NEWS_CORP_ACTIVITIES_SET:
        return True
    valid = ", ".join(sorted(_NEWS_CORP_ACTIVITIES_SET))
    raise ValidationError(
        f"Invalid corporate activity: '{activity}'. Allowed values: {valid}"
    )


def validate_news_economic_category(category: str) -> bool:
    """Validate news economic category exists."""
    if category in _NEWS_ECONOMIC_CATEGORIES_SET:
        return True
    valid = ", ".join(sorted(_NEWS_ECONOMIC_CATEGORIES_SET))
    raise ValidationError(
        f"Invalid economic category: '{category}'. Allowed values: {valid}"
    )


def validate_news_market(market: str) -> bool:
    """Validate news market exists."""
    if market in _NEWS_MARKETS_SET:
        return True
    valid = ", ".join(sorted(_NEWS_MARKETS_SET))
    raise ValidationError(f"Invalid market: '{market}'. Allowed values: {valid}")


def validate_news_sector(sector: str) -> bool:
    """Validate news sector exists."""
    if sector in _NEWS_SECTORS_SET:
        return True
    valid = ", ".join(sorted(_NEWS_SECTORS_SET))
    raise ValidationError(f"Invalid sector: '{sector}'. Allowed values: {valid}")


def validate_choice(field_name: str, value: str, allowed: set[str] | list[str]) -> bool:
    """Generic validator for choice fields.

    Args:
        field_name: Name of the field being validated (for error messages).
        value: Value to check.
        allowed: Set of allowed values.

    Returns:
        True if value is in allowed set.

    Raises:
        ValidationError: If value is not in allowed set.
    """
    if value in allowed:
        return True
    allowed_values = ", ".join(sorted(allowed))
    raise ValidationError(
        f"Invalid {field_name}: '{value}'. "
        f"Unsupported {field_name}. "
        f"Allowed values: {allowed_values}"
    )


def validate_range(field_name: str, value: int, min_val: int, max_val: int) -> bool:
    """Validate numeric range.

    Args:
        field_name: Name of field for error messages.
        value: Value to check.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.

    Returns:
        True if within range.

    Raises:
        ValidationError: If value is outside [min_val, max_val].
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"Invalid {field_name}: {value}. Must be a number.")
    if min_val <= value <= max_val:
        return True
    raise ValidationError(
        f"Invalid {field_name}: {value}. Must be between {min_val} and {max_val}."
    )


def validate_yyyymmdd_date(field_name: str, value: int) -> bool:
    """Validate date integer in YYYYMMDD format with calendar checks.

    Args:
        field_name: Name of the field for error messages.
        value: Date value in YYYYMMDD format.

    Returns:
        True if date is a valid calendar date.

    Raises:
        ValidationError: If value is not a valid YYYYMMDD date.
    """
    if not isinstance(value, int):
        raise ValidationError(
            f"Invalid {field_name} value: {value!r}. Must be int in YYYYMMDD format."
        )

    value_str = str(value)
    if not _YYYYMMDD_DATE_PATTERN.fullmatch(value_str):
        raise ValidationError(
            f"Invalid {field_name} value: {value!r}. Must be in YYYYMMDD format."
        )

    year = int(value_str[:4])
    month = int(value_str[4:6])
    day = int(value_str[6:8])

    if not 1 <= month <= 12:
        raise ValidationError(
            f"Invalid {field_name} value: {value!r}. Month must satisfy 0 < MM <= 12."
        )

    if not 1 <= day <= 31:
        raise ValidationError(
            f"Invalid {field_name} value: {value!r}. Day must satisfy 0 < DD <= 31."
        )

    try:
        date(year, month, day)
    except ValueError as exc:
        raise ValidationError(f"Invalid {field_name} value: {value!r}. {exc}.") from exc

    return True


def validate_fields(
    fields: Sequence[str],
    allowed: Sequence[str],
    field_name: str = "fields",
) -> bool:
    """Validate a list of fields against allowed values.

    Args:
        fields: List of field names to validate.
        allowed: List of allowed field names.
        field_name: Name for error messages (default: "fields").

    Returns:
        True if all fields are valid.

    Raises:
        ValidationError: If any field is not in allowed list.
    """
    if isinstance(fields, str) or not isinstance(fields, Sequence):
        raise ValidationError(f"Invalid {field_name} parameter: expected list.")
    if not all(isinstance(f, str) for f in fields):
        raise ValidationError(
            f"Invalid {field_name} parameter: all items must be strings."
        )
    allowed_set = set(allowed)
    invalid = [f for f in fields if f not in allowed_set]
    if invalid:
        raise ValidationError(
            f"Invalid {field_name}: {', '.join(invalid)}. "
            f"Allowed {field_name}: {', '.join(sorted(allowed_set))}"
        )
    return True


def verify_symbol_exchange(
    exchange: str, symbol: str, retries: int = 2
) -> tuple[str, str]:
    """Verify exchange is valid, symbol is non-empty, and the combination
    exists on TradingView.

    Combines :meth:`validate_exchange` and :meth:`validate_symbol` with a
    live check against the TradingView scanner API. Returns the uppercased
    (exchange, symbol) if valid.

    Args:
        exchange: Exchange name (e.g. ``"NASDAQ"``).
        symbol: Symbol name (e.g. ``"AAPL"``).
        retries: Number of HTTP retry attempts on network errors. Must be >= 1.

    Returns:
        A tuple of (exchange, symbol) in uppercase.

    Raises:
        ValidationError: If the exchange, symbol, or their combination is
            invalid, or if the live check cannot be completed.
    """
    validate_exchange(exchange)
    validate_symbol(exchange, symbol)
    if retries < 1:
        raise ValidationError(f"Retries must be at least 1, got {retries}.")

    exchange_up = exchange.upper()
    symbol_up = symbol.upper()

    url = _SCANNER_SYMBOL_URL.format(exchange=exchange_up, symbol=symbol_up)
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 404:
                raise ValidationError(
                    f"Symbol '{symbol}' not found on exchange '{exchange}'. "
                    "Verify the symbol and exchange combination, or use "
                    "SymbolMarkets to discover valid exchange listings."
                )
            resp.raise_for_status()
            return exchange_up, symbol_up
        except requests.RequestException as exc:
            last_exc = exc
            logger.warning(
                "Attempt %d: network error verifying '%s:%s': %s",
                attempt + 1,
                exchange,
                symbol,
                exc,
            )
    raise ValidationError(
        f"Could not verify '{exchange}:{symbol}' after {retries} attempt(s): {last_exc}"
    ) from last_exc


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
