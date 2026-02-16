"""Calendar scraper for dividend and earnings events."""

import datetime
import logging
from typing import Any, Dict, List, Optional

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.exceptions import NetworkError, ValidationError

logger = logging.getLogger(__name__)

# Default fields for dividend calendar (TradingView web defaults, Jan 2025)
DEFAULT_DIVIDEND_FIELDS: List[str] = [
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
DEFAULT_EARNINGS_FIELDS: List[str] = [
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


class Calendar(BaseScraper):
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

    def __init__(
        self,
        export_result: bool = False,
        export_type: str = "json",
        timeout: int = 10,
    ) -> None:
        super().__init__(
            export_result=export_result,
            export_type=export_type,
            timeout=timeout,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_dividends(
        self,
        timestamp_from: Optional[int] = None,
        timestamp_to: Optional[int] = None,
        markets: Optional[List[str]] = None,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
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
        )

    def get_earnings(
        self,
        timestamp_from: Optional[int] = None,
        timestamp_to: Optional[int] = None,
        markets: Optional[List[str]] = None,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
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
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_events(
        self,
        label: str,
        filter_left: str,
        default_fields: List[str],
        fields: Optional[List[str]],
        timestamp_from: Optional[int],
        timestamp_to: Optional[int],
        markets: Optional[List[str]],
        data_category: str,
    ) -> Dict[str, Any]:
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

        Returns:
            Standardized response envelope dict.
        """
        # Validate fields
        use_fields = default_fields
        if fields:
            try:
                self.validator.validate_fields(fields, default_fields, field_name="fields")
            except ValidationError as exc:
                return self._error_response(str(exc))
            use_fields = fields

        # Compute default timestamps (±3 days from midnight)
        if timestamp_from is None:
            now = datetime.datetime.now().timestamp()
            midnight = now - (now % _SECONDS_PER_DAY)
            timestamp_from = int(midnight - _DAYS_OFFSET * _SECONDS_PER_DAY)

        if timestamp_to is None:
            now = datetime.datetime.now().timestamp()
            midnight = now - (now % _SECONDS_PER_DAY)
            timestamp_to = int(midnight + _DAYS_OFFSET * _SECONDS_PER_DAY + _SECONDS_PER_DAY - 1)

        # Build payload
        url = f"{SCANNER_URL}/global/scan?label-product={label}"
        payload: Dict[str, Any] = {
            "columns": use_fields,
            "filter": [
                {
                    "left": filter_left,
                    "operation": "in_range",
                    "right": [timestamp_from, timestamp_to],
                }
            ],
            "ignore_unknown_fields": False,
            "options": {"lang": "en"},
        }

        if markets:
            payload["markets"] = markets

        # Execute request
        try:
            response = self._make_request(url, method="POST", json_data=payload)
            json_response: Dict[str, Any] = response.json()
        except NetworkError as exc:
            return self._error_response(str(exc))
        except (ValueError, KeyError) as exc:
            return self._error_response(f"Failed to parse API response: {exc}")

        # Parse events
        data_items: List[Dict[str, Any]] = json_response.get("data", [])
        events = self._map_scanner_rows(data_items, use_fields)

        # Export if enabled
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
        )
