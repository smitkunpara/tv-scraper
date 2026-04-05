"""Minds scraper for fetching community discussions from TradingView."""

import logging
from datetime import datetime
from typing import Any

import requests

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.exceptions import ValidationError

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
        export_result: Whether to export results to file.
        export_type: Export format, ``"json"`` or ``"csv"``.
        timeout: HTTP request timeout in seconds.

    Example::

        from tv_scraper.scrapers.social import Minds

        scraper = Minds()
        result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")
    """

    def get_minds(  # noqa: PLR0915
        self,
        exchange: str,
        symbol: str,
        limit: int | None = None,
    ) -> dict[str, Any]:
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
            self.validator.verify_symbol_exchange(exchange, symbol)
        except ValidationError as exc:
            return self._error_response(
                str(exc),
                exchange=exchange,
                symbol=symbol,
            )

        combined_symbol = f"{exchange.upper()}:{symbol.upper()}"

        parsed_data: list[dict[str, Any]] = []
        next_cursor: str | None = None
        pages = 0
        symbol_info: dict[str, Any] = {}

        try:
            while True:
                if pages >= MAX_PAGES:
                    logger.warning(
                        "Max pages (%d) reached for %s:%s", MAX_PAGES, exchange, symbol
                    )
                    break

                params: dict[str, str] = {"symbol": combined_symbol}
                if next_cursor:
                    params["c"] = next_cursor

                response = requests.get(
                    MINDS_API_URL,
                    headers=self._headers,
                    params=params,
                    timeout=self.timeout,
                )

                response.raise_for_status()

                if response.status_code != 200:
                    logger.error(
                        "HTTP error for %s:%s - Status: %d",
                        exchange,
                        symbol,
                        response.status_code,
                    )
                    return self._error_response(
                        f"HTTP {response.status_code}: {response.text}",
                        exchange=exchange,
                        symbol=symbol,
                    )

                if "<title>Captcha Challenge</title>" in response.text:
                    logger.error("Captcha detected for %s:%s", exchange, symbol)
                    return self._error_response(
                        "Captcha challenge encountered. Try again later.",
                        exchange=exchange,
                        symbol=symbol,
                    )

                try:
                    json_response = response.json()
                except ValueError as exc:
                    logger.error(
                        "JSON parsing error for %s:%s: %s", exchange, symbol, exc
                    )
                    return self._error_response(
                        f"Failed to parse JSON response: {exc}",
                        exchange=exchange,
                        symbol=symbol,
                    )

                results = json_response.get("results", [])

                if not results:
                    break

                parsed = [self._parse_mind(item) for item in results]
                parsed_data.extend(parsed)
                pages += 1

                # Extract symbol info from first page
                if pages == 1:
                    meta = json_response.get("meta", {})
                    symbol_info = meta.get("symbols_info", {}).get(combined_symbol, {})

                # Check for next page cursor
                next_url = json_response.get("next", "")
                if not next_url or "?c=" not in next_url:
                    break

                cursor_part = next_url.split("?c=")[1].split("&")[0]
                if not cursor_part:
                    break
                next_cursor = cursor_part

        except requests.HTTPError as exc:
            logger.error("HTTP error for %s:%s: %s", exchange, symbol, exc)
            return self._error_response(
                f"HTTP error: {exc}",
                exchange=exchange,
                symbol=symbol,
            )
        except requests.RequestException as exc:
            logger.error("Request failed for %s:%s: %s", exchange, symbol, exc)
            return self._error_response(
                f"Request failed: {exc}",
                exchange=exchange,
                symbol=symbol,
            )
        except Exception as exc:
            logger.error("Unexpected error for %s:%s: %s", exchange, symbol, exc)
            return self._error_response(
                f"Unexpected error: {exc}",
                exchange=exchange,
                symbol=symbol,
            )

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

        meta: dict[str, Any] = {
            "exchange": exchange,
            "symbol": symbol,
            "total": len(parsed_data),
            "pages": pages,
            "symbol_info": symbol_info,
        }
        if limit is not None:
            meta["limit"] = limit

        return self._success_response(
            parsed_data,
            **meta,
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
