"""Markets scraper for retrieving top stocks by various criteria.

Queries the TradingView scanner API to fetch ranked stock lists
across supported markets, sorted by market cap, volume, change, etc.
"""

from typing import Any, Dict, List, Optional

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import SCANNER_URL


class Markets(BaseScraper):
    """Scraper for market-wide stock rankings.

    Fetches top stocks from the TradingView scanner API, optionally
    filtered by market region and sorted by a chosen criterion.

    Args:
        export_result: Whether to export results to file.
        export_type: Export format, ``"json"`` or ``"csv"``.
        timeout: HTTP request timeout in seconds.

    Example::

        markets = Markets()
        result = markets.get_top_stocks(market="america", sort_by="market_cap", limit=20)
        for stock in result["data"]:
            print(stock["symbol"], stock["close"])
    """

    VALID_MARKETS: List[str] = [
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

    SORT_CRITERIA: Dict[str, str] = {
        "market_cap": "market_cap_basic",
        "volume": "volume",
        "change": "change",
        "price": "close",
        "volatility": "Volatility.D",
    }

    DEFAULT_FIELDS: List[str] = [
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

    STOCK_FILTERS: List[Dict[str, str]] = [
        {"left": "type", "operation": "equal", "right": "stock"},
        {"left": "market_cap_basic", "operation": "nempty"},
    ]

    def get_top_stocks(
        self,
        market: str = "america",
        sort_by: str = "market_cap",
        fields: Optional[List[str]] = None,
        sort_order: str = "desc",
        limit: int = 50,
    ) -> Dict[str, Any]:
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
        # --- validation ------------------------------------------------
        if market not in self.VALID_MARKETS:
            return self._error_response(
                f"Unsupported market: '{market}'. "
                f"Valid markets: {', '.join(self.VALID_MARKETS)}"
            )

        if sort_by not in self.SORT_CRITERIA:
            return self._error_response(
                f"Unsupported sort criterion: '{sort_by}'. "
                f"Valid sort criteria: {', '.join(self.SORT_CRITERIA.keys())}"
            )

        # --- build payload ---------------------------------------------
        used_fields = fields if fields is not None else self.DEFAULT_FIELDS
        sort_field = self.SORT_CRITERIA[sort_by]

        payload: Dict[str, Any] = {
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

        # --- request ---------------------------------------------------
        try:
            response = self._make_request(url, method="POST", json_data=payload)
            json_data = response.json()
        except Exception as exc:
            return self._error_response(str(exc))

        items: List[Dict[str, Any]] = json_data.get("data", [])
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
            market=market,
            sort_by=sort_by,
            total=len(mapped),
            total_count=total_count,
        )
