"""DataValidator singleton for validating exchanges, indicators, timeframes, etc."""

import functools
import inspect
import logging
import re
import threading
from difflib import get_close_matches
from typing import Any, Callable, Optional, TypeVar

import requests

from tv_scraper.core.exceptions import ValidationError
from tv_scraper.core.validation_data import (
    AREAS,
    EXCHANGES,
    INDICATORS,
    LANGUAGES,
    NEWS_PROVIDERS,
    TIMEFRAMES,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


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


class DataValidator:
    """Singleton validator that uses static validation data.

    Usage::

        validator = DataValidator()
        validator.validate_exchange("BINANCE")  # True
        validator.validate_exchange("TYPO")     # raises ValidationError
    """

    _instance: Optional["DataValidator"] = None
    _lock = threading.RLock()

    def __new__(cls) -> "DataValidator":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._load_data()
        return cls._instance

    def _load_data(self) -> None:
        """Initialize data from constants."""
        self._exchanges: list[str] = EXCHANGES
        self._exchanges_set: set[str] = {e.upper() for e in self._exchanges}

        self._indicators: list[str] = INDICATORS
        self._indicators_set: set[str] = set(self._indicators)

        self._timeframes: dict[str, Any] = TIMEFRAMES
        self._languages: dict[str, str] = LANGUAGES
        self._languages_set: set[str] = set(self._languages.values())
        self._areas: dict[str, str] = AREAS
        self._areas_set: set[str] = set(self._areas.values())
        self._news_providers: list[str] = NEWS_PROVIDERS
        self._news_providers_set: set[str] = set(self._news_providers)

    def validate_exchange(self, exchange: str) -> bool:
        """Validate exchange exists.

        Args:
            exchange: Exchange name to validate.

        Returns:
            True if exchange is valid.

        Raises:
            ValidationError: If exchange is not found, with suggestions.
        """
        if exchange.upper() in self._exchanges_set:
            return True
        suggestions = get_close_matches(
            exchange.upper(), self._exchanges, n=5, cutoff=0.6
        )
        suggestion_str = (
            f" Did you mean one of: {', '.join(suggestions)}?" if suggestions else ""
        )
        sample = ", ".join(self._exchanges[:10])
        raise ValidationError(
            f"Invalid exchange: '{exchange}'.{suggestion_str} "
            f"Valid exchanges include: {sample}, ..."
        )

    def validate_symbol(self, exchange: str, symbol: str) -> bool:
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

    def validate_indicators(self, indicators: list[str]) -> bool:
        """Validate all indicators exist in known list.

        Args:
            indicators: List of indicator names to validate.

        Returns:
            True if all indicators are valid.

        Raises:
            ValidationError: If any indicator is invalid or list is empty.
        """
        if not indicators:
            raise ValidationError(
                "No indicators provided. Provide at least one indicator."
            )
        for indicator in indicators:
            if indicator not in self._indicators_set:
                suggestions = get_close_matches(
                    indicator, self._indicators, n=3, cutoff=0.5
                )
                suggestion_str = (
                    f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
                )
                raise ValidationError(
                    f"Invalid indicator: '{indicator}'.{suggestion_str}"
                )
        return True

    def validate_timeframe(self, timeframe: str) -> bool:
        """Validate timeframe is supported.

        Args:
            timeframe: Timeframe string to validate (e.g. '1d', '1h').

        Returns:
            True if timeframe is valid.

        Raises:
            ValidationError: If timeframe is not supported.
        """
        if timeframe in self._timeframes:
            return True
        valid = ", ".join(self._timeframes.keys())
        raise ValidationError(
            f"Invalid timeframe: '{timeframe}'. Valid timeframes: {valid}"
        )

    def validate_language(self, language: str) -> bool:
        """Validate language code exists (e.g. 'en', 'es')."""
        if language in self._languages_set:
            return True
        valid = ", ".join(sorted(self._languages_set))
        raise ValidationError(
            f"Invalid language: '{language}'. Allowed values: {valid}"
        )

    def validate_area(self, area: str) -> bool:
        """Validate area code exists (e.g. 'world', 'europe')."""
        if area in self._areas_set or area in self._areas:
            return True
        valid = ", ".join(sorted(self._areas.keys()))
        raise ValidationError(f"Invalid area: '{area}'. Allowed values: {valid}")

    def validate_news_provider(self, provider: str) -> bool:
        """Validate news provider exists."""
        if provider in self._news_providers_set:
            return True
        valid = ", ".join(sorted(self._news_providers_set))
        raise ValidationError(f"Invalid news provider: '{provider}'. Allowed values: {valid}")

    def validate_choice(self, field_name: str, value: str, allowed: set[str] | list[str]) -> bool:
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
        raise ValidationError(
            f"Invalid {field_name}: '{value}'. Allowed values: {', '.join(sorted(allowed))}"
        )

    def validate_range(
        self, field_name: str, value: int, min_val: int, max_val: int
    ) -> bool:
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
        if min_val <= value <= max_val:
            return True
        raise ValidationError(
            f"Invalid {field_name}: {value}. Must be between {min_val} and {max_val}."
        )

    def validate_fields(
        self, fields: list[str], allowed: list[str], field_name: str = "fields"
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
        allowed_set = set(allowed)
        invalid = [f for f in fields if f not in allowed_set]
        if invalid:
            raise ValidationError(
                f"Invalid {field_name}: {', '.join(invalid)}. "
                f"Allowed {field_name}: {', '.join(sorted(allowed_set))}"
            )
        return True

    def verify_symbol_exchange(
        self, exchange: str, symbol: str, retries: int = 2
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
        self.validate_exchange(exchange)
        self.validate_symbol(exchange, symbol)
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

    def verify_options_symbol(self, exchange: str, symbol: str) -> tuple[str, str]:
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
        exchange_up, symbol_up = self.verify_symbol_exchange(exchange, symbol)

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

    def get_exchanges(self) -> list[str]:
        """Return list of all valid exchanges."""
        return list(self._exchanges)

    def get_indicators(self) -> list[str]:
        """Return list of all valid indicators."""
        return list(self._indicators)

    def get_timeframes(self) -> dict[str, Any]:
        """Return timeframe mappings."""
        return dict(self._timeframes)

    def get_news_providers(self) -> list[str]:
        """Return list of all valid news providers."""
        return list(self._news_providers)

    def get_languages(self) -> dict[str, str]:
        """Return language name-to-code mappings."""
        return dict(self._languages)

    def get_areas(self) -> dict[str, str]:
        """Return area name-to-code mappings."""
        return dict(self._areas)

    @classmethod
    def reset(cls) -> None:
        """Reset singleton for testing."""
        with cls._lock:
            cls._instance = None


# --- Shared Instance and Module-Level Functions ---

_validator = DataValidator()


def validate_exchange(exchange: str) -> bool:
    """Directly validate exchange."""
    return _validator.validate_exchange(exchange)


def validate_symbol(exchange: str, symbol: str) -> bool:
    """Directly validate symbol."""
    return _validator.validate_symbol(exchange, symbol)


def validate_indicators(indicators: list[str]) -> bool:
    """Directly validate indicators."""
    return _validator.validate_indicators(indicators)


def validate_timeframe(timeframe: str) -> bool:
    """Directly validate timeframe."""
    return _validator.validate_timeframe(timeframe)


def validate_language(language: str) -> bool:
    """Directly validate language."""
    return _validator.validate_language(language)


def validate_area(area: str) -> bool:
    """Directly validate area."""
    return _validator.validate_area(area)


def validate_news_provider(provider: str) -> bool:
    """Directly validate news provider."""
    return _validator.validate_news_provider(provider)


def validate_choice(field_name: str, value: str, allowed: set[str] | list[str]) -> bool:
    """Directly validate choice."""
    return _validator.validate_choice(field_name, value, allowed)


def validate_range(field_name: str, value: int, min_val: int, max_val: int) -> bool:
    """Directly validate range."""
    return _validator.validate_range(field_name, value, min_val, max_val)


def validate_fields(
    fields: list[str], allowed: list[str], field_name: str = "fields"
) -> bool:
    """Directly validate fields."""
    return _validator.validate_fields(fields, allowed, field_name)


def verify_symbol_exchange(
    exchange: str, symbol: str, retries: int = 2
) -> tuple[str, str]:
    """Directly verify symbol and exchange."""
    return _validator.verify_symbol_exchange(exchange, symbol, retries)


def verify_options_symbol(exchange: str, symbol: str) -> tuple[str, str]:
    """Directly verify symbol for options."""
    return _validator.verify_options_symbol(exchange, symbol)
