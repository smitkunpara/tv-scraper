"""Base scraper class for tv_scraper."""

import functools
import inspect
import logging
import os
from collections.abc import Callable, Sequence
from difflib import get_close_matches
from typing import Any, TypeVar

import requests

from tv_scraper.core.constants import (
    CAPTCHA_MARKER,
    DEFAULT_USER_AGENT,
    EXPORT_TYPES,
    REQUEST_TIMEOUT,
    STATUS_FAILED,
    STATUS_SUCCESS,
)
from tv_scraper.core.exceptions import CaptchaError, ValidationError
from tv_scraper.core.validation_data import EXCHANGES, TIMEFRAMES
from tv_scraper.utils.io import generate_export_filepath, save_csv_file, save_json_file

_EXCHANGES_SET = {e.upper() for e in EXCHANGES}
_SCANNER_SYMBOL_URL = (
    "https://scanner.tradingview.com/symbol"
    "?symbol={exchange}%3A{symbol}&fields=market&no_404=false"
)

logger = logging.getLogger(__name__)

_MIN_TIMEOUT: int = 1
_MAX_TIMEOUT: int = 300

F = TypeVar("F", bound=Callable[..., Any])


def catch_errors(func: F) -> F:
    """Decorator to catch ValidationErrors and return a standardized error response.

    Automatically captures all function arguments into the metadata field
    of the response envelope.
    """

    @functools.wraps(func)
    def wrapper(self: "BaseScraper", *args: Any, **kwargs: Any) -> Any:
        # Capture metadata for the response envelope
        sig = inspect.signature(func)
        try:
            bound_args = sig.bind(self, *args, **kwargs)
            bound_args.apply_defaults()
            self._last_metadata = {
                k: v
                for k, v in bound_args.arguments.items()
                if k != "self" and v is not None
            }
        except ValueError:
            # Fallback if signature binding fails (e.g. invalid arguments)
            self._last_metadata = kwargs.copy()

        try:
            return func(self, *args, **kwargs)
        except ValidationError as exc:
            return self._error_response(str(exc), **self._last_metadata)
        except Exception as exc:
            logger.exception("Unexpected error in %s", func.__name__)
            return self._error_response(
                f"Unexpected error: {exc}", **self._last_metadata
            )

    return wrapper  # type: ignore


