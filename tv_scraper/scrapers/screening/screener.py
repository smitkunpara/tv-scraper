import logging
from typing import Any, Literal, get_args

from tv_scraper.core.base import catch_errors
from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.exceptions import ValidationError
from tv_scraper.core.scanner import ScannerScraper
from tv_scraper.core.validation_data import SORT_ORDER_LITERAL

SCREENER_MARKET_LITERAL = Literal[
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
]
SCREENER_OPERATION_LITERAL = Literal[
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
    "in_day_range",
    "not_in_day_range",
    "match",
    "nmatch",
    "empty",
    "nempty",
    "smatch",
    "above%",
    "below%",
    "in_range%",
    "in_week_range",
    "in_month_range",
    "in_year_range",
]

SCREENER_MARKET_LIST = list(get_args(SCREENER_MARKET_LITERAL))
SCREENER_OPERATION_LIST = list(get_args(SCREENER_OPERATION_LITERAL))
SORT_ORDERS = frozenset(get_args(SORT_ORDER_LITERAL))

logger = logging.getLogger(__name__)

MIN_LIMIT = 1
MAX_LIMIT = 10000


class Screener(ScannerScraper):
    """Screen financial instruments across markets with custom filters.

    Supports stocks, crypto, forex, bonds, futures, and CFDs via the
    TradingView scanner API.  Returns a standardized response envelope
    and never raises on user/network errors.

    Args:
        export: Export format, ``"json"`` or ``"csv"``.
            If ``None`` (default), results are not exported.
        timeout: HTTP request timeout in seconds.

    Example::

        screener = Screener()
        result = screener.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "greater", "right": 100}],
            fields=["name", "close", "volume", "market_cap_basic"],
        )
    """

    SUPPORTED_MARKETS = set(SCREENER_MARKET_LIST)
    OPERATIONS = frozenset(SCREENER_OPERATION_LIST)

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

    def _validate_filter(self, filters: list[dict[str, Any]]) -> None:
        """Validate filter structure.

        Args:
            filters: List of filter dicts to validate.

        Raises:
            ValidationError: If validation fails.
        """
        for i, f in enumerate(filters):
            if not isinstance(f, dict):
                raise ValidationError(f"Filter at index {i} must be a dictionary")
            if "left" not in f:
                raise ValidationError(
                    f"Filter at index {i} missing required 'left' key"
                )
            if "operation" not in f:
                raise ValidationError(
                    f"Filter at index {i} missing required 'operation' key"
                )
            if f["operation"] not in self.OPERATIONS:
                raise ValidationError(
                    f"Invalid operation '{f['operation']}' in filter at index {i}. "
                    f"Valid operations: {', '.join(sorted(self.OPERATIONS))}"
                )

    def _validate_filter2(self, filter2: dict[str, Any]) -> None:
        """Validate filter2 structure.

        Args:
            filter2: Filter2 dict to validate.

        Raises:
            ValidationError: If validation fails.
        """
        if not isinstance(filter2, dict):
            raise ValidationError("filter2 must be a dictionary")
        if "operator" not in filter2:
            raise ValidationError("filter2 missing required 'operator' key")

    @catch_errors
    def get_screener(
        self,
        market: SCREENER_MARKET_LITERAL = "america",
        filters: list[dict[str, Any]] | None = None,
        fields: list[str] | None = None,
        sort_by: str | None = None,
        sort_order: SORT_ORDER_LITERAL = "desc",
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
        # --- Validation ---
        self._validate_choice(market, SCREENER_MARKET_LIST)
        self._validate_choice(sort_order, SORT_ORDERS)
        self._validate_range(limit, MIN_LIMIT, MAX_LIMIT)

        if filters is not None:
            self._validate_filter(filters)

        if filter2 is not None:
            self._validate_filter2(filter2)

        resolved_fields = (
            fields if fields is not None else self._get_default_fields(market)
        )

        payload: dict[str, Any] = {
            "columns": resolved_fields,
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

        url = f"{SCANNER_URL}/{market}/scan"

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

        total_count = json_response.get("totalCount", len(formatted_data))

        if self.export_result:
            self._export(
                data=formatted_data,
                symbol=f"{market}_screener",
                data_category="screener",
            )

        return self._success_response(
            formatted_data,
            total=len(formatted_data),
            total_available=total_count,
        )
