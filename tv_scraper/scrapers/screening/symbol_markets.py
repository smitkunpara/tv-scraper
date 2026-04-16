"""Symbol Markets module for finding all exchanges where a symbol is traded."""

from typing import Any, Literal, get_args

from tv_scraper.core.base import catch_errors
from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.scanner import ScannerScraper
from tv_scraper.core.validation_data import EXCHANGE_LITERAL

SYMBOL_MARKET_SCANNER_LITERAL = Literal["global", "america", "crypto", "forex", "cfd"]


class SymbolMarkets(ScannerScraper):
    """Find all markets/exchanges where a symbol is traded.

    Queries the TradingView scanner API using a name-match filter to
    discover every exchange that lists a given symbol.  Returns a
    standardized response envelope and never raises on user/network
    errors.

    Args:
        export: Export format, ``"json"`` or ``"csv"``.
            If ``None`` (default), results are not exported.
        timeout: HTTP request timeout in seconds.

    Example::

        sm = SymbolMarkets()
        result = sm.get_symbol_markets(symbol="AAPL")
        for item in result["data"]:
            print(item["symbol"], item["exchange"])
    """

    SUPPORTED_SCANNERS = set(get_args(SYMBOL_MARKET_SCANNER_LITERAL))

    DEFAULT_FIELDS: list[str] = [
        "name",
        "close",
        "change",
        "change_abs",
        "volume",
        "exchange",
        "type",
        "description",
        "currency",
        "market_cap_basic",
    ]

    @catch_errors
    def get_symbol_markets(
        self,
        exchange: EXCHANGE_LITERAL,
        symbol: str,
        fields: list[str] | None = None,
        scanner: SYMBOL_MARKET_SCANNER_LITERAL = "global",
        limit: int = 150,
    ) -> dict[str, Any]:
        """Scrape all markets/exchanges where a symbol is traded.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: The symbol to search for (e.g. ``"AAPL"``, ``"BTCUSD"``).
            fields: Columns to retrieve. Defaults to :attr:`DEFAULT_FIELDS`.
            scanner: Scanner region (``"global"``, ``"america"``, ``"crypto"``,
                ``"forex"``, ``"cfd"``).
            limit: Maximum number of results (default 150).

        Returns:
            Standardized response envelope with ``status``, ``data``,
            ``metadata``, and ``error`` keys.
        """
        # --- Validation ---
        v_exchange, v_symbol = self._verify_symbol_exchange(exchange, symbol)
        self._validate_choice(scanner, self.SUPPORTED_SCANNERS)
        self._validate_range(limit, 1, 1000)

        resolved_fields = fields if fields is not None else list(self.DEFAULT_FIELDS)

        filters = [
            {"left": "name", "operation": "match", "right": v_symbol},
            {"left": "exchange", "operation": "equal", "right": v_exchange},
        ]

        payload = {
            "filter": filters,
            "columns": resolved_fields,
            "options": {"lang": "en"},
            "range": [0, limit],
        }

        url = f"{SCANNER_URL}/{scanner}/scan"

        json_response, error_msg = self._request(
            "POST",
            url,
            json_payload=payload,
        )

        if error_msg:
            return self._error_response(error_msg)

        assert json_response is not None

        raw_items = json_response.get("data", [])
        formatted_data = self._map_scanner_rows(raw_items, resolved_fields)

        if not formatted_data:
            error_msg = (
                f"No markets found for symbol: {v_symbol}"
                if v_symbol
                else f"No markets found for exchange: {v_exchange}"
            )
            return self._error_response(error_msg)

        total_count = json_response.get("totalCount", len(formatted_data))

        if self.export_result:
            export_symbol = symbol or exchange or "symbol_markets"
            self._export(
                data=formatted_data,
                symbol=export_symbol,
                data_category="symbol_markets",
            )

        return self._success_response(
            formatted_data,
            total=len(formatted_data),
            total_available=total_count,
        )
