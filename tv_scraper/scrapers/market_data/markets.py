"""Markets scraper for retrieving top stocks by various criteria.

Queries the TradingView scanner API to fetch ranked stock lists
across supported markets, sorted by market cap, volume, change, etc.
"""

from typing import Any, Literal

from tv_scraper.core import validators
from tv_scraper.core.base import catch_errors
from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.scanner import ScannerScraper

MARKET_LITERAL = Literal[
    "america",
    "australia",
    "canada",
    "germany",
    "india",
    "uk",
    "crypto",
    "forex",
    "global",
]
MARKET_SORT_LITERAL = Literal["market_cap", "volume", "change", "price", "volatility"]
SORT_ORDER_LITERAL = Literal["asc", "desc"]


class Markets(ScannerScraper):
    """Scraper for market-wide stock rankings.

    Fetches top stocks from the TradingView scanner API, optionally
    filtered by market region and sorted by a chosen criterion.

    Args:
        export_result: Whether to export results to file.
        export_type: Export format, ``"json"`` or ``"csv"``.
        timeout: HTTP request timeout in seconds.

    Example::

        markets = Markets()
        result = markets.get_markets(market="america", sort_by="market_cap", limit=20)
        for stock in result["data"]:
            print(stock["symbol"], stock["close"])
    """

    VALID_MARKETS: list[str] = [
        "america",
        "australia",
        "canada",
        "germany",
        "india",
        "uk",
        "crypto",
        "forex",
        "global",
    ]

    SORT_CRITERIA: dict[str, str] = {
        "market_cap": "market_cap_basic",
        "volume": "volume",
        "change": "change",
        "price": "close",
        "volatility": "Volatility.D",
    }

    DEFAULT_FIELDS: list[str] = [
        "name",
        "close",
        "change",
        "change_abs",
        "volume",
        "Recommend.All",
        "market_cap_basic",
        "price_earnings_ttm",
        "earnings_per_share_basic_ttm",
        "sector",
        "industry",
    ]

    STOCK_FILTERS: list[dict[str, str]] = [
        {"left": "type", "operation": "equal", "right": "stock"},
        {"left": "market_cap_basic", "operation": "nempty"},
    ]

    @catch_errors
    def get_markets(
        self,
        market: MARKET_LITERAL = "america",
        sort_by: MARKET_SORT_LITERAL = "market_cap",
        fields: list[str] | None = None,
        sort_order: SORT_ORDER_LITERAL = "desc",
        limit: int = 50,
    ) -> dict[str, Any]:
        """Get top stocks ranked by the chosen criterion.

        Args:
            market: Market region to scan (e.g. ``"america"``, ``"india"``).
            sort_by: Sort criterion key (``"market_cap"``, ``"volume"``,
                ``"change"``, ``"price"``, ``"volatility"``).
            fields: List of scanner fields to retrieve.  Uses
                :attr:`DEFAULT_FIELDS` when ``None``.
            sort_order: ``"desc"`` (default) or ``"asc"``.
            limit: Maximum number of results to return.

        Returns:
            Standardized response dict with ``status``, ``data``,
            ``metadata``, and ``error`` keys.
        """
        validators.validate_choice("market", market, self.VALID_MARKETS)
        validators.validate_choice("sort_by", sort_by, list(self.SORT_CRITERIA.keys()))
        validators.validate_choice("sort_order", sort_order, ["asc", "desc"])
        validators.validate_range("limit", limit, 1, 1000)

        # --- build payload ---------------------------------------------
        used_fields = fields if fields is not None else self.DEFAULT_FIELDS
        sort_field = self.SORT_CRITERIA[sort_by]

        payload: dict[str, Any] = {
            "columns": used_fields,
            "options": {"lang": "en"},
            "range": [0, limit],
            "sort": {
                "sortBy": sort_field,
                "sortOrder": sort_order,
            },
            "filter": self.STOCK_FILTERS,
        }

        url = f"{SCANNER_URL}/{market}/scan"

        json_data, error_msg = self._request(
            "POST",
            url,
            json_payload=payload,
        )

        if error_msg:
            return self._error_response(error_msg)

        assert json_data is not None

        items: list[dict[str, Any]] = json_data.get("data", [])
        total_count: int = json_data.get("totalCount", len(items))

        if not items:
            return self._error_response(f"No data found for market: {market}")

        # --- map rows --------------------------------------------------
        mapped = self._map_scanner_rows(items, used_fields)

        # --- export ----------------------------------------------------
        if self.export_result:
            self._export(
                data=mapped,
                symbol=f"{market}_top_stocks",
                data_category="markets",
            )

        return self._success_response(
            mapped,
            total=len(mapped),
            total_count=total_count,
        )
