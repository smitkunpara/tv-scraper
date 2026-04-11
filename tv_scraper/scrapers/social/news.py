"""News scraper for fetching headlines and article content from TradingView."""

import logging
from typing import Any, Literal
from urllib.parse import urlencode

from tv_scraper.core import validators
from tv_scraper.core.base import BaseScraper, catch_errors
from tv_scraper.core.validation_data import (
    AREA_LITERAL,
    AREAS,
    EXCHANGE_LITERAL,
    NEWS_CORP_ACTIVITY_LITERAL,
    NEWS_COUNTRY_LITERAL,
    NEWS_ECONOMIC_CATEGORY_LITERAL,
    NEWS_MARKET_LITERAL,
    NEWS_PROVIDER_LITERAL,
    NEWS_SECTOR_LITERAL,
)

logger = logging.getLogger(__name__)

# TradingView News API endpoints
NEWS_HEADLINES_URL = "https://news-headlines.tradingview.com/v2/view/headlines/symbol"
NEWS_FLOW_URL = "https://news-mediator.tradingview.com/news-flow/v2/news"
NEWS_STORY_URL = "https://news-mediator.tradingview.com/public/news/v1/story"

# Valid sort options
SORT_BY_LITERAL = Literal["latest", "oldest", "most_urgent", "least_urgent"]
VALID_SORT_OPTIONS: set[SORT_BY_LITERAL] = {
    "latest",
    "oldest",
    "most_urgent",
    "least_urgent",
}

# Valid section options
NEWS_SECTION_LITERAL = Literal["all", "esg", "press_release", "financial_statement"]
VALID_SECTIONS: set[NEWS_SECTION_LITERAL] = {
    "all",
    "esg",
    "press_release",
    "financial_statement",
}


