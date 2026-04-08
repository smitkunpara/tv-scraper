"""Options scraper for fetching option chain data from TradingView."""

from typing import Any

from tv_scraper.core import validators
from tv_scraper.core.base import catch_errors
from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.exceptions import ValidationError
from tv_scraper.core.scanner import ScannerScraper
from tv_scraper.core.validation_data import EXCHANGE_LITERAL

OPTIONS_SCANNER_URL = f"{SCANNER_URL}/options/scan2?label-product=symbols-options"

DEFAULT_OPTION_COLUMNS = [
    "ask",
    "bid",
    "currency",
    "delta",
    "expiration",
    "gamma",
    "iv",
    "option-type",
    "pricescale",
    "rho",
    "root",
    "strike",
    "theoPrice",
    "theta",
    "vega",
    "bid_iv",
    "ask_iv",
]

VALID_OPTION_COLUMNS = set(DEFAULT_OPTION_COLUMNS)


class Options(ScannerScraper):
    """Scraper for option chain data from TradingView.

    Fetches option chains for a given underlying symbol, filtered by
    either expiration date or strike price.

    Args:
        export_result: Whether to export results to file.
        export_type: Export format, ``"json"`` or ``"csv"``.
        timeout: HTTP request timeout in seconds.

    Example::

        from tv_scraper.scrapers.market_data import Options

        scraper = Options()
        # Get by expiry
        result = scraper.get_options_by_expiry(
            exchange="BSE",
            symbol="SENSEX",
            expiration=20260219,
            root="BSX"
        )
        # Get by strike
        result = scraper.get_options_by_strike(
            exchange="BSE",
            symbol="SENSEX",
            strike=83300
        )
    """

    @catch_errors
    def get_options_by_expiry(
        self,
        exchange: EXCHANGE_LITERAL,
        symbol: str,
        expiration: int,
        root: str,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fetch option chain for a symbol filtered by expiration date.

        Args:
            exchange: Exchange name (e.g. ``"BSE"``).
            symbol: Trading symbol slug (e.g. ``"SENSEX"``).
            expiration: Expiration date in YYYYMMDD format (e.g. ``20260219``).
            root: Root symbol for the option (e.g. ``"BSX"``).
            columns: List of data columns to retrieve. Defaults to
                :attr:`DEFAULT_OPTION_COLUMNS`.

        Returns:
            Standardized response dict with keys
            ``status``, ``data``, ``metadata``, ``error``.
        """
        validators.verify_options_symbol(exchange, symbol)
        if columns is not None:
            validators.validate_fields(columns, list(VALID_OPTION_COLUMNS), "columns")

        underlying = f"{exchange}:{symbol}"
        cols = columns if columns is not None else DEFAULT_OPTION_COLUMNS

        payload = {
            "columns": cols,
            "filter": [
                {"left": "type", "operation": "equal", "right": "option"},
                {"left": "expiration", "operation": "equal", "right": expiration},
                {"left": "root", "operation": "equal", "right": root},
            ],
            "index_filters": [{"name": "underlying_symbol", "values": [underlying]}],
        }

        return self._execute_request(payload, exchange, symbol, expiration)

    @catch_errors
    def get_options_by_strike(
        self,
        exchange: EXCHANGE_LITERAL,
        symbol: str,
        strike: int | float,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fetch option chain for a symbol filtered by strike price.

        Args:
            exchange: Exchange name (e.g. ``"BSE"``).
            symbol: Trading symbol slug (e.g. ``"SENSEX"``).
            strike: Strike price (e.g. ``83300``).
            columns: List of data columns to retrieve. Defaults to
                :attr:`DEFAULT_OPTION_COLUMNS`.

        Returns:
            Standardized response dict with keys
            ``status``, ``data``, ``metadata``, ``error``.
        """
        validators.verify_options_symbol(exchange, symbol)
        if columns is not None:
            validators.validate_fields(columns, list(VALID_OPTION_COLUMNS), "columns")

        if not isinstance(strike, (int, float)):
            raise ValidationError(
                f"Invalid strike value: {strike!r}. Must be int or float."
            )

        underlying = f"{exchange}:{symbol}"
        cols = columns if columns is not None else DEFAULT_OPTION_COLUMNS

        payload = {
            "columns": cols,
            "filter": [
                {"left": "type", "operation": "equal", "right": "option"},
                {"left": "strike", "operation": "equal", "right": strike},
            ],
            "index_filters": [{"name": "underlying_symbol", "values": [underlying]}],
        }

        return self._execute_request(payload, exchange, symbol, strike)

    def _execute_request(
        self,
        payload: dict[str, Any],
        exchange: str,
        symbol: str,
        filter_value: int | float,
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
                symbol=f"{exchange}_{symbol}_{filter_value}",
                data_category="options",
            )

        return self._success_response(
            formatted_data,
            total=json_response.get("totalCount", len(formatted_data)),
            filter_value=filter_value,
        )
