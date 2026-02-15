"""Screener module for screening financial instruments with custom filters."""

import logging
from typing import Any, Dict, List, Optional

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.exceptions import NetworkError

logger = logging.getLogger(__name__)


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
        result = screener.screen(
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

    OPERATIONS: list[str] = [
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
    ]

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

    def _get_default_fields(self, market: str) -> List[str]:
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

    def _build_payload(
        self,
        fields: List[str],
        market: str,
        filters: Optional[List[Dict[str, Any]]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Build the scanner API request payload.

        Args:
            fields: Columns to retrieve.
            market: Market identifier.
            filters: Optional list of filter condition dicts.
            sort_by: Optional field to sort by.
            sort_order: Sort direction (``"asc"`` or ``"desc"``).
            limit: Maximum number of results.

        Returns:
            Payload dict ready for JSON serialization.
        """
        payload: Dict[str, Any] = {
            "columns": fields,
            "options": {"lang": "en"},
            "range": [0, limit],
        }
        if filters:
            payload["filter"] = filters
        if sort_by:
            payload["sort"] = {
                "sortBy": sort_by,
                "sortOrder": sort_order,
            }
        return payload

    def screen(
        self,
        market: str = "america",
        filters: Optional[List[Dict[str, Any]]] = None,
        fields: Optional[List[str]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Screen financial instruments based on custom filters.

        Args:
            market: The market to screen (e.g. ``"america"``, ``"crypto"``).
            filters: List of filter dicts, each with ``left``, ``operation``,
                and ``right`` keys.
            fields: Columns to retrieve. Defaults to market-specific defaults.
            sort_by: Field to sort by.
            sort_order: Sort direction, ``"asc"`` or ``"desc"``.
            limit: Maximum number of results (default 50).

        Returns:
            Standardized response envelope with ``status``, ``data``,
            ``metadata``, and ``error`` keys.
        """
        # Validate market
        if market not in self.SUPPORTED_MARKETS:
            return self._error_response(
                f"Unsupported market: '{market}'. "
                f"Supported markets: {', '.join(sorted(self.SUPPORTED_MARKETS))}",
            )

        # Resolve fields
        resolved_fields = fields if fields is not None else self._get_default_fields(market)

        # Build payload
        payload = self._build_payload(
            fields=resolved_fields,
            market=market,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
        )

        url = f"{SCANNER_URL}/{market}/scan"

        try:
            response = self._make_request(url, method="POST", json_data=payload)
            json_response = response.json()

            raw_items = json_response.get("data", [])
            formatted_data = self._map_scanner_rows(raw_items, resolved_fields)

            total_count = json_response.get("totalCount", len(formatted_data))

            if self.export_result:
                self._export(
                    data=formatted_data,
                    symbol=f"{market}_screener",
                    data_category="screener",
                )

            return self._success_response(
                formatted_data,
                market=market,
                total=len(formatted_data),
                total_available=total_count,
            )
        except NetworkError as exc:
            return self._error_response(str(exc))
        except Exception as exc:
            return self._error_response(f"Request failed: {exc}")