class News(BaseScraper):
    """Scraper for TradingView news headlines and article content.

    Fetches news headlines for a given symbol and exchange, with optional
    filters for provider, area, section, language, and sort order. Also
    supports scraping full article content given a story ID.

    Args:
        export_result: Whether to export results to file.
        export_type: Export format, ``"json"`` or ``"csv"``.
        timeout: HTTP request timeout in seconds.
        cookie: Optional TradingView cookie for captcha avoidance.

    Example::

        from tv_scraper.scrapers.social import News

        scraper = News()
        news = scraper.get_news_headlines(exchange="BINANCE", symbol="BTCUSD")
        if news["status"] == "success" and news["data"]:
            content = scraper.get_news_content(news["data"][0]["id"])
    """

    def __init__(
        self,
        export_result: bool = False,
        export_type: str = "json",
        timeout: int = 10,
        cookie: str | None = None,
    ) -> None:
        super().__init__(
            export_result=export_result,
            export_type=export_type,
            timeout=timeout,
            cookie=cookie,
        )

    @catch_errors
    def get_news(
        self,
        symbol: str | None = None,
        corp_activity: list[NEWS_CORP_ACTIVITY_LITERAL] | None = None,
        economic_category: list[NEWS_ECONOMIC_CATEGORY_LITERAL] | None = None,
        market: list[NEWS_MARKET_LITERAL] | None = None,
        market_country: list[NEWS_COUNTRY_LITERAL] | None = None,
        provider: list[NEWS_PROVIDER_LITERAL] | None = None,
        sector: list[NEWS_SECTOR_LITERAL] | None = None,
        language: str = "en",
        limit: int = 50,
    ) -> dict[str, Any]:
        """Scrape news flow using the Mediator API with advanced filtering.

        Args:
            symbol: Optional symbol filter (e.g. ``"OANDA:XAUUSD"``).
            corp_activity: Optional list of corporate activities.
            economic_category: Optional list of economic categories.
            market: Optional list of market types.
            market_country: Optional list of country codes.
            provider: Optional list of news providers.
            sector: Optional list of industry sectors.
            language: Language code (default: ``"en"``).
            limit: Maximum number of items to return (applied client-side).

        Returns:
            Standardized response dict with keys
            ``status``, ``data``, ``metadata``, ``error``.
        """
        validators.validate_language(language)

        filters = [f"lang:{language}"]
        if symbol:
            filters.append(f"symbol:{symbol}")
        if corp_activity:
            for val in corp_activity:
                validators.validate_news_corp_activity(val)
            filters.append(f"corp_activity:{','.join(corp_activity)}")
        if economic_category:
            for val in economic_category:
                validators.validate_news_economic_category(val)
            filters.append(f"economic_category:{','.join(economic_category)}")
        if market:
            for val in market:
                validators.validate_news_market(val)
            filters.append(f"market:{','.join(market)}")
        if market_country:
            for val in market_country:
                validators.validate_news_country(val)
            filters.append(f"market_country:{','.join(market_country)}")
        if provider:
            for val in provider:
                validators.validate_news_provider(val)
            filters.append(f"provider:{','.join(provider)}")
        if sector:
            for val in sector:
                validators.validate_news_sector(val)
            filters.append(f"sector:{','.join(sector)}")

        params = [("filter", f) for f in filters]
        params.extend(
            [
                ("client", "screener"),
                ("streaming", "true"),
                ("user_prostatus", "non_pro"),
            ]
        )

        # Pre-flight URL length check
        full_url = f"{NEWS_FLOW_URL}?{urlencode(params)}"
        if len(full_url) > 4096:
            return self._error_response(
                f"URL length ({len(full_url)}) exceeds the maximum allowed limit of 4096 characters. "
                "Please reduce the number of filters."
            )

        response_json, error_msg = self._request(
            "GET",
            NEWS_FLOW_URL,
            params=params,
        )

        if error_msg:
            return self._error_response(error_msg)

        assert response_json is not None
        items = response_json.get("items", [])[:limit]

        cleaned_items = [self._clean_headline(item) for item in items]

        if self.export_result:
            self._export(
                data=cleaned_items,
                symbol=symbol or "news_flow",
                data_category="news",
            )

        return self._success_response(cleaned_items, total=len(cleaned_items))

    @catch_errors
    def get_news_headlines(
        self,
        exchange: EXCHANGE_LITERAL,
        symbol: str,
        provider: NEWS_PROVIDER_LITERAL | None = None,
        area: AREA_LITERAL | None = None,
        sort_by: SORT_BY_LITERAL = "latest",
        section: NEWS_SECTION_LITERAL = "all",
        language: str = "en",
    ) -> dict[str, Any]:
        """Scrape news headlines for a symbol using the legacy symbols API.

        Args:
            exchange: Exchange name (e.g. ``"NSE"``).
            symbol: Trading symbol slug (e.g. ``"NIFTY"``).
            provider: Optional news provider filter (e.g. ``"cointelegraph"``).
            area: Optional region filter (e.g. ``"americas"``).
            sort_by: Sort order. One of ``"latest"``, ``"oldest"``,
                ``"most_urgent"``, ``"least_urgent"``.
            section: News section. One of ``"all"``, ``"esg"``,
                ``"press_release"``, ``"financial_statement"``.
            language: Language code (e.g. ``"en"``, ``"fr"``).

        Returns:
            Standardized response dict with keys
            ``status``, ``data``, ``metadata``, ``error``.
        """
        validators.verify_symbol_exchange(exchange, symbol)
        validators.validate_language(language)
        if provider:
            validators.validate_news_provider(provider)
        if area:
            validators.validate_area(area)
        validators.validate_choice(
            "sort_by", sort_by, ["latest", "oldest", "most_urgent", "least_urgent"]
        )
        validators.validate_choice(
            "section",
            section,
            ["all", "esg", "press_release", "financial_statement"],
        )

        params: dict[str, Any] = {
            "client": "web",
            "lang": language,
            "area": AREAS.get(area, "") if area else "",
            "provider": provider.replace(".", "_") if provider else "",
            "section": "" if section == "all" else section,
            "streaming": "",
            "symbol": f"{exchange}:{symbol}",
        }

        response_json, error_msg = self._request(
            "GET",
            NEWS_HEADLINES_URL,
            params=params,
        )

        if error_msg:
            return self._error_response(error_msg)

        assert response_json is not None

        items: list[dict[str, Any]] = response_json.get("items", [])

        if not items:
            return self._success_response([], total=0)

        items = self._sort_news(items, sort_by)
        cleaned_items = [self._clean_legacy_headline(item) for item in items]

        if self.export_result:
            self._export(
                data=cleaned_items,
                symbol=f"{exchange}_{symbol}",
                data_category="news",
            )

        return self._success_response(cleaned_items, total=len(cleaned_items))

    @catch_errors
    def get_news_content(
        self,
        story_id: str,
        language: str = "en",
    ) -> dict[str, Any]:
        """Scrape full article content from a TradingView news story.

        Args:
            story_id: Story ID from the headlines API
                (e.g. ``"tag:reuters.com,2026:newsml_L4N3Z9104:0"``).
            language: Language code (default: ``"en"``).

        Returns:
            Standardized response dict with keys
            ``status``, ``data``, ``metadata``, ``error``.
        """
        if not story_id or not story_id.strip():
            return self._error_response("story_id cannot be empty")

        validators.validate_language(language)

        params: dict[str, str] = {
            "id": story_id,
            "lang": language,
            "user_prostatus": "non_pro",
        }

        story_data, error_msg = self._request(
            "GET",
            NEWS_STORY_URL,
            params=params,
        )

        if error_msg:
            return self._error_response(error_msg)

        assert story_data is not None

        article_data = self._parse_story(story_data)

        return self._success_response(article_data)

    def _sort_news(
        self,
        news_list: list[dict[str, Any]],
        sort_by: str,
    ) -> list[dict[str, Any]]:
        """Sort news items by the given criterion.

        Args:
            news_list: List of news headline dicts.
            sort_by: Sort criterion.

        Returns:
            Sorted list of news headline dicts.
        """
        reverse = sort_by in ("latest", "most_urgent")
        key = "published" if sort_by in ("latest", "oldest") else "urgency"
        return sorted(news_list, key=lambda x: x.get(key, 0), reverse=reverse)

    def _clean_headline(self, item: dict[str, Any]) -> dict[str, Any]:
        """Normalize news item from Mediator API.

        Args:
            item: Raw news item dict.

        Returns:
            Cleaned news item dict with standardized fields.
        """
        return {
            "id": item.get("id"),
            "title": item.get("title"),
            "published": item.get("published"),
            "urgency": item.get("urgency"),
            "permission": item.get("permission"),
            "relatedSymbols": item.get("relatedSymbols", []),
            "storyPath": self._normalize_story_path(item.get("storyPath", "")),
            "provider": item.get("provider", {}),
            "is_flash": item.get("is_flash", False),
        }

    def _clean_legacy_headline(self, item: dict[str, Any]) -> dict[str, Any]:
        """Remove unwanted fields from legacy headlines.

        Keeps core fields (id, title, shortDescription, published, storyPath)
        and drops extra fields from the raw payload.

        Args:
            item: Raw headline dict.

        Returns:
            Cleaned headline dict with only relevant fields.
        """
        return {
            "id": item.get("id"),
            "title": item.get("title"),
            "shortDescription": item.get("shortDescription"),
            "published": item.get("published"),
            "storyPath": self._normalize_story_path(item.get("storyPath", "")),
        }

    def _normalize_story_path(self, story_path: str) -> str:
        """Ensure story path starts with a forward slash.

        Args:
            story_path: The raw story path.

        Returns:
            Story path with leading slash if not already present.
        """
        if story_path and not story_path.startswith("/"):
            return f"/{story_path}"
        return story_path

    def _parse_story(self, story_data: dict[str, Any]) -> dict[str, Any]:
        """Parse story JSON into simplified format.

        Extracts title, description, published timestamp, and id.
        Description is built from ast_description.children by merging paragraphs.

        Args:
            story_data: Raw JSON response from the story API.

        Returns:
            Dict with title, description, published timestamp, id, and storyPath.
        """
        title = story_data.get("title", "")
        published = story_data.get("published", 0)
        story_id = story_data.get("id", "")
        description = self._parse_ast_description(story_data.get("ast_description", {}))
        story_path = self._normalize_story_path(story_data.get("story_path", ""))

        return {
            "id": story_id,
            "title": title,
            "description": description,
            "published": published,
            "storyPath": story_path,
        }

    def _parse_ast_description(self, ast_desc: dict[str, Any]) -> str:
        """Parse ast_description.children into a description string.

        Merges paragraph children, extracting text from strings and
        symbol objects, joining paragraphs with newlines.

        Args:
            ast_desc: ast_description object with children array.

        Returns:
            Merged description string with paragraphs separated by newlines.
        """
        children = ast_desc.get("children", [])
        paragraphs: list[str] = []

        for child in children:
            if not isinstance(child, dict):
                continue

            child_type = child.get("type")
            if child_type == "p":
                para_children = child.get("children", [])
                para_text = self._parse_paragraph_children(para_children)
                if para_text.strip():
                    paragraphs.append(para_text.strip())

        return "\n".join(paragraphs)

    def _parse_paragraph_children(self, children: list[Any]) -> str:
        """Parse children of a paragraph node.

        Extracts text from string children and params.text from object children.

        Args:
            children: List of paragraph children (strings or dicts).

        Returns:
            Merged paragraph text.
        """
        parts: list[str] = []

        for item in children:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                params = item.get("params", {})
                text = params.get("text", "")
                if text:
                    parts.append(text)

        return "".join(parts)
