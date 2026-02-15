"""Ideas scraper for fetching trading ideas from TradingView."""

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import JSONDecodeError, RequestException

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import BASE_URL
from tv_scraper.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

ALLOWED_SORT_VALUES = {"popular", "recent"}


class Ideas(BaseScraper):
    """Scraper for trading ideas published on TradingView.

    Fetches user-published ideas for a given symbol, with support for
    pagination, sorting, concurrent page scraping, and optional cookie
    authentication for captcha bypass.

    Args:
        export_result: Whether to export results to file.
        export_type: Export format, ``"json"`` or ``"csv"``.
        timeout: HTTP request timeout in seconds.
        cookie: TradingView session cookie string. Falls back to
            ``TRADINGVIEW_COOKIE`` environment variable if not provided.

    Example::

        from tv_scraper.scrapers.social import Ideas

        scraper = Ideas()
        result = scraper.scrape(exchange="CRYPTO", symbol="BTCUSD")
    """

    def __init__(
        self,
        export_result: bool = False,
        export_type: str = "json",
        timeout: int = 10,
        cookie: Optional[str] = None,
    ) -> None:
        super().__init__(
            export_result=export_result,
            export_type=export_type,
            timeout=timeout,
        )
        self._cookie: Optional[str] = cookie or os.environ.get("TRADINGVIEW_COOKIE")

    def scrape(
        self,
        exchange: str,
        symbol: str,
        start_page: int = 1,
        end_page: int = 1,
        sort_by: str = "popular",
    ) -> Dict[str, Any]:
        """Scrape trading ideas for a symbol across one or more pages.

        Args:
            exchange: Exchange name (e.g. ``"CRYPTO"``). Used for metadata
                only; the ideas URL uses the symbol slug directly.
            symbol: Trading symbol (e.g. ``"BTCUSD"``).
            start_page: First page to scrape (1-based).
            end_page: Last page to scrape (inclusive).
            sort_by: Sorting criteria — ``"popular"`` or ``"recent"``.

        Returns:
            Standardized response dict with keys
            ``status``, ``data``, ``metadata``, ``error``.
        """
        # --- Validation ---
        try:
            self.validator.validate_symbol(exchange, symbol)
            self.validator.validate_choice("sort_by", sort_by, ALLOWED_SORT_VALUES)
        except ValidationError as exc:
            return self._error_response(str(exc))

        # Apply cookie header if available
        headers = dict(self._headers)
        if self._cookie:
            headers["cookie"] = self._cookie

        page_list = list(range(start_page, end_page + 1))
        articles: List[Dict[str, Any]] = []

        # --- Concurrent page scraping ---
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self._scrape_page, symbol, page, sort_by, headers): page
                for page in page_list
            }
            for future in as_completed(futures):
                page = futures[future]
                try:
                    result = future.result()
                    if result is None:
                        # Captcha or fatal page error — abort
                        return self._error_response(
                            f"Captcha challenge encountered on page {page}. "
                            "Try updating the TRADINGVIEW_COOKIE.",
                        )
                    articles.extend(result)
                except Exception as exc:
                    logger.error("Failed to scrape page %d: %s", page, exc)
                    return self._error_response(
                        f"Failed to scrape page {page}: {exc}",
                    )

        # --- Export ---
        if self.export_result:
            self._export(
                data=articles,
                symbol=f"{exchange}_{symbol}" if exchange else symbol,
                data_category="ideas",
            )

        return self._success_response(
            articles,
            exchange=exchange,
            symbol=symbol,
            total=len(articles),
            pages=len(page_list),
        )

    def _scrape_page(
        self,
        symbol: str,
        page: int,
        sort_by: str,
        headers: Dict[str, str],
    ) -> Optional[List[Dict[str, Any]]]:
        """Scrape a single page of ideas from the TradingView API.

        Args:
            symbol: Trading symbol slug.
            page: Page number to scrape (1-based).
            sort_by: Sorting criteria.
            headers: HTTP headers dict (including cookie if set).

        Returns:
            List of mapped idea dicts, or ``None`` if a captcha was detected.
        """
        if page == 1:
            url = f"{BASE_URL}/symbols/{symbol}/ideas/"
        else:
            url = f"{BASE_URL}/symbols/{symbol}/ideas/page-{page}/"

        params: Dict[str, str] = {"component-data-only": "1"}
        if sort_by == "recent":
            params["sort"] = "recent"

        try:
            response = requests.get(
                url, headers=headers, params=params, timeout=self.timeout,
            )

            if response.status_code != 200:
                logger.error(
                    "HTTP %d: Failed to fetch page %d for %s",
                    response.status_code, page, symbol,
                )
                return []

            if "<title>Captcha Challenge</title>" in response.text:
                logger.error(
                    "Captcha challenge on page %d of %s", page, symbol,
                )
                return None

            data = response.json()
            ideas_data = data.get("data", {}).get("ideas", {}).get("data", {})
            items = ideas_data.get("items", [])

            return [self._map_idea(item) for item in items]

        except JSONDecodeError as exc:
            logger.error("Invalid JSON for page %d of %s: %s", page, symbol, exc)
            return []
        except RequestException as exc:
            logger.error(
                "Network request failed for page %d of %s: %s", page, symbol, exc,
            )
            return []

    @staticmethod
    def _map_idea(item: Dict[str, Any]) -> Dict[str, Any]:
        """Map a raw API idea item to the output schema.

        Args:
            item: Raw idea dict from the TradingView API.

        Returns:
            Mapped idea dict with standardized keys.
        """
        return {
            "title": item.get("name", ""),
            "description": item.get("description", ""),
            "preview_image": item.get("symbol", {}).get("logo_urls", []),
            "chart_url": item.get("chart_url", ""),
            "comments_count": item.get("comments_count", 0),
            "views_count": item.get("views_count", 0),
            "author": item.get("user", {}).get("username", ""),
            "likes_count": item.get("likes_count", 0),
            "timestamp": item.get("date_timestamp", 0),
        }
