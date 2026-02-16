"""News scraper for fetching headlines and article content from TradingView."""

import logging
from typing import Any, Dict, List, Optional

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

# TradingView News API endpoints
NEWS_HEADLINES_URL = (
    "https://news-headlines.tradingview.com/v2/view/headlines/symbol"
)
NEWS_STORY_URL = (
    "https://news-mediator.tradingview.com/public/news/v1/story"
)

# Valid sort options
VALID_SORT_OPTIONS = {"latest", "oldest", "most_urgent", "least_urgent"}

# Valid section options
VALID_SECTIONS = {"all", "esg", "press_release", "financial_statement"}


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
        headlines = scraper.scrape_headlines(exchange="BINANCE", symbol="BTCUSD")
        if headlines["status"] == "success" and headlines["data"]:
            content = scraper.scrape_content(headlines["data"][0]["storyPath"])
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
        if cookie:
            self._headers["cookie"] = cookie

        # Cache validation data
        self._news_providers: List[str] = self.validator.get_news_providers()
        self._languages: Dict[str, str] = self.validator.get_languages()
        self._areas: Dict[str, str] = self.validator.get_areas()
        self._language_codes: List[str] = list(self._languages.values())

    def scrape_headlines(
        self,
        exchange: str,
        symbol: str,
        provider: Optional[str] = None,
        area: Optional[str] = None,
        sort_by: str = "latest",
        section: str = "all",
        language: str = "en",
    ) -> Dict[str, Any]:
        """Scrape news headlines for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NSE"``). Can be empty if
                combined symbol is used in the `symbol` parameter.
            symbol: Trading symbol slug (e.g. ``"NIFTY"``) or combined
                ``"EXCHANGE:SYMBOL"`` string (e.g. ``"NSE:NIFTY"``).
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
        # Support combined EXCHANGE:SYMBOL
        if not exchange and ":" in symbol:
            exchange, symbol = symbol.split(":", 1)

        # Validate inputs
        try:
            self.validator.validate_exchange(exchange)
            self.validator.validate_symbol(exchange, symbol)
            self.validator.validate_choice("sort_by", sort_by, VALID_SORT_OPTIONS)
            self.validator.validate_choice("section", section, VALID_SECTIONS)

            if language not in self._language_codes:
                raise ValidationError(
                    f"Invalid language: '{language}'. "
                    f"Allowed values: {', '.join(sorted(self._language_codes))}"
                )

            if provider is not None and provider not in self._news_providers:
                raise ValidationError(
                    f"Invalid provider: '{provider}'. "
                    f"Allowed values: {', '.join(sorted(self._news_providers))}"
                )

            if area is not None and area not in self._areas:
                raise ValidationError(
                    f"Invalid area: '{area}'. "
                    f"Allowed values: {', '.join(sorted(self._areas.keys()))}"
                )
        except ValidationError as exc:
            return self._error_response(str(exc))

        # Build URL parameters
        area_code = self._areas[area] if area else ""
        provider_param = provider.replace(".", "_") if provider else ""
        section_param = "" if section == "all" else section

        url = (
            f"{NEWS_HEADLINES_URL}"
            f"?client=web"
            f"&lang={language}"
            f"&area={area_code}"
            f"&provider={provider_param}"
            f"&section={section_param}"
            f"&streaming="
            f"&symbol={exchange}:{symbol}"
        )

        try:
            response = self._make_request(
                url,
                method="GET",
            )
            response.raise_for_status()

            # Check captcha
            if "<title>Captcha Challenge</title>" in response.text:
                logger.error(
                    "Captcha Challenge encountered for %s on %s.",
                    symbol,
                    exchange,
                )
                return self._error_response(
                    f"Captcha challenge encountered for {symbol} on {exchange}. "
                    "Try updating the TRADINGVIEW_COOKIE."
                )

            response_json = response.json()
            items: List[Dict[str, Any]] = response_json.get("items", [])

            if not items:
                return self._success_response(
                    [],
                    symbol=symbol,
                    exchange=exchange,
                    total=0,
                )

            # Apply client-side sorting
            items = self._sort_news(items, sort_by)

            # Clean up output - remove unwanted fields
            cleaned_items = [self._clean_headline(item) for item in items]

            # Export if requested
            if self.export_result:
                self._export(
                    data=cleaned_items,
                    symbol=f"{exchange}_{symbol}",
                    data_category="news",
                )

            return self._success_response(
                cleaned_items,
                symbol=symbol,
                exchange=exchange,
                total=len(cleaned_items),
            )

        except Exception as exc:
            return self._error_response(f"Request failed: {exc}")

    def scrape_content(
        self,
        story_id: str,
        language: str = "en",
    ) -> Dict[str, Any]:
        """Scrape full article content from a TradingView news story.

        Args:
            story_id: Story ID from the headlines API
                (e.g. ``"tag:reuters.com,2026:newsml_L4N3Z9104:0"``).
            language: Language code (default: ``"en"``).

        Returns:
            Standardized response dict with keys
            ``status``, ``data``, ``metadata``, ``error``.
        """
        try:
            params = {
                "id": story_id,
                "lang": language,
                "user_prostatus": "non_pro",
            }

            response = self._make_request(
                NEWS_STORY_URL,
                method="GET",
                params=params,
            )
            response.raise_for_status()

            story_data = response.json()

            # Parse the story data
            article_data = self._parse_story(story_data)

            return self._success_response(
                article_data,
                story_id=story_id,
            )

        except Exception as exc:
            return self._error_response(f"Request failed: {exc}")

    def _sort_news(
        self,
        news_list: List[Dict[str, Any]],
        sort_by: str,
    ) -> List[Dict[str, Any]]:
        """Sort news items by the given criterion.

        Args:
            news_list: List of news headline dicts.
            sort_by: Sort criterion.

        Returns:
            Sorted list of news headline dicts.
        """
        if sort_by == "latest":
            return sorted(
                news_list, key=lambda x: x.get("published", 0), reverse=True
            )
        elif sort_by == "oldest":
            return sorted(
                news_list, key=lambda x: x.get("published", 0), reverse=False
            )
        elif sort_by == "most_urgent":
            return sorted(
                news_list, key=lambda x: x.get("urgency", 0), reverse=True
            )
        elif sort_by == "least_urgent":
            return sorted(
                news_list, key=lambda x: x.get("urgency", 0), reverse=False
            )
        return news_list

    def _clean_headline(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Remove unwanted fields from headline.

        Removes: id, sourceLogoid, provider, relatedSymbols, permission, urgency

        Args:
            item: Raw headline dict.

        Returns:
            Cleaned headline dict with only relevant fields.
        """
        # Ensure story_path starts with "/"
        story_path = item.get("storyPath", "")
        if story_path and not story_path.startswith("/"):
            story_path = f"/{story_path}"

        return {
            "id": item.get("id"),
            "title": item.get("title"),
            "shortDescription": item.get("shortDescription"),
            "published": item.get("published"),
            "storyPath": story_path,
        }

    def _parse_story(self, story_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse story JSON into simplified format.

        Extracts title, description, and published timestamp.
        Description is built from ast_description.children by merging paragraphs.

        Args:
            story_data: Raw JSON response from the story API.

        Returns:
            Dict with title, description, and published timestamp.
        """
        # Extract basic fields
        title = story_data.get("title", "")
        published = story_data.get("published", 0)

        # Parse ast_description to build description
        description = self._parse_ast_description(
            story_data.get("ast_description", {})
        )

        # Ensure story_path starts with "/"
        story_path = story_data.get("story_path", "")
        if story_path and not story_path.startswith("/"):
            story_path = f"/{story_path}"

        return {
            "title": title,
            "description": description,
            "published": published,
            "storyPath": story_path,
        }

    def _parse_ast_description(self, ast_desc: Dict[str, Any]) -> str:
        """Parse ast_description.children into a description string.

        Merges paragraph children, extracting text from strings and
        symbol objects, joining paragraphs with newlines.

        Args:
            ast_desc: ast_description object with children array.

        Returns:
            Merged description string with paragraphs separated by newlines.
        """
        children = ast_desc.get("children", [])
        paragraphs: List[str] = []

        for child in children:
            if not isinstance(child, dict):
                continue

            child_type = child.get("type")
            if child_type == "p":
                # Process paragraph children
                para_children = child.get("children", [])
                para_text = self._parse_paragraph_children(para_children)
                if para_text.strip():
                    paragraphs.append(para_text.strip())

        return "\n".join(paragraphs)

    def _parse_paragraph_children(self, children: List[Any]) -> str:
        """Parse children of a paragraph node.

        Extracts text from string children and params.text from object children.

        Args:
            children: List of paragraph children (strings or dicts).

        Returns:
            Merged paragraph text.
        """
        parts: List[str] = []

        for item in children:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                # Extract text from symbol objects
                params = item.get("params", {})
                text = params.get("text", "")
                if text:
                    parts.append(text)

        return "".join(parts)
