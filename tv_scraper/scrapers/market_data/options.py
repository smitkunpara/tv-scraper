"""Options scraper for fetching option chain data from TradingView."""

import logging
from typing import Any

import requests

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.exceptions import ValidationError

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
        exchange: str,
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

        # Validation — verify combination exists and has options
        try:
            self.validator.verify_options_symbol(exchange, symbol)
        except ValidationError as exc:
            return self._error_response(
                str(exc),
                exchange=exchange,
                symbol=symbol,
                expiration=expiration,
                root=root,
            )

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

    def get_options_by_strike(
        self,
        exchange: str,
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

        try:
            self.validator.verify_options_symbol(exchange, symbol)
        except ValidationError as exc:
            return self._error_response(
                str(exc),
                exchange=exchange,
                symbol=symbol,
                strike=strike,
            )

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
            response = requests.post(
                OPTIONS_SCANNER_URL,
                json=payload,
                headers=self._headers,
                timeout=self.timeout,
            )

            if response.status_code == 404:
                return self._error_response(
                    f"Options chain not found for symbol '{exchange}:{symbol}'. "
                    "This symbol may not have options available on TradingView.",
                    exchange=exchange,
                    symbol=symbol,
                    filter_type=filter_type,
                    filter_value=filter_value,
                )

            response.raise_for_status()
            json_response = response.json()
        except requests.RequestException as exc:
            return self._error_response(
                f"Network error: {exc}",
                exchange=exchange,
                symbol=symbol,
                filter_type=filter_type,
                filter_value=filter_value,
            )
        except (ValueError, KeyError) as exc:
            return self._error_response(
                f"Failed to parse API response: {exc}",
                exchange=exchange,
                symbol=symbol,
                filter_type=filter_type,
                filter_value=filter_value,
            )
        except Exception as exc:
            return self._error_response(
                f"Request failed: {exc}",
                exchange=exchange,
                symbol=symbol,
                filter_type=filter_type,
                filter_value=filter_value,
            )

        fields = json_response.get("fields", [])
        raw_symbols = json_response.get("symbols", [])

        if not raw_symbols:
            return self._error_response(
                f"No options found for symbol '{exchange}:{symbol}'. "
                "This symbol may not have options available on TradingView.",
                exchange=exchange,
                symbol=symbol,
                filter_type=filter_type,
                filter_value=filter_value,
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
