"""Symbol Markets module for finding all exchanges where a symbol is traded."""

from typing import Any

import requests

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import SCANNER_URL


class SymbolMarkets(BaseScraper):
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

    def get_symbol_markets(
        self,
        symbol: str,
        fields: list[str] | None = None,
        scanner: str = "global",
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

        # Validate symbol
        if not search_symbol.strip():
            return self._error_response(
                "Symbol must be a non-empty string.",
                symbol=symbol,
                scanner=scanner,
                limit=limit,
            )

        # Validate scanner
        if scanner not in self.SUPPORTED_SCANNERS:
            return self._error_response(
                f"Unsupported scanner: '{scanner}'. "
                f"Supported scanners: {', '.join(sorted(self.SUPPORTED_SCANNERS))}",
                symbol=symbol,
                scanner=scanner,
                limit=limit,
            )

        resolved_fields = fields if fields is not None else list(self.DEFAULT_FIELDS)

        payload = self._build_payload(
            symbol=search_symbol,
            fields=resolved_fields,
            limit=limit,
        )

        url = f"{SCANNER_URL}/{scanner}/scan"

        try:
            response = requests.post(
                url,
                headers=self._headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            json_response = response.json()
        except requests.RequestException as exc:
            return self._error_response(
                f"Network error: {exc}",
                symbol=symbol,
                scanner=scanner,
                limit=limit,
            )
        except ValueError as exc:
            return self._error_response(
                f"JSON parse error: {exc}",
                symbol=symbol,
                scanner=scanner,
                limit=limit,
            )

        raw_items = json_response.get("data", [])
        formatted_data = self._map_scanner_rows(raw_items, resolved_fields)

        if not formatted_data:
            return self._error_response(
                f"No markets found for symbol: {symbol}",
                symbol=symbol,
                scanner=scanner,
                limit=limit,
            )

        total_count = json_response.get("totalCount", len(formatted_data))

        if self.export_result:
            self._export(
                data=formatted_data,
                symbol=symbol,
                data_category="symbol_markets",
            )

        return self._success_response(
            formatted_data,
            symbol=symbol,
            scanner=scanner,
            limit=limit,
            total=len(formatted_data),
            total_available=total_count,
        )
