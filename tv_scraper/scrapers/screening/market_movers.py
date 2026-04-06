"""Market Movers module for scraping top gainers, losers, and active instruments."""

import logging
from typing import Any, Literal

from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.scanner import ScannerScraper
from tv_scraper.core.validators import DataValidator

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

logger = logging.getLogger(__name__)


class MarketMovers(ScannerScraper):
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
        result = movers.get_market_movers(market="stocks-usa", category="gainers", limit=20)
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

    def _build_payload(
        self,
        market: str,
        category: str,
        fields: list[str],
        limit: int,
        language: str = "en",
    ) -> dict[str, Any]:
        """Build the scanner API request payload.

        Args:
            market: Market identifier.
            category: Category identifier.
            fields: Columns to retrieve.
            limit: Maximum number of results.
            language: Language code for the request (default: "en").

        Returns:
            Payload dict ready for JSON serialization.
        """
        return {
            "columns": fields,
            "filter": self._get_filter_conditions(market, category),
            "options": {"lang": language},
            "range": [0, limit],
            "sort": self._get_sort_config(category),
        }

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
        # Validate limit bounds
        if not isinstance(limit, int) or limit < 1 or limit > 1000:
            return self._error_response(
                f"Invalid limit: {limit}. Must be an integer between 1 and 1000.",
                market=market,
                category=category,
                limit=limit,
            )

        # Validate market
        if market not in self.SUPPORTED_MARKETS:
            return self._error_response(
                f"Unsupported market: '{market}'. "
                f"Supported markets: {', '.join(self.SUPPORTED_MARKETS)}",
                market=market,
                category=category,
                limit=limit,
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
                f"Supported categories: {', '.join(allowed)}",
                market=market,
                category=category,
                limit=limit,
            )

        # Validate language
        valid_languages = DataValidator().get_languages()
        valid_language_codes = set(valid_languages.values())
        if language not in valid_language_codes:
            return self._error_response(
                f"Unsupported language: '{language}'. "
                f"Supported language codes: {', '.join(sorted(valid_language_codes))}",
                market=market,
                category=category,
                limit=limit,
            )

        resolved_fields = (
            fields if fields is not None else self._get_default_fields(market)
        )

        # Validate fields
        if not isinstance(resolved_fields, list) or not all(
            isinstance(f, str) for f in resolved_fields
        ):
            return self._error_response(
                "Invalid fields parameter. Must be a list of strings.",
                market=market,
                category=category,
                limit=limit,
            )

        payload = self._build_payload(
            market, category, resolved_fields, limit, language
        )
        url = self._get_scanner_url(market)

        json_response, error_msg = self._request(
            "POST",
            url,
            json_payload=payload,
        )

        if error_msg:
            return self._error_response(
                error_msg,
                market=market,
                category=category,
                limit=limit,
            )

        assert json_response is not None

        # Validate JSON response structure
        if not isinstance(json_response, dict):
            return self._error_response(
                f"Invalid response format: expected dict, got {type(json_response).__name__}",
                market=market,
                category=category,
                limit=limit,
            )

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
            market=market,
            category=category,
            limit=limit,
            total=len(formatted_data),
            totalCount=total_count,
        )
