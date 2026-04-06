"""News scraper for fetching headlines and article content from TradingView."""

import logging
from typing import Any, Literal

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.exceptions import ValidationError
from tv_scraper.core.validation_data import (
    AREA_LITERAL,
    EXCHANGE_LITERAL,
    LANGUAGE_LITERAL,
    NEWS_PROVIDER_LITERAL,
)

logger = logging.getLogger(__name__)

# TradingView News API endpoints
NEWS_HEADLINES_URL = "https://news-headlines.tradingview.com/v2/view/headlines/symbol"
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
    supports scraping full article content given a story path.

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

    def get_news_headlines(
        self,
        exchange: EXCHANGE_LITERAL,
        symbol: str,
        provider: NEWS_PROVIDER_LITERAL | None = None,
        area: AREA_LITERAL | None = None,
        sort_by: SORT_BY_LITERAL = "latest",
        section: NEWS_SECTION_LITERAL = "all",
        language: LANGUAGE_LITERAL = "en",
    ) -> dict[str, Any]:
        """Scrape news headlines for a symbol.

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
        meta: dict[str, Any] = {
            "exchange": exchange,
            "symbol": symbol,
            "sort_by": sort_by,
            "section": section,
            "language": language,
        }
        if provider is not None:
            meta["provider"] = provider
        if area is not None:
            meta["area"] = area

        meta.update({"exchange": exchange, "symbol": symbol})

        try:
            exchange, symbol = self.validator.verify_symbol_exchange(exchange, symbol)
            self.validator.validate_choice("sort_by", sort_by, VALID_SORT_OPTIONS)
            self.validator.validate_choice("section", section, VALID_SECTIONS)

            languages = self.validator.get_languages()
            if language not in languages.values():
                raise ValidationError(
                    f"Invalid language: '{language}'. "
                    f"Allowed values: {', '.join(sorted(languages.values()))}"
                )

            providers = self.validator.get_news_providers()
            if provider is not None and provider not in providers:
                raise ValidationError(
                    f"Invalid provider: '{provider}'. "
                    f"Allowed values: {', '.join(sorted(providers))}"
                )

            areas = self.validator.get_areas()
            if area is not None and area not in areas:
                raise ValidationError(
                    f"Invalid area: '{area}'. "
                    f"Allowed values: {', '.join(sorted(areas.keys()))}"
                )
        except ValidationError as exc:
            return self._error_response(str(exc), **meta)

        params: dict[str, Any] = {
            "client": "web",
            "lang": language,
            "area": areas[area] if area else "",
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
            return self._error_response(error_msg, **meta)

        assert response_json is not None

        items: list[dict[str, Any]] = response_json.get("items", [])

        if not items:
            return self._success_response([], total=0, **meta)

        items = self._sort_news(items, sort_by)
        cleaned_items = [self._clean_headline(item) for item in items]

        if self.export_result:
            self._export(
                data=cleaned_items,
                symbol=f"{exchange}_{symbol}",
                data_category="news",
            )

        return self._success_response(cleaned_items, total=len(cleaned_items), **meta)

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
        meta: dict[str, Any] = {
            "story_id": story_id,
            "language": language,
        }

        if not story_id or not story_id.strip():
            return self._error_response("story_id cannot be empty", **meta)

        languages = self.validator.get_languages()
        if language not in languages.values():
            return self._error_response(
                f"Invalid language: '{language}'. "
                f"Allowed values: {', '.join(sorted(languages.values()))}",
                **meta,
            )

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
            return self._error_response(error_msg, **meta)

        assert story_data is not None

        article_data = self._parse_story(story_data)

        return self._success_response(
            article_data,
            story_id=story_id,
            language=language,
        )

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
        """Remove unwanted fields from headline.

        Removes: id, sourceLogoid, provider, relatedSymbols, permission, urgency

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
