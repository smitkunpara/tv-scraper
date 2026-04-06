"""Ideas scraper for fetching trading ideas from TradingView."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Literal

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import BASE_URL
from tv_scraper.core.exceptions import ValidationError
from tv_scraper.core.validation_data import EXCHANGE_LITERAL

logger = logging.getLogger(__name__)

IDEAS_SORT_LITERAL = Literal["popular", "recent"]
ALLOWED_SORT_VALUES: set[IDEAS_SORT_LITERAL] = {"popular", "recent"}
DEFAULT_MAX_WORKERS = 3


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
        result = scraper.get_ideas(exchange="CRYPTO", symbol="BTCUSD")
    """

    def __init__(
        self,
        export_result: bool = False,
        export_type: str = "json",
        timeout: int = 10,
        cookie: str | None = None,
        max_workers: int = DEFAULT_MAX_WORKERS,
    ) -> None:
        super().__init__(
            export_result=export_result,
            export_type=export_type,
            timeout=timeout,
            cookie=cookie,
        )
        self._max_workers: int = max(1, max_workers)

    def get_ideas(
        self,
        exchange: EXCHANGE_LITERAL,
        symbol: str,
        start_page: int = 1,
        end_page: int = 1,
        sort_by: IDEAS_SORT_LITERAL = "popular",
    ) -> dict[str, Any]:
        """Scrape trading ideas for a symbol across one or more pages.

        Args:
            exchange: Exchange name (e.g. ``"NSE"``).
            symbol: Trading symbol slug (e.g. ``"NIFTY"``).
            start_page: First page to scrape (1-based).
            end_page: Last page to scrape (inclusive).
            sort_by: Sorting criteria — ``"popular"`` or ``"recent"``.

        Returns:
            Standardized response dict with keys
            ``status``, ``data``, ``metadata``, ``error``.
        """

        # --- Validation ---
        if start_page < 1:
            return self._error_response(
                f"start_page must be >= 1, got {start_page}",
                exchange=exchange,
                symbol=symbol,
                start_page=start_page,
                end_page=end_page,
                sort_by=sort_by,
            )
        if end_page < start_page:
            return self._error_response(
                f"end_page ({end_page}) must be >= start_page ({start_page})",
                exchange=exchange,
                symbol=symbol,
                start_page=start_page,
                end_page=end_page,
                sort_by=sort_by,
            )

        try:
            exchange, symbol = self.validator.verify_symbol_exchange(exchange, symbol)
            self.validator.validate_choice("sort_by", sort_by, ALLOWED_SORT_VALUES)
        except ValidationError as exc:
            return self._error_response(
                str(exc),
                exchange=exchange,
                symbol=symbol,
                start_page=start_page,
                end_page=end_page,
                sort_by=sort_by,
            )

        url_slug = f"{exchange}-{symbol}"

        page_list = range(start_page, end_page + 1)
        articles: list[dict[str, Any]] = []
        failed_pages: list[tuple[int, str]] = []

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = {
                executor.submit(self._scrape_page, url_slug, page, sort_by): page
                for page in page_list
            }
            for future in as_completed(futures, timeout=self.timeout * 2):
                page = futures[future]
                try:
                    result, error_msg = future.result(timeout=self.timeout)
                    if error_msg:
                        logger.error(
                            "Failed to scrape page %d of %s: %s",
                            page,
                            url_slug,
                            error_msg,
                        )
                        failed_pages.append((page, error_msg))
                        continue
                    if result is not None:
                        articles.extend(result)
                except Exception as exc:
                    logger.error("Failed to scrape page %d: %s", page, exc)
                    failed_pages.append((page, str(exc)))

        if failed_pages:
            return self._error_response(
                f"Failed pages: {failed_pages}. Articles collected so far: {len(articles)}",
                exchange=exchange,
                symbol=symbol,
                start_page=start_page,
                end_page=end_page,
                sort_by=sort_by,
                total=len(articles),
                pages=len(page_list),
                failed_pages=failed_pages,
            )

        # --- Export ---
        if self.export_result:
            self._export(
                data=articles,
                symbol=f"{exchange}_{symbol}",
                data_category="ideas",
            )

        return self._success_response(
            articles,
            exchange=exchange,
            symbol=symbol,
            start_page=start_page,
            end_page=end_page,
            sort_by=sort_by,
            total=len(articles),
            pages=len(page_list),
        )

    def _scrape_page(
        self,
        url_slug: str,
        page: int,
        sort_by: str,
    ) -> tuple[list[dict[str, Any]] | None, str | None]:
        """Scrape a single page of ideas from the TradingView API.

        Args:
            url_slug: Trading symbol slug (possibly combined with exchange).
            page: Page number to scrape (1-based).
            sort_by: Sorting criteria.

        Returns:
            Tuple of (List of mapped idea dicts, None) on success.
            Tuple of (None, error_message) on failure.
        """
        if page == 1:
            url = f"{BASE_URL}/symbols/{url_slug}/ideas/"
        else:
            url = f"{BASE_URL}/symbols/{url_slug}/ideas/page-{page}/"

        params: dict[str, str] = {"component-data-only": "1"}
        if sort_by == "recent":
            params["sort"] = "recent"

        response_data, error_msg = self._request("GET", url, params=params)

        if error_msg:
            return None, error_msg

        if not isinstance(response_data, dict):
            logger.error(
                "Unexpected response type for page %d of %s: %s",
                page,
                url_slug,
                type(response_data).__name__,
            )
            return [], None

        ideas_data = response_data.get("data")
        if not isinstance(ideas_data, dict):
            ideas_data = {}
        ideas_inner = ideas_data.get("ideas")
        if not isinstance(ideas_inner, dict):
            ideas_inner = {}
        items_container = ideas_inner.get("data")
        if not isinstance(items_container, dict):
            items_container = {}
        items = items_container.get("items")
        if not isinstance(items, list):
            items = []

        return [self._map_idea(item) for item in items], None

    @staticmethod
    def _map_idea(item: dict[str, Any]) -> dict[str, Any]:
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
