"""Market Movers module for scraping top gainers, losers, and active instruments."""

import logging
from typing import Any, Dict, List, Optional

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.exceptions import NetworkError

logger = logging.getLogger(__name__)


class MarketMovers(BaseScraper):
    """Scrape market movers (gainers, losers, most active, etc.) from TradingView.

    Supports multiple stock markets, crypto, forex, bonds, and futures.
    Categories include gainers, losers, most-active, penny-stocks, and
    pre-market / after-hours variants.  Returns a standardized response
    envelope and never raises on user or network errors.

    Args:
        export_result: Whether to export results to file.
        export_type: Export format, ``"json"`` or ``"csv"``.
        timeout: HTTP request timeout in seconds.

    Example::

        movers = MarketMovers()
        result = movers.scrape(market="stocks-usa", category="gainers", limit=20)
        for stock in result["data"]:
            print(f"{stock['symbol']}: {stock['change']}%")
    """

    SUPPORTED_MARKETS: list[str] = [
        "stocks-usa",
        "stocks-uk",
        "stocks-india",
        "stocks-australia",
        "stocks-canada",
        "crypto",
        "forex",
        "bonds",
        "futures",
    ]

    STOCK_CATEGORIES: list[str] = [
        "gainers",
        "losers",
        "most-active",
        "penny-stocks",
        "pre-market-gainers",
        "pre-market-losers",
        "after-hours-gainers",
        "after-hours-losers",
    ]

    # Non-stock markets accept any of the basic categories
    NON_STOCK_CATEGORIES: list[str] = [
        "gainers",
        "losers",
        "most-active",
    ]

    DEFAULT_FIELDS: list[str] = [
        "name",
        "close",
        "change",
        "change_abs",
        "volume",
        "market_cap_basic",
        "price_earnings_ttm",
        "earnings_per_share_basic_ttm",
        "logoid",
        "description",
    ]

    # Maps market identifier to scanner API path segment
    _MARKET_TO_SCANNER: Dict[str, str] = {
        "stocks-usa": "america",
        "stocks-uk": "uk",
        "stocks-india": "india",
        "stocks-australia": "australia",
        "stocks-canada": "canada",
        "crypto": "crypto",
        "forex": "forex",
        "bonds": "bonds",
        "futures": "futures",
    }

    # Sort configuration per category
    _CATEGORY_SORT: Dict[str, Dict[str, str]] = {
        "gainers": {"sortBy": "change", "sortOrder": "desc"},
        "losers": {"sortBy": "change", "sortOrder": "asc"},
        "most-active": {"sortBy": "volume", "sortOrder": "desc"},
        "penny-stocks": {"sortBy": "volume", "sortOrder": "desc"},
        "pre-market-gainers": {"sortBy": "change", "sortOrder": "desc"},
        "pre-market-losers": {"sortBy": "change", "sortOrder": "asc"},
        "after-hours-gainers": {"sortBy": "change", "sortOrder": "desc"},
        "after-hours-losers": {"sortBy": "change", "sortOrder": "asc"},
    }

    def _get_scanner_url(self, market: str) -> str:
        """Return the scanner API URL for the given market.

        Args:
            market: Market identifier (e.g. ``"stocks-usa"``).

        Returns:
            Full scanner URL.
        """
        segment = self._MARKET_TO_SCANNER.get(market, "america")
        return f"{SCANNER_URL}/{segment}/scan"

    def _get_sort_config(self, category: str) -> Dict[str, str]:
        """Return sort configuration for the given category.

        Args:
            category: Category identifier (e.g. ``"gainers"``).

        Returns:
            Sort config dict with ``sortBy`` and ``sortOrder`` keys.
        """
        return dict(
            self._CATEGORY_SORT.get(
                category, {"sortBy": "change", "sortOrder": "desc"}
            )
        )

    def _get_filter_conditions(
        self, market: str, category: str
    ) -> List[Dict[str, Any]]:
        """Build filter conditions for the scanner API.

        Args:
            market: Market identifier.
            category: Category identifier.

        Returns:
            List of filter condition dicts.
        """
        filters: List[Dict[str, Any]] = []

        # Market filter for stock markets
        scanner_segment = self._MARKET_TO_SCANNER.get(market)
        if market.startswith("stocks") and scanner_segment:
            filters.append(
                {"left": "market", "operation": "equal", "right": scanner_segment}
            )

        # Category-specific filters
        if category == "penny-stocks":
            filters.append({"left": "close", "operation": "less", "right": 5})
        elif category in (
            "gainers",
            "pre-market-gainers",
            "after-hours-gainers",
        ):
            filters.append({"left": "change", "operation": "greater", "right": 0})
        elif category in (
            "losers",
            "pre-market-losers",
            "after-hours-losers",
        ):
            filters.append({"left": "change", "operation": "less", "right": 0})

        return filters

    def _build_payload(
        self,
        market: str,
        category: str,
        fields: List[str],
        limit: int,
    ) -> Dict[str, Any]:
        """Build the scanner API request payload.

        Args:
            market: Market identifier.
            category: Category identifier.
            fields: Columns to retrieve.
            limit: Maximum number of results.

        Returns:
            Payload dict ready for JSON serialization.
        """
        return {
            "columns": fields,
            "filter": self._get_filter_conditions(market, category),
            "options": {"lang": "en"},
            "range": [0, limit],
            "sort": self._get_sort_config(category),
        }

    def scrape(
        self,
        market: str = "stocks-usa",
        category: str = "gainers",
        fields: Optional[List[str]] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Scrape market movers data from TradingView.

        Args:
            market: The market to scrape (e.g. ``"stocks-usa"``, ``"crypto"``).
            category: Category of movers (e.g. ``"gainers"``, ``"losers"``).
            fields: Columns to retrieve. Defaults to ``DEFAULT_FIELDS``.
            limit: Maximum number of results (default 50).

        Returns:
            Standardized response envelope with ``status``, ``data``,
            ``metadata``, and ``error`` keys.
        """
        # Validate market
        if market not in self.SUPPORTED_MARKETS:
            return self._error_response(
                f"Unsupported market: '{market}'. "
                f"Supported markets: {', '.join(self.SUPPORTED_MARKETS)}"
            )

        # Validate category
        allowed = (
            self.STOCK_CATEGORIES
            if market.startswith("stocks")
            else self.NON_STOCK_CATEGORIES
        )
        if category not in allowed:
            return self._error_response(
                f"Unsupported category: '{category}'. "
                f"Supported categories: {', '.join(allowed)}"
            )

        resolved_fields = fields if fields is not None else list(self.DEFAULT_FIELDS)
        payload = self._build_payload(market, category, resolved_fields, limit)
        url = self._get_scanner_url(market)

        try:
            response = self._make_request(url, method="POST", json_data=payload)
            json_response = response.json()

            raw_items = json_response.get("data", [])
            formatted_data = self._map_scanner_rows(raw_items, resolved_fields)

            if self.export_result:
                self._export(
                    data=formatted_data,
                    symbol=f"{market}_{category}",
                    data_category="market_movers",
                )

            return self._success_response(
                formatted_data,
                market=market,
                category=category,
                total=len(formatted_data),
            )
        except NetworkError as exc:
            return self._error_response(str(exc))
        except Exception as exc:
            return self._error_response(f"Request failed: {exc}")
