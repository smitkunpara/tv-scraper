"""Symbol Markets module for finding all exchanges where a symbol is traded."""

from typing import Any, Literal

from tv_scraper.core import validators
from tv_scraper.core.base import catch_errors
from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.scanner import ScannerScraper

SYMBOL_MARKET_SCANNER_LITERAL = Literal["global", "america", "crypto", "forex", "cfd"]


class SymbolMarkets(ScannerScraper):
    """Find all markets/exchanges where a symbol is traded.

    Queries the TradingView scanner API using a name-match filter to
    discover every exchange that lists a given symbol.  Returns a
    standardized response envelope and never raises on user/network
    errors.

    Args:
        export_result: Whether to export results to file.
        export_type: Export format, ``"json"`` or ``"csv"``.
        timeout: HTTP request timeout in seconds.

    Example::

        sm = SymbolMarkets()
        result = sm.get_symbol_markets(symbol="AAPL")
        for item in result["data"]:
            print(item["symbol"], item["exchange"])
    """

    SUPPORTED_SCANNERS: set[str] = {
        "global",
        "america",
        "crypto",
        "forex",
        "cfd",
    }

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

    def _build_payload(
        self,
        symbol: str,
        fields: list[str],
        limit: int,
    ) -> dict[str, Any]:
        """Build the scanner API request payload.

        Args:
            symbol: Symbol name to match against.
            fields: Columns to retrieve.
            limit: Maximum number of results.

        Returns:
            Payload dict ready for JSON serialization.
        """
        return {
            "filter": [
                {"left": "name", "operation": "match", "right": symbol},
            ],
            "columns": fields,
            "options": {"lang": "en"},
            "range": [0, limit],
        }

    @catch_errors
    def get_symbol_markets(
        self,
        symbol: str,
        fields: list[str] | None = None,
        scanner: SYMBOL_MARKET_SCANNER_LITERAL = "global",
        limit: int = 150,
    ) -> dict[str, Any]:
        """Scrape all markets/exchanges where a symbol is traded.

        Args:
            symbol: The symbol to search for (e.g. ``"AAPL"``, ``"BTCUSD"``).
            fields: Columns to retrieve. Defaults to :attr:`DEFAULT_FIELDS`.
            scanner: Scanner region (``"global"``, ``"america"``, ``"crypto"``,
                ``"forex"``, ``"cfd"``).
            limit: Maximum number of results (default 150).

        Returns:
            Standardized response envelope with ``status``, ``data``,
            ``metadata``, and ``error`` keys.
        """
        # Support combined EXCHANGE:SYMBOL by extracting the symbol name
        search_symbol = symbol.split(":", 1)[1] if ":" in symbol else symbol

        # --- Validation ---
        validators.validate_symbol("global", search_symbol)
        validators.validate_choice("scanner", scanner, self.SUPPORTED_SCANNERS)
        validators.validate_range("limit", limit, 1, 1000)

        resolved_fields = fields if fields is not None else list(self.DEFAULT_FIELDS)

        payload = self._build_payload(
            symbol=search_symbol,
            fields=resolved_fields,
            limit=limit,
        )

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
            return self._error_response(f"No markets found for symbol: {symbol}")

        total_count = json_response.get("totalCount", len(formatted_data))

        if self.export_result:
            self._export(
                data=formatted_data,
                symbol=symbol,
                data_category="symbol_markets",
            )

        return self._success_response(
            formatted_data,
            total=len(formatted_data),
            total_available=total_count,
        )