class BaseScraper:
    """Base class for all scrapers providing common functionality.

    Provides standardized response envelopes, HTTP request handling,
    data export, and access to the shared DataValidator.

    Args:
        export: Export format, ``"json"`` or ``"csv"``.
            If ``None`` (default), results are not exported.
        timeout: HTTP request timeout in seconds.
    """

    def __init__(
        self,
        export: str | None = None,
        timeout: int = REQUEST_TIMEOUT,
        cookie: str | None = None,
    ) -> None:
        if export is not None and export not in EXPORT_TYPES:
            raise ValueError(
                f"Invalid export: '{export}'. "
                f"Supported types: {', '.join(sorted(EXPORT_TYPES))} or None"
            )
        if (
            not isinstance(timeout, int)
            or timeout < _MIN_TIMEOUT
            or timeout > _MAX_TIMEOUT
        ):
            raise ValueError(
                f"Timeout must be an integer between {_MIN_TIMEOUT} and {_MAX_TIMEOUT}, got {timeout}."
            )
        self.export_result = bool(export)
        self.export_type = export or "json"
        self.timeout = timeout

        self.cookie = cookie or os.environ.get("TRADINGVIEW_COOKIE")
        self._last_metadata: dict[str, Any] = {}
        self._headers: dict[str, str] = {"User-Agent": DEFAULT_USER_AGENT}
        if self.cookie:
            self._headers["cookie"] = self.cookie

    def _success_response(
        self, data: Any, warnings: list[str] | None = None, **metadata: Any
    ) -> dict[str, Any]:
        """Build a standardized success response.

        Args:
            data: The response payload.
            warnings: List of warning messages.
            **metadata: Arbitrary metadata key-value pairs.
                The key is the argument name passed to the function and
                the value is the data provided by the user.

        Returns:
            Response dict with status, data, metadata (``dict[str, Any]``),
            warnings (``list[str]``), and error fields.
        """
        combined_meta = self._last_metadata.copy()
        combined_meta.update(metadata)
        return {
            "status": STATUS_SUCCESS,
            "data": data,
            "metadata": combined_meta,
            "warnings": warnings or [],
            "error": None,
        }

    def _error_response(
        self,
        error: str,
        data: Any = None,
        warnings: list[str] | None = None,
        **metadata: Any,
    ) -> dict[str, Any]:
        """Build a standardized error response.

        Args:
            error: Error message string.
            data: Optional partial data payload.
            warnings: List of warning messages.
            **metadata: Arbitrary metadata key-value pairs.
                The key is the argument name passed to the function and
                the value is the data provided by the user.

        Returns:
            Response dict with status="failed", data, metadata (``dict[str, Any]``),
            warnings (``list[str]``), and error message.
        """
        combined_meta = self._last_metadata.copy()
        combined_meta.update(metadata)
        return {
            "status": STATUS_FAILED,
            "data": data,
            "metadata": combined_meta,
            "warnings": warnings or [],
            "error": error,
        }

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_payload: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        check_captcha: bool = True,
    ) -> tuple[Any, str | None]:
        """Unified HTTP request with error handling.

        Returns:
            (parsed_json, None) on success
            (None, error_message) on failure
        """
        req_headers = self._headers.copy()
        if headers:
            req_headers.update(headers)

        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=json_payload,
                data=data,
                files=files,
                headers=req_headers,
                timeout=self.timeout,
            )

            if check_captcha and CAPTCHA_MARKER in response.text:
                raise CaptchaError("TradingView requested a captcha challenge.")

            response.raise_for_status()

            # Simple check if there's content. We usually expect JSON.
            if not response.text.strip():
                return None, "Empty response from server."

            return response.json(), None

        except CaptchaError as exc:
            return None, str(exc)
        except requests.RequestException as exc:
            return None, f"Network error: {exc}"
        except ValueError as exc:
            return None, f"Failed to parse API response: {exc}"

    def _validate_choice(
        self, value: str | None, allowed: set[str] | list[str] | frozenset[str]
    ) -> bool:
        if value is None:
            return True

        if value in allowed:
            return True

        allowed_list = sorted(list(allowed))
        suggestions = get_close_matches(str(value), allowed_list, n=3, cutoff=0.6)
        suggestion_str = (
            f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
        )
        sample = ", ".join(map(str, allowed_list[:5]))
        raise ValidationError(
            f"Invalid value: '{value}'.{suggestion_str} "
            f"Allowed values include: {sample}, ..."
        )

    def _validate_list(
        self,
        values: Sequence[str] | None,
        allowed: set[str] | frozenset[str] | list[str],
    ) -> bool:
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

    def _validate_range(
        self, value: int | float | None, min_val: int, max_val: int
    ) -> bool:
        if value is None:
            return True
        if not isinstance(value, (int, float)):
            raise ValidationError(f"Invalid value: {value}. Must be a number.")
        if min_val <= value <= max_val:
            return True
        raise ValidationError(
            f"Invalid value: {value}. Must be between {min_val} and {max_val}."
        )

    def _validate_timeframe(self, timeframe: str) -> bool:
        if timeframe in TIMEFRAMES:
            return True
        valid = ", ".join(TIMEFRAMES.keys())
        raise ValidationError(
            f"Invalid timeframe: '{timeframe}'. Valid timeframes: {valid}"
        )

    def _verify_symbol_exchange(
        self, exchange: str | None, symbol: str | None
    ) -> tuple[str, str]:
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

        self._validate_choice(exchange_up, _EXCHANGES_SET)

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
            pass

        return exchange_up, symbol_up

    def _export(
        self,
        data: Any,
        symbol: str,
        data_category: str,
        timeframe: str | None = None,
    ) -> None:
        """Export data if export_result is True.

        Args:
            data: Data to export.
            symbol: Symbol name for the filename.
            data_category: Category prefix for the filename.
            timeframe: Optional timeframe suffix.
        """
        if not self.export_result:
            return
        filepath = generate_export_filepath(
            symbol, data_category, self.export_type, timeframe
        )
        if self.export_type == "csv":
            save_csv_file(data, filepath)
        else:
            save_json_file(data, filepath)
