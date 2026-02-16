"""Minds scraper for fetching community discussions from TradingView."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.exceptions import NetworkError, ValidationError

logger = logging.getLogger(__name__)

# TradingView Minds API endpoint
MINDS_API_URL = "https://www.tradingview.com/api/v1/minds/"


class Minds(BaseScraper):
    """Scraper for TradingView Minds community discussions.

    Fetches community-generated content including questions, discussions,
    trading ideas, and sentiment from TradingView's Minds feature.

    Args:
        export_result: Whether to export results to file.
        export_type: Export format, ``"json"`` or ``"csv"``.
        timeout: HTTP request timeout in seconds.

    Example::

        from tv_scraper.scrapers.social import Minds

        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")
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

    def get_minds(
        self,
        exchange: str,
        symbol: str,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get Minds discussions for a symbol with cursor-based pagination.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).
            limit: Maximum number of results to retrieve. If ``None``,
                fetches all available data across pages.

        Returns:
            Standardized response dict with keys
            ``status``, ``data``, ``metadata``, ``error``.
        """
        try:
            self.validator.validate_exchange(exchange)
            self.validator.validate_symbol(exchange, symbol)
        except ValidationError as exc:
            return self._error_response(str(exc))

        combined_symbol = f"{exchange.upper()}:{symbol.upper()}"

        parsed_data: List[Dict[str, Any]] = []
        next_cursor: Optional[str] = None
        pages = 0
        symbol_info: Dict[str, Any] = {}

        try:
            while True:
                params: Dict[str, str] = {"symbol": combined_symbol}
                if next_cursor:
                    params["c"] = next_cursor

                response = self._make_request(
                    MINDS_API_URL,
                    method="GET",
                    params=params,
                )

                if response.status_code != 200:
                    return self._error_response(
                        f"HTTP {response.status_code}: {response.text}"
                    )

                json_response = response.json()
                results = json_response.get("results", [])

                if not results:
                    break

                parsed = [self._parse_mind(item) for item in results]
                parsed_data.extend(parsed)
                pages += 1

                # Extract symbol info from first page
                if pages == 1:
                    meta = json_response.get("meta", {})
                    symbol_info = meta.get("symbols_info", {}).get(
                        combined_symbol, {}
                    )

                # Check if limit reached
                if limit is not None and len(parsed_data) >= limit:
                    break

                # Check for next page cursor
                next_url = json_response.get("next", "")
                if not next_url or "?c=" not in next_url:
                    break

                next_cursor = next_url.split("?c=")[1].split("&")[0]

        except Exception as exc:
            return self._error_response(f"Request failed: {exc}")

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

    def _parse_mind(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a single mind item from the API response.

        Args:
            item: Raw mind item dict from the TradingView API.

        Returns:
            Normalized mind dict with standardized keys.
            Excludes: symbols, modified, hidden, uid
        """
        # Parse author info
        author = item.get("author", {})
        author_data = {
            "username": author.get("username"),
            "profile_url": f"https://www.tradingview.com{author.get('uri', '')}",
            "is_broker": author.get("is_broker", False),
        }

        # Parse created date
        created = item.get("created", "")
        try:
            created_datetime = datetime.fromisoformat(
                created.replace("Z", "+00:00")
            )
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
