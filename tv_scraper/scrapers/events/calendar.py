"""Calendar scraper for dividend and earnings events."""

import datetime
import logging
from typing import Any, Literal

from tv_scraper.core import validators
from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.exceptions import ValidationError
from tv_scraper.core.scanner import ScannerScraper

logger = logging.getLogger(__name__)

# Default fields for dividend calendar (TradingView web defaults, Jan 2025)
DEFAULT_DIVIDEND_FIELDS: list[str] = [
    "dividend_ex_date_recent",
    "dividend_ex_date_upcoming",
    "logoid",
    "name",
    "description",
    "dividends_yield",
    "dividend_payment_date_recent",
    "dividend_payment_date_upcoming",
    "dividend_amount_recent",
    "dividend_amount_upcoming",
    "fundamental_currency_code",
    "market",
]

# Default fields for earnings calendar (TradingView web defaults, Jan 2025)
DEFAULT_EARNINGS_FIELDS: list[str] = [
    "earnings_release_next_date",
    "earnings_release_date",
    "logoid",
    "name",
    "description",
    "earnings_per_share_fq",
    "earnings_per_share_forecast_next_fq",
    "eps_surprise_fq",
    "eps_surprise_percent_fq",
    "revenue_fq",
    "revenue_forecast_next_fq",
    "market_cap_basic",
    "earnings_release_time",
    "earnings_release_next_time",
    "earnings_per_share_forecast_fq",
    "revenue_forecast_fq",
    "fundamental_currency_code",
    "market",
    "earnings_publication_type_fq",
    "earnings_publication_type_next_fq",
    "revenue_surprise_fq",
    "revenue_surprise_percent_fq",
]

_DAYS_OFFSET: int = 3
_SECONDS_PER_DAY: int = 86400


class Calendar(ScannerScraper):
    """Scraper for dividend and earnings events from TradingView calendar.

    Fetches calendar events via the TradingView scanner API and returns
    standardized response envelopes.

    Args:
        export_result: Whether to export results to file.
        export_type: Export format, ``"json"`` or ``"csv"``.
        timeout: HTTP request timeout in seconds.

    Example::

        from tv_scraper.scrapers.events import Calendar

        cal = Calendar()
        dividends = cal.get_dividends(markets=["america"])
        earnings = cal.get_earnings(
            fields=["logoid", "name", "earnings_per_share_fq"],
        )
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_dividends(
        self,
        timestamp_from: int | None = None,
        timestamp_to: int | None = None,
        markets: list[str] | None = None,
        fields: list[str] | None = None,
        lang: str = "en",
    ) -> dict[str, Any]:
        """Fetch dividend events from the TradingView calendar.

        Args:
            timestamp_from: Start of the date range (Unix timestamp).
                Defaults to current midnight minus 3 days.
            timestamp_to: End of the date range (Unix timestamp).
                Defaults to current midnight plus 3 days + 86399s.
            markets: List of market names to filter
                (e.g. ``["america", "uk"]``).
            fields: Specific fields to fetch. Validated against the
                known dividend field list. Defaults to all dividend fields.
            lang: Language code for API responses (default: "en").

        Returns:
            Standardized response dict with ``status``, ``data``,
            ``metadata``, and ``error`` keys.
        """
        return self._fetch_events(
            label="calendar-dividends",
            filter_left="dividend_ex_date_recent,dividend_ex_date_upcoming",
            default_fields=DEFAULT_DIVIDEND_FIELDS,
            fields=fields,
            timestamp_from=timestamp_from,
            timestamp_to=timestamp_to,
            markets=markets,
            data_category="dividends",
            lang=lang,
        )

    def get_earnings(
        self,
        timestamp_from: int | None = None,
        timestamp_to: int | None = None,
        markets: list[str] | None = None,
        fields: list[str] | None = None,
        lang: str = "en",
    ) -> dict[str, Any]:
        """Fetch earnings events from the TradingView calendar.

        Args:
            timestamp_from: Start of the date range (Unix timestamp).
                Defaults to current midnight minus 3 days.
            timestamp_to: End of the date range (Unix timestamp).
                Defaults to current midnight plus 3 days + 86399s.
            markets: List of market names to filter
                (e.g. ``["america", "uk"]``).
            fields: Specific fields to fetch. Validated against the
                known earnings field list. Defaults to all earnings fields.
            lang: Language code for API responses (default: "en").

        Returns:
            Standardized response dict with ``status``, ``data``,
            ``metadata``, and ``error`` keys.
        """
        return self._fetch_events(
            label="calendar-earnings",
            filter_left="earnings_release_date,earnings_release_next_date",
            default_fields=DEFAULT_EARNINGS_FIELDS,
            fields=fields,
            timestamp_from=timestamp_from,
            timestamp_to=timestamp_to,
            markets=markets,
            data_category="earnings",
            lang=lang,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_events(
        self,
        label: str,
        filter_left: str,
        default_fields: list[str],
        fields: list[str] | None,
        timestamp_from: int | None,
        timestamp_to: int | None,
        markets: list[str] | None,
        data_category: Literal["dividends", "earnings"],
        lang: str = "en",
    ) -> dict[str, Any]:
        """Shared implementation for fetching calendar events.

        Args:
            label: TradingView label-product query parameter.
            filter_left: Column names for date range filtering.
            default_fields: Default field list for this event type.
            fields: User-specified fields (validated against defaults).
            timestamp_from: Start timestamp or ``None`` for default.
            timestamp_to: End timestamp or ``None`` for default.
            markets: Optional market filter.
            data_category: Category name for export filenames.
            lang: Language code for API responses (default: "en").

        Returns:
            Standardized response envelope dict.
        """
        use_fields = default_fields
        if fields:
            try:
                validators.validate_fields(fields, default_fields, field_name="fields")
            except ValidationError as exc:
                return self._error_response(
                    str(exc),
                    event_type=data_category,
                )
            use_fields = fields

        if timestamp_from is None or timestamp_to is None:
            now = datetime.datetime.now().timestamp()
            midnight = now - (now % _SECONDS_PER_DAY)

        if timestamp_from is None:
            timestamp_from = int(midnight - _DAYS_OFFSET * _SECONDS_PER_DAY)

        if timestamp_to is None:
            timestamp_to = int(
                midnight + _DAYS_OFFSET * _SECONDS_PER_DAY + _SECONDS_PER_DAY - 1
            )

        url = f"{SCANNER_URL}/global/scan?label-product={label}"
        payload: dict[str, Any] = {
            "columns": use_fields,
            "filter": [
                {
                    "left": filter_left,
                    "operation": "in_range",
                    "right": [timestamp_from, timestamp_to],
                }
            ],
            "ignore_unknown_fields": False,
            "options": {"lang": lang},
        }

        if markets:
            payload["markets"] = markets

        json_response, error_msg = self._request(
            "POST",
            url,
            json_payload=payload,
        )

        if error_msg:
            return self._error_response(error_msg, event_type=data_category)

        assert json_response is not None

        data_items: list[dict[str, Any]] = json_response.get("data", [])
        if not isinstance(data_items, list):
            data_items = []
            logger.warning("API response 'data' field is not a list")

        if not data_items:
            logger.info("No %s events found in the specified date range", data_category)

        events = self._map_scanner_rows(data_items, use_fields)

        if self.export_result:
            self._export(
                data=events,
                symbol=data_category,
                data_category="calendar",
            )

        return self._success_response(
            events,
            event_type=data_category,
            total=len(events),
            timestamp_from=timestamp_from,
            timestamp_to=timestamp_to,
            **{"markets": markets} if markets else {},
        )
