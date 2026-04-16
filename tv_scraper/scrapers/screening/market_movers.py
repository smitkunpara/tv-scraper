"""Market Movers module for scraping top gainers, losers, and active instruments."""

import logging
from typing import Any, Literal, get_args

from tv_scraper.core.base import catch_errors
from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.scanner import ScannerScraper
from tv_scraper.core.validation_data import LANGUAGES

MOVER_MARKET_LITERAL = Literal[
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
MOVER_CATEGORY_LITERAL = Literal[
    "gainers",
    "losers",
    "most-active",
    "penny-stocks",
    "pre-market-gainers",
    "pre-market-losers",
    "after-hours-gainers",
    "after-hours-losers",
]

SUPPORTED_MARKETS = list(get_args(MOVER_MARKET_LITERAL))
STOCK_CATEGORIES = list(get_args(MOVER_CATEGORY_LITERAL))


logger = logging.getLogger(__name__)


class MarketMovers(ScannerScraper):
    """Scrape market movers (gainers, losers, most active, etc.) from TradingView.

    Supports multiple stock markets, crypto, forex, bonds, and futures.
    Categories include gainers, losers, most-active, penny-stocks, and
    pre-market / after-hours variants.  Returns a standardized response
    envelope and never raises on user or network errors.

    Args:
        export: Export format, ``"json"`` or ``"csv"``.
            If ``None`` (default), results are not exported.
        timeout: HTTP request timeout in seconds.

    Example::

        movers = MarketMovers()
        result = movers.get_market_movers(market="stocks-usa", category="gainers", limit=20)
        for stock in result["data"]:
            print(f"{stock['symbol']}: {stock['change']}%")
    """

    SUPPORTED_MARKETS = SUPPORTED_MARKETS
    STOCK_CATEGORIES = STOCK_CATEGORIES

    # Non-stock markets accept any of the basic categories
    NON_STOCK_CATEGORIES: list[str] = [
        "gainers",
        "losers",
        "most-active",
    ]

    DEFAULT_STOCK_FIELDS: list[str] = [
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

    DEFAULT_CRYPTO_FIELDS: list[str] = [
        "name",
        "close",
        "change",
        "change_abs",
        "volume",
        "market_cap_calc",
        "logoid",
        "description",
    ]

    DEFAULT_FOREX_FIELDS: list[str] = [
        "name",
        "close",
        "change",
        "change_abs",
        "logoid",
        "description",
    ]

    DEFAULT_BASIC_FIELDS: list[str] = [
        "name",
        "close",
        "change",
        "change_abs",
        "logoid",
        "description",
    ]

    # Maps market identifier to scanner API path segment
    _MARKET_TO_SCANNER: dict[str, str] = {
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
    _CATEGORY_SORT: dict[str, dict[str, str]] = {
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

    def _get_default_fields(self, market: str) -> list[str]:
        """Return the default fields appropriate for the given market."""
        if market == "crypto":
            return list(self.DEFAULT_CRYPTO_FIELDS)
        if market == "forex":
            return list(self.DEFAULT_FOREX_FIELDS)
        if market in ("bonds", "futures"):
            return list(self.DEFAULT_BASIC_FIELDS)
        return list(self.DEFAULT_STOCK_FIELDS)

    def _get_sort_config(self, category: str) -> dict[str, str]:
        """Return sort configuration for the given category.

        Args:
            category: Category identifier (e.g. ``"gainers"``).

        Returns:
            Sort config dict with ``sortBy`` and ``sortOrder`` keys.
        """
        return self._CATEGORY_SORT.get(
            category, {"sortBy": "change", "sortOrder": "desc"}
        )

    def _get_filter_conditions(
        self, market: str, category: str
    ) -> list[dict[str, Any]]:
        """Build filter conditions for the scanner API.

        Args:
            market: Market identifier.
            category: Category identifier.

        Returns:
            List of filter condition dicts.
        """
        filters: list[dict[str, Any]] = []

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

    @catch_errors
    def get_market_movers(
        self,
        market: MOVER_MARKET_LITERAL = "stocks-usa",
        category: MOVER_CATEGORY_LITERAL = "gainers",
        fields: list[str] | None = None,
        limit: int = 50,
        language: str = "en",
    ) -> dict[str, Any]:
        """Scrape market movers data from TradingView.

        Args:
            market: The market to scrape (e.g. ``"stocks-usa"``, ``"crypto"``).
            category: Category of movers (e.g. ``"gainers"``, ``"losers"``).
            fields: Columns to retrieve. Defaults to ``DEFAULT_FIELDS``.
            limit: Maximum number of results (default 50, max 1000).
            language: Language code for the request (default: "en").

        Returns:
            Standardized response envelope with ``status``, ``data``,
            ``metadata``, and ``error`` keys.
        """
        # --- Validation ---
        self._validate_range(limit, 1, 1000)
        self._validate_choice(market, self.SUPPORTED_MARKETS)

        allowed_categories = (
            self.STOCK_CATEGORIES
            if market.startswith("stocks")
            else self.NON_STOCK_CATEGORIES
        )
        self._validate_choice(category, allowed_categories)
        self._validate_choice(language, set(LANGUAGES.values()))

        resolved_fields = (
            fields if fields is not None else self._get_default_fields(market)
        )
        if not isinstance(resolved_fields, list) or not all(
            isinstance(f, str) for f in resolved_fields
        ):
            from tv_scraper.core.exceptions import ValidationError

            raise ValidationError(
                "Invalid fields parameter: must be a list of strings."
            )

        payload = {
            "columns": resolved_fields,
            "filter": self._get_filter_conditions(market, category),
            "options": {"lang": language},
            "range": [0, limit],
            "sort": self._get_sort_config(category),
        }
        url = self._get_scanner_url(market)

        json_response, error_msg = self._request(
            "POST",
            url,
            json_payload=payload,
        )

        if error_msg:
            return self._error_response(error_msg)

        assert json_response is not None

        if not isinstance(json_response, dict):
            return self._error_response("Invalid response format: expected dictionary.")

        raw_items = json_response.get("data", [])
        total_count = json_response.get("totalCount", 0)
        formatted_data = self._map_scanner_rows(raw_items, resolved_fields)

        if self.export_result:
            self._export(
                data=formatted_data,
                symbol=f"{market}_{category}",
                data_category="market_movers",
            )

        return self._success_response(
            formatted_data,
            total=len(formatted_data),
            total_available=total_count,
        )
