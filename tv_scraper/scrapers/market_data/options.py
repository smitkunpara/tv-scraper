"""Options scraper for fetching option chain data from TradingView."""

import re
from datetime import date
from typing import Any, get_args

import requests

from tv_scraper.core.base import catch_errors
from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.exceptions import ValidationError
from tv_scraper.core.scanner import ScannerScraper
from tv_scraper.core.validation_data import EXCHANGE_LITERAL, OPTION_COLUMN_LITERAL

OPTIONS_SCANNER_URL = f"{SCANNER_URL}/options/scan2?label-product=symbols-options"

DEFAULT_OPTION_COLUMNS: list[str] = list(get_args(OPTION_COLUMN_LITERAL))
VALID_OPTION_COLUMNS = set(DEFAULT_OPTION_COLUMNS)


_STRIP_HTML_TAGS = re.compile(r"<[^>]+>")
_OPTIONS_SEARCH_URL = (
    "https://symbol-search.tradingview.com/symbol_search/v3/"
    "?text={symbol}&exchange={exchange}&lang=en"
    "&search_type=undefined&only_has_options=true&domain=production"
)
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


class Options(ScannerScraper):
    """Scraper for option chain data from TradingView.

    Fetches option chains for a given underlying symbol, filtered by
    expiration date, strike price, or both.

    Args:
        export: Export format, ``"json"`` or ``"csv"``.
            If ``None`` (default), results are not exported.
        timeout: HTTP request timeout in seconds.

    Example::

        from tv_scraper.scrapers.market_data import Options

        scraper = Options()
        # Get by expiry
        result = scraper.get_options(
            exchange="BSE",
            symbol="SENSEX",
            expiration=20260219,
        )
        # Get by strike
        result = scraper.get_options(
            exchange="BSE",
            symbol="SENSEX",
            strike=83300
        )
        # Get by expiry + strike
        result = scraper.get_options(
            exchange="BSE",
            symbol="SENSEX",
            expiration=20260219,
            strike=83300,
        )
    """

    def _validate_yyyymmdd_date(self, value: int | None) -> bool:
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

    def _verify_options_symbol(self, exchange: str, symbol: str) -> tuple[str, str]:
        exchange_up, symbol_up = self._verify_symbol_exchange(exchange, symbol)
        url = _OPTIONS_SEARCH_URL.format(symbol=symbol_up, exchange=exchange_up)
        try:
            resp = requests.get(url, headers=_OPTIONS_SEARCH_HEADERS, timeout=5)
            if resp.status_code == 403:
                raise ValidationError(
                    f"Symbol '{symbol}' has no options available on exchange '{exchange}'. "
                    "Check the symbol name or try a different exchange."
                )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("symbols", [])
            for item in items:
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

    @catch_errors
    def get_options(
        self,
        exchange: EXCHANGE_LITERAL,
        symbol: str,
        expiration: int | None = None,
        strike: int | float | None = None,
        columns: list[OPTION_COLUMN_LITERAL] | None = None,
    ) -> dict[str, Any]:
        """Fetch option chain for a symbol filtered by expiry and/or strike.

        Args:
            exchange: Exchange name (e.g. ``"BSE"``).
            symbol: Trading symbol slug (e.g. ``"SENSEX"``).
            expiration: Expiration date in YYYYMMDD format.
            strike: Strike price.
            columns: List of data columns to retrieve. Defaults to
                ``DEFAULT_OPTION_COLUMNS``.

        Returns:
            Standardized response dict with keys
            ``status``, ``data``, ``metadata``, ``error``.
        """
        v_exchange, v_symbol = self._verify_options_symbol(exchange, symbol)
        selected_columns: list[str] = (
            list(columns) if columns is not None else list(DEFAULT_OPTION_COLUMNS)
        )
        self._validate_list(columns, list(VALID_OPTION_COLUMNS))

        if expiration is None and strike is None:
            raise ValidationError(
                "At least one filter must be provided: expiration, strike, or both."
            )

        self._validate_yyyymmdd_date(expiration)

        if strike is not None and not isinstance(strike, (int, float)):
            raise ValidationError(
                f"Invalid strike value: {strike!r}. Must be int or float."
            )

        underlying = f"{v_exchange}:{v_symbol}"

        payload = {
            "columns": selected_columns,
            "filter": [{"left": "type", "operation": "equal", "right": "option"}],
            "index_filters": [{"name": "underlying_symbol", "values": [underlying]}],
        }

        if expiration is not None:
            payload["filter"].append(
                {"left": "expiration", "operation": "equal", "right": expiration}
            )

        if strike is not None:
            payload["filter"].append(
                {"left": "strike", "operation": "equal", "right": strike}
            )

        filter_value = self._build_filter_value(expiration, strike)
        return self._execute_request(payload, v_exchange, v_symbol, filter_value)

    @staticmethod
    def _build_filter_value(
        expiration: int | None,
        strike: int | float | None,
    ) -> int | float | dict[str, int | float]:
        """Return metadata-friendly filter representation."""
        if expiration is not None and strike is not None:
            return {"expiration": expiration, "strike": strike}
        if expiration is not None:
            return expiration
        assert strike is not None
        return strike

    @staticmethod
    def _serialize_filter_value(
        filter_value: int | float | dict[str, int | float],
    ) -> str:
        """Serialize filter value for export filenames."""
        if isinstance(filter_value, dict):
            parts: list[str] = []
            if "expiration" in filter_value:
                parts.append(f"exp_{filter_value['expiration']}")
            if "strike" in filter_value:
                parts.append(f"strike_{filter_value['strike']}")
            return "_".join(parts)
        return str(filter_value)

    def _execute_request(
        self,
        payload: dict[str, Any],
        exchange: str,
        symbol: str,
        filter_value: int | float | dict[str, int | float],
    ) -> dict[str, Any]:
        """Internal helper to execute the POST request and format response."""
        json_response, error_msg = self._request(
            "POST",
            OPTIONS_SCANNER_URL,
            json_payload=payload,
        )

        if error_msg:
            # Check if it's potentially a 404
            if "404" in error_msg:
                return self._error_response(
                    f"Options chain not found for symbol '{exchange}:{symbol}'. "
                    "This symbol may not have options available on TradingView.",
                    filter_value=filter_value,
                )
            return self._error_response(
                error_msg,
                filter_value=filter_value,
            )

        assert json_response is not None

        if not isinstance(json_response, dict):
            return self._error_response(
                "Invalid API response format: expected a dictionary",
                filter_value=filter_value,
            )

        fields = json_response.get("fields", [])
        raw_symbols = json_response.get("symbols", [])

        if not isinstance(fields, list) or not isinstance(raw_symbols, list):
            return self._error_response(
                "Invalid API response: 'fields' and 'symbols' must be lists",
                filter_value=filter_value,
            )

        if not raw_symbols:
            return self._error_response(
                f"No options found for symbol '{exchange}:{symbol}'. "
                "This symbol may not have options available on TradingView.",
                filter_value=filter_value,
            )

        formatted_data = []
        for item in raw_symbols:
            if not isinstance(item, dict):
                continue
            option_data = {"symbol": item.get("s")}
            values = item.get("f", [])
            for i, field in enumerate(fields):
                if i < len(values):
                    option_data[field] = values[i]
            formatted_data.append(option_data)

        if self.export_result:
            self._export(
                data=formatted_data,
                symbol=(
                    f"{exchange}_{symbol}_{self._serialize_filter_value(filter_value)}"
                ),
                data_category="options",
            )

        return self._success_response(
            formatted_data,
            total=len(formatted_data),
            total_available=json_response.get("totalCount", len(formatted_data)),
            filter_value=filter_value,
        )
