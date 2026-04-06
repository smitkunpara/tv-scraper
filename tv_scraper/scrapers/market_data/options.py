"""Options scraper for fetching option chain data from TradingView."""

from typing import Any

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
        error = self._validate_inputs(exchange, symbol, columns)
        if error:
            return error

        underlying = f"{exchange}:{symbol}"
        cols = columns if columns is not None else DEFAULT_OPTION_COLUMNS

        payload = self._build_payload(
            cols=cols,
            underlying=underlying,
            filter_type="expiry",
            filter_value=expiration,
            additional_filters=[
                {"left": "type", "operation": "equal", "right": "option"},
                {"left": "expiration", "operation": "equal", "right": expiration},
                {"left": "root", "operation": "equal", "right": root},
            ],
        )

        return self._execute_request(payload, exchange, symbol, expiration)

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
        error = self._validate_inputs(exchange, symbol, columns)
        if error:
            return error

        if not isinstance(strike, (int, float)):
            return self._error_response(
                f"Invalid strike value: {strike!r}. Must be int or float.",
                exchange=exchange,
                symbol=symbol,
                strike=strike,
            )

        underlying = f"{exchange}:{symbol}"
        cols = columns if columns is not None else DEFAULT_OPTION_COLUMNS

        payload = self._build_payload(
            cols=cols,
            underlying=underlying,
            filter_type="strike",
            filter_value=strike,
            additional_filters=[
                {"left": "type", "operation": "equal", "right": "option"},
                {"left": "strike", "operation": "equal", "right": strike},
            ],
        )

        return self._execute_request(payload, exchange, symbol, strike)

    def _validate_inputs(
        self, exchange: str, symbol: str, columns: list[str] | None
    ) -> dict[str, Any] | None:
        """Validate exchange, symbol, and columns. Returns error dict or None."""
        try:
            exchange, symbol = self.validator.verify_options_symbol(exchange, symbol)
        except ValidationError as exc:
            return self._error_response(
                str(exc),
                exchange=exchange,
                symbol=symbol,
            )

        if columns is not None:
            invalid_cols = [c for c in columns if c not in VALID_OPTION_COLUMNS]
            if invalid_cols:
                return self._error_response(
                    f"Invalid column names: {invalid_cols}. "
                    f"Valid columns: {sorted(VALID_OPTION_COLUMNS)}",
                    exchange=exchange,
                    symbol=symbol,
                )

        return None

    def _build_payload(
        self,
        cols: list[str],
        underlying: str,
        filter_type: str,
        filter_value: int | float,
        additional_filters: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build the request payload for the options scanner API."""
        return {
            "columns": cols,
            "filter": additional_filters,
            "index_filters": [{"name": "underlying_symbol", "values": [underlying]}],
        }

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
                    exchange=exchange,
                    symbol=symbol,
                    filter_value=filter_value,
                )
            return self._error_response(
                error_msg,
                exchange=exchange,
                symbol=symbol,
                filter_value=filter_value,
            )

        assert json_response is not None

        if not isinstance(json_response, dict):
            return self._error_response(
                "Invalid API response format: expected a dictionary",
                exchange=exchange,
                symbol=symbol,
                filter_value=filter_value,
            )

        fields = json_response.get("fields", [])
        raw_symbols = json_response.get("symbols", [])

        if not isinstance(fields, list) or not isinstance(raw_symbols, list):
            return self._error_response(
                "Invalid API response: 'fields' and 'symbols' must be lists",
                exchange=exchange,
                symbol=symbol,
                filter_value=filter_value,
            )

        if not raw_symbols:
            return self._error_response(
                f"No options found for symbol '{exchange}:{symbol}'. "
                "This symbol may not have options available on TradingView.",
                exchange=exchange,
                symbol=symbol,
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
            exchange=exchange,
            symbol=symbol,
            total=json_response.get("totalCount", len(formatted_data)),
            filter_value=filter_value,
        )
