"""Minds scraper for fetching community discussions from TradingView."""

import logging
from datetime import datetime
from typing import Any

from tv_scraper.core import validators
from tv_scraper.core.base import BaseScraper, catch_errors
from tv_scraper.core.validation_data import EXCHANGE_LITERAL

logger = logging.getLogger(__name__)

# TradingView Minds API endpoint
MINDS_API_URL = "https://www.tradingview.com/api/v1/minds/"

# Maximum pages to fetch to prevent infinite loops
MAX_PAGES = 100


class Minds(BaseScraper):
    """Scraper for TradingView Minds community discussions.

    Fetches community-generated content including questions, discussions,
    trading ideas, and sentiment from TradingView's Minds feature.

    Args:
        export: Export format, ``"json"`` or ``"csv"``.
            If ``None`` (default), results are not exported.
        timeout: HTTP request timeout in seconds.
        cookie: Optional TradingView session cookie. If omitted,
            uses ``TRADINGVIEW_COOKIE`` from the environment when available.

    Example::

        from tv_scraper.scrapers.social import Minds

        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")
    """

    @catch_errors
    def get_minds(
        self,
        exchange: EXCHANGE_LITERAL,
        symbol: str,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Get Minds discussions for a symbol with cursor-based pagination.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).
            limit: Optional limit for the returned list. When provided and
                the collected list is longer than ``limit``, the final result
                is truncated via ``parsed_data[:limit]``.

        Returns:
            Standardized response dict with keys
            ``status``, ``data``, ``metadata``, ``error``.
        """
        # --- Validation ---
        validators.verify_symbol_exchange(exchange, symbol)

        combined_symbol = f"{exchange}:{symbol}"

        parsed_data: list[dict[str, Any]] = []
        next_cursor: str | None = None
        pages = 0
        symbol_info: dict[str, Any] = {}

        while True:
            if pages >= MAX_PAGES:
                logger.warning(
                    "Max pages (%d) reached for %s:%s", MAX_PAGES, exchange, symbol
                )
                break

            params: dict[str, str] = {"symbol": combined_symbol}
            if next_cursor:
                params["c"] = next_cursor

            json_response, error_msg = self._request(
                "GET", MINDS_API_URL, params=params
            )

            if error_msg:
                logger.error("Error for %s:%s - %s", exchange, symbol, error_msg)
                return self._error_response(error_msg)

            assert json_response is not None

            results = json_response.get("results", [])

            if not results:
                if pages == 0:
                    meta_dict = json_response.get("meta", {})
                    symbol_info = meta_dict.get("symbols_info", {}).get(
                        combined_symbol, {}
                    )
                break

            parsed = [self._parse_mind(item) for item in results]
            parsed_data.extend(parsed)
            pages += 1

            if pages == 1:
                meta_dict = json_response.get("meta", {})
                symbol_info = meta_dict.get("symbols_info", {}).get(combined_symbol, {})

            # Check for next page cursor
            next_url = json_response.get("next", "")
            if not next_url or "?c=" not in next_url:
                break

            cursor_part = next_url.split("?c=")[1].split("&")[0]
            if not cursor_part:
                break
            next_cursor = cursor_part

        # Apply limit
        if limit is not None and len(parsed_data) > limit:
            parsed_data = parsed_data[:limit]

        # Export if requested
        if self.export_result and parsed_data:
            self._export(
                data=parsed_data,
                symbol=f"{exchange}_{symbol}",
                data_category="minds",
            )

        return self._success_response(
            parsed_data,
            total=len(parsed_data),
            pages=pages,
            symbol_info=symbol_info,
        )

    def _parse_mind(self, item: dict[str, Any]) -> dict[str, Any]:
        """Parse a single mind item from the API response.

        Args:
            item: Raw mind item dict from the TradingView API.

        Returns:
            Normalized mind dict with standardized keys.
            Excludes: symbols, modified, hidden, uid
        """
        # Parse author info
        author = item.get("author", {})
        uri = author.get("uri", "")
        if uri and not uri.startswith("http"):
            uri = f"https://www.tradingview.com{uri}"
        author_data = {
            "username": author.get("username"),
            "profile_url": uri,
            "is_broker": author.get("is_broker", False),
        }

        # Parse created date
        created = item.get("created", "")
        try:
            created_datetime = datetime.fromisoformat(created.replace("Z", "+00:00"))
            created_formatted = created_datetime.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError):
            created_formatted = created

        return {
            "text": item.get("text", ""),
            "url": item.get("url", ""),
            "author": author_data,
            "created": created_formatted,
            "total_likes": item.get("total_likes", 0),
            "total_comments": item.get("total_comments", 0),
        }
