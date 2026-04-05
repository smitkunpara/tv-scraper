"""Screener module for screening financial instruments with custom filters."""

import logging
from typing import Any

import requests

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import SCANNER_URL

logger = logging.getLogger(__name__)

SORT_ORDERS: frozenset[str] = frozenset({"asc", "desc"})
MIN_LIMIT = 1
MAX_LIMIT = 10000


class Screener(BaseScraper):
    """Screen financial instruments across markets with custom filters.

    Supports stocks, crypto, forex, bonds, futures, and CFDs via the
    TradingView scanner API.  Returns a standardized response envelope
    and never raises on user/network errors.

    Args:
        export_result: Whether to export results to file.
        export_type: Export format, ``"json"`` or ``"csv"``.
        timeout: HTTP request timeout in seconds.

    Example::

        screener = Screener()
        result = screener.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "greater", "right": 100}],
            fields=["name", "close", "volume", "market_cap_basic"],
        )
    """

    SUPPORTED_MARKETS: set[str] = {
        "america",
        "australia",
        "canada",
        "germany",
        "india",
        "israel",
        "italy",
        "luxembourg",
        "mexico",
        "spain",
        "turkey",
        "uk",
        "crypto",
        "forex",
        "cfd",
        "futures",
        "bonds",
        "global",
    }

    OPERATIONS: frozenset[str] = frozenset(
        {
            "greater",
            "less",
            "egreater",
            "eless",
            "equal",
            "nequal",
            "in_range",
            "not_in_range",
            "above",
            "below",
            "crosses",
            "crosses_above",
            "crosses_below",
            "has",
            "has_none_of",
        }
    )

    DEFAULT_STOCK_FIELDS: list[str] = [
        "name",
        "close",
        "change",
        "change_abs",
        "volume",
        "Recommend.All",
        "market_cap_basic",
        "price_earnings_ttm",
        "earnings_per_share_basic_ttm",
    ]

    DEFAULT_CRYPTO_FIELDS: list[str] = [
        "name",
        "close",
        "change",
        "change_abs",
        "volume",
        "market_cap_calc",
        "Recommend.All",
    ]

    DEFAULT_FOREX_FIELDS: list[str] = [
        "name",
        "close",
        "change",
        "change_abs",
        "Recommend.All",
    ]

    def _get_default_fields(self, market: str) -> list[str]:
        """Return default fields for the given market type.

        Args:
            market: Market identifier (e.g. ``"crypto"``, ``"forex"``).

        Returns:
            List of default field names.
        """
        if market == "crypto":
            return list(self.DEFAULT_CRYPTO_FIELDS)
        if market == "forex":
            return list(self.DEFAULT_FOREX_FIELDS)
        return list(self.DEFAULT_STOCK_FIELDS)

    def _validate_filter(self, filters: list[dict[str, Any]]) -> str | None:
        """Validate filter structure.

        Args:
            filters: List of filter dicts to validate.

        Returns:
            Error message if validation fails, None otherwise.
        """
        for i, f in enumerate(filters):
            if not isinstance(f, dict):
                return f"Filter at index {i} must be a dictionary"
            if "left" not in f:
                return f"Filter at index {i} missing required 'left' key"
            if "operation" not in f:
                return f"Filter at index {i} missing required 'operation' key"
            if f["operation"] not in self.OPERATIONS:
                return (
                    f"Invalid operation '{f['operation']}' in filter at index {i}. "
                    f"Valid operations: {', '.join(sorted(self.OPERATIONS))}"
                )
        return None

    def _validate_filter2(self, filter2: dict[str, Any]) -> str | None:
        """Validate filter2 structure.

        Args:
            filter2: Filter2 dict to validate.

        Returns:
            Error message if validation fails, None otherwise.
        """
        if not isinstance(filter2, dict):
            return "filter2 must be a dictionary"
        if "operator" not in filter2:
            return "filter2 missing required 'operator' key"
        return None

    def _build_metadata(
        self,
        market: str,
        sort_order: str,
        limit: int,
        filters: list[dict[str, Any]] | None = None,
        sort_by: str | None = None,
        symbols: dict[str, Any] | None = None,
        filter2: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build metadata dict for response envelope.

        Args:
            market: Market identifier.
            sort_order: Sort direction.
            limit: Result limit.
            filters: Optional filters list.
            sort_by: Optional sort field.
            symbols: Optional symbols filter.
            filter2: Optional complex filter.

        Returns:
            Metadata dict for response envelope.
        """
        meta: dict[str, Any] = {
            "market": market,
            "sort_order": sort_order,
            "limit": limit,
        }
        if filters is not None:
            meta["filters"] = filters
        if sort_by is not None:
            meta["sort_by"] = sort_by
        if symbols is not None:
            meta["symbols"] = symbols
        if filter2 is not None:
            meta["filter2"] = filter2
        return meta

    def _build_payload(
        self,
        fields: list[str],
        market: str,
        filters: list[dict[str, Any]] | None = None,
        sort_by: str | None = None,
        sort_order: str = "desc",
        limit: int = 50,
        symbols: dict[str, Any] | None = None,
        filter2: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build the scanner API request payload.

        Args:
            fields: Columns to retrieve.
            market: Market identifier, auto-derived into the ``markets`` body field.
            filters: Optional list of filter condition dicts.
            sort_by: Optional field to sort by.
            sort_order: Sort direction (``"asc"`` or ``"desc"``).
            limit: Maximum number of results.

        Returns:
            Payload dict ready for JSON serialization.
        """
        if market not in self.SUPPORTED_MARKETS:
            raise ValueError(
                f"Unsupported market: '{market}'. "
                f"Supported markets: {', '.join(sorted(self.SUPPORTED_MARKETS))}"
            )
        payload: dict[str, Any] = {
            "columns": fields,
            "options": {"lang": "en"},
            "range": [0, limit],
            "markets": [market],
        }
        if filters:
            payload["filter"] = filters
        if sort_by:
            payload["sort"] = {
                "sortBy": sort_by,
                "sortOrder": sort_order,
            }
        if symbols:
            payload["symbols"] = symbols
        if filter2:
            payload["filter2"] = filter2
        return payload

    def get_screener(
        self,
        market: str = "america",
        filters: list[dict[str, Any]] | None = None,
        fields: list[str] | None = None,
        sort_by: str | None = None,
        sort_order: str = "desc",
        limit: int = 50,
        symbols: dict[str, Any] | None = None,
        filter2: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Screen financial instruments based on custom filters.

        Args:
            market: The market to screen (e.g. ``"america"``, ``"crypto"``).
            filters: List of filter dicts, each with ``left``, ``operation``,
                and ``right`` keys.
            fields: Columns to retrieve. Defaults to market-specific defaults.
            sort_by: Field to sort by.
            sort_order: Sort direction, ``"asc"`` or ``"desc"``.
            limit: Maximum number of results (default 50).
            symbols: Optional symbols filter for index-based filtering.
                Use ``{"symbolset": ["SYML:SP;SPX"]}`` for S&P 500,
                ``{"symbolset": ["SYML:NASDAQ;NDX"]}`` for NASDAQ 100, etc.
                Can also use ``{"tickers": ["NASDAQ:AAPL", "NYSE:JPM"]}`` for
                explicit symbol lists.
            filter2: Optional complex filter with boolean logic using
                ``operator``, ``operands``, and ``expression`` keys.

        Returns:
            Standardized response envelope with ``status``, ``data``,
            ``metadata``, and ``error`` keys.
        """
        if market not in self.SUPPORTED_MARKETS:
            return self._error_response(
                f"Unsupported market: '{market}'. "
                f"Supported markets: {', '.join(sorted(self.SUPPORTED_MARKETS))}",
                market=market,
                sort_order=sort_order,
                limit=limit,
            )

        if sort_order not in SORT_ORDERS:
            return self._error_response(
                f"Invalid sort_order: '{sort_order}'. Must be 'asc' or 'desc'.",
                market=market,
                sort_order=sort_order,
                limit=limit,
            )

        if not isinstance(limit, int) or limit < MIN_LIMIT or limit > MAX_LIMIT:
            return self._error_response(
                f"Invalid limit: {limit}. Must be an integer between {MIN_LIMIT} and {MAX_LIMIT}.",
                market=market,
                sort_order=sort_order,
                limit=limit,
            )

        if filters is not None:
            filter_error = self._validate_filter(filters)
            if filter_error:
                return self._error_response(
                    filter_error, market=market, sort_order=sort_order, limit=limit
                )

        if filter2 is not None:
            filter2_error = self._validate_filter2(filter2)
            if filter2_error:
                return self._error_response(
                    filter2_error, market=market, sort_order=sort_order, limit=limit
                )

        resolved_fields = (
            fields if fields is not None else self._get_default_fields(market)
        )

        payload = self._build_payload(
            fields=resolved_fields,
            market=market,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            symbols=symbols,
            filter2=filter2,
        )

        url = f"{SCANNER_URL}/{market}/scan"

        try:
            response = requests.post(
                url,
                headers=self._headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            return self._error_response(
                f"HTTP error: {exc}",
                **self._build_metadata(
                    market, sort_order, limit, filters, sort_by, symbols, filter2
                ),
            )
        except requests.RequestException as exc:
            return self._error_response(
                f"Network error: {exc}",
                **self._build_metadata(
                    market, sort_order, limit, filters, sort_by, symbols, filter2
                ),
            )

        try:
            json_response = response.json()
        except ValueError as exc:
            return self._error_response(
                f"Failed to parse JSON response: {exc}",
                **self._build_metadata(
                    market, sort_order, limit, filters, sort_by, symbols, filter2
                ),
            )

        raw_items = json_response.get("data", [])
        formatted_data = self._map_scanner_rows(raw_items, resolved_fields)

        total_count = json_response.get("totalCount", len(formatted_data))

        if self.export_result:
            self._export(
                data=formatted_data,
                symbol=f"{market}_screener",
                data_category="screener",
            )

        screener_meta = self._build_metadata(
            market, sort_order, limit, filters, sort_by, symbols, filter2
        )
        screener_meta["total"] = len(formatted_data)
        screener_meta["total_available"] = total_count
        return self._success_response(formatted_data, **screener_meta)
