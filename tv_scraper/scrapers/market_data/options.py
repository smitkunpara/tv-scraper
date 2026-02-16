"""Options scraper for fetching option chain data from TradingView."""

import logging
from typing import Any

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.exceptions import NetworkError, ValidationError

logger = logging.getLogger(__name__)

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


class Options(BaseScraper):
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
        result = scraper.get_chain_by_expiry(
            exchange="BSE",
            symbol="SENSEX",
            expiration=20260219,
            root="BSX"
        )
        # Get by strike
        result = scraper.get_chain_by_strike(
            exchange="BSE",
            symbol="SENSEX",
            strike=83300
        )
    """

    def get_chain_by_expiry(
        self,
        exchange: str,
        symbol: str,
        expiration: int,
        root: str,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fetch option chain for a symbol filtered by expiration date.

        Args:
            exchange: Exchange name (e.g. ``"BSE"``). Can be empty if
                combined symbol is used in the `symbol` parameter.
            symbol: Trading symbol slug (e.g. ``"SENSEX"``) or combined
                ``"EXCHANGE:SYMBOL"`` string (e.g. ``"BSE:SENSEX"``).
            expiration: Expiration date in YYYYMMDD format (e.g. ``20260219``).
            root: Root symbol for the option (e.g. ``"BSX"``).
            columns: List of data columns to retrieve. Defaults to
                :attr:`DEFAULT_OPTION_COLUMNS`.

        Returns:
            Standardized response dict with keys
            ``status``, ``data``, ``metadata``, ``error``.
        """
        # Support combined EXCHANGE:SYMBOL
        if not exchange and ":" in symbol:
            exchange, symbol = symbol.split(":", 1)

        # Validation
        try:
            self.validator.validate_exchange(exchange)
            self.validator.validate_symbol(exchange, symbol)
        except ValidationError as exc:
            return self._error_response(str(exc))

        cols = columns if columns is not None else DEFAULT_OPTION_COLUMNS
        underlying = f"{exchange}:{symbol}"

        payload = {
            "columns": cols,
            "filter": [
                {"left": "type", "operation": "equal", "right": "option"},
                {"left": "expiration", "operation": "equal", "right": expiration},
                {"left": "root", "operation": "equal", "right": root},
            ],
            "ignore_unknown_fields": False,
            "index_filters": [{"name": "underlying_symbol", "values": [underlying]}],
        }

        return self._execute_request(payload, exchange, symbol, "expiry", expiration)

    def get_chain_by_strike(
        self,
        exchange: str,
        symbol: str,
        strike: int | float,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fetch option chain for a symbol filtered by strike price.

        Args:
            exchange: Exchange name (e.g. ``"BSE"``). Can be empty if
                combined symbol is used in the `symbol` parameter.
            symbol: Trading symbol slug (e.g. ``"SENSEX"``) or combined
                ``"EXCHANGE:SYMBOL"`` string (e.g. ``"BSE:SENSEX"``).
            strike: Strike price (e.g. ``83300``).
            columns: List of data columns to retrieve. Defaults to
                :attr:`DEFAULT_OPTION_COLUMNS`.

        Returns:
            Standardized response dict with keys
            ``status``, ``data``, ``metadata``, ``error``.
        """
        # Support combined EXCHANGE:SYMBOL
        if not exchange and ":" in symbol:
            exchange, symbol = symbol.split(":", 1)

        # Validation
        try:
            self.validator.validate_exchange(exchange)
            self.validator.validate_symbol(exchange, symbol)
        except ValidationError as exc:
            return self._error_response(str(exc))

        cols = columns if columns is not None else DEFAULT_OPTION_COLUMNS
        underlying = f"{exchange}:{symbol}"

        payload = {
            "columns": cols,
            "filter": [
                {"left": "type", "operation": "equal", "right": "option"},
                {"left": "strike", "operation": "equal", "right": strike},
            ],
            "ignore_unknown_fields": False,
            "index_filters": [{"name": "underlying_symbol", "values": [underlying]}],
        }

        return self._execute_request(payload, exchange, symbol, "strike", strike)

    def _execute_request(
        self,
        payload: dict[str, Any],
        exchange: str,
        symbol: str,
        filter_type: str,
        filter_value: Any,
    ) -> dict[str, Any]:
        """Internal helper to execute the POST request and format response."""
        try:
            response = self._make_request(
                OPTIONS_SCANNER_URL, method="POST", json_data=payload
            )

            if response.status_code == 404:
                return self._error_response(
                    f"Options chain not found for symbol '{exchange}:{symbol}'. "
                    "This symbol may not have options available on TradingView."
                )

            response.raise_for_status()
            json_response = response.json()
        except NetworkError as exc:
            return self._error_response(str(exc))
        except (ValueError, KeyError) as exc:
            return self._error_response(f"Failed to parse API response: {exc}")
        except Exception as exc:
            return self._error_response(f"Request failed: {exc}")

        fields = json_response.get("fields", [])
        raw_symbols = json_response.get("symbols", [])

        if not raw_symbols:
            return self._error_response(
                f"No options found for symbol '{exchange}:{symbol}'. "
                "This symbol may not have options available on TradingView."
            )

        formatted_data = []
        for item in raw_symbols:
            option_data = {"symbol": item.get("s")}
            values = item.get("f", [])
            for i, field in enumerate(fields):
                if i < len(values):
                    option_data[field] = values[i]
            formatted_data.append(option_data)

        # Export if requested
        if self.export_result:
            self._export(
                data=formatted_data,
                symbol=f"{exchange}_{symbol}_{filter_type}_{filter_value}",
                data_category="options",
            )

        return self._success_response(
            formatted_data,
            exchange=exchange,
            symbol=symbol,
            total=json_response.get("totalCount", len(formatted_data)),
            filter_type=filter_type,
            filter_value=filter_value,
        )
