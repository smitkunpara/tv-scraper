# News Scraper

## Overview

`News` scrapes TradingView news flow, symbol-specific headlines, and full story content. It now supports the **News Flow (v2) API** with advanced categorical filtering.

- **News Flow (v2):** `https://news-mediator.tradingview.com/news-flow/v2/news`
- **Headlines (Legacy):** `https://news-headlines.tradingview.com/v2/view/headlines/symbol`
- **Story Content:** `https://news-mediator.tradingview.com/public/news/v1/story`

## Constructor

```python
from tv_scraper.scrapers.social import News

scraper = News(
    export_result=False,
    export_type="json",
    timeout=10,
    cookie=None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `export_result` | `bool` | `False` | Export results to file |
| `export_type` | `str` | `"json"` | Export format: `"json"` or `"csv"` |
| `timeout` | `int` | `10` | HTTP timeout in seconds |
| `cookie` | `str \| None` | `None` | TradingView cookie. If omitted, `TRADINGVIEW_COOKIE` env var is used when available |

## Method: `get_news()`

This is the primary method for fetching a live flow of news with advanced filtering.

```python
def get_news(
    symbol: str | None = None,
    corp_activity: list[str] | None = None,
    economic_category: list[str] | None = None,
    market: list[str] | None = None,
    market_country: list[str] | None = None,
    provider: list[str] | None = None,
    sector: list[str] | None = None,
    language: str = "en",
    limit: int = 50,
) -> dict[str, Any]
```

### Filtering & Validation

The Mediator API uses a complex filtering system. All categorical inputs are strictly validated against `Literal` types:

- **`market_country`**: List of 90+ country codes (e.g., `["US", "IN", "GB"]`).
- **`corp_activity`**: Filter by corporate events like `dividends`, `earnings`, `ipo`.
- **`economic_category`**: Filter by economic news like `gdp`, `labor`, `prices`.
- **`market`**: Filter by asset class like `stock`, `crypto`, `forex`.
- **`sector`**: Filter by industry sector like `Energy Minerals`, `Finance`.
- **`provider`**: Comprehensive list of news sources (refer to [Supported Data](../supported_data.md)).

> [!IMPORTANT]
> **URL Length Guard:** TradingView servers have limits on query string length. `get_news()` includes a pre-flight check that enforces a maximum URL length of **4096 characters**. If exceeded, it returns a `failed` response.

### Output Items (News Flow)

Each `data` item in the Flow API returns richer data than the legacy headlines:

```json
{
  "id": "tag:provider.com,2026:newsml_123:0",
  "title": "Headline title",
  "published": 1700000000,
  "urgency": 2,
  "permission": "free",
  "relatedSymbols": [
    {"symbol": "NASDAQ:AAPL", "currency_id": "USD"}
  ],
  "storyPath": "/news/path",
  "provider": {
    "id": "reuters",
    "name": "Reuters",
    "logo_id": "reuters_logo"
  },
  "is_flash": false
}
```

## Method: `get_news_headlines()` (Legacy)

Fetches symbol-specific headlines using the older symbols-based API.

```python
def get_news_headlines(
    exchange: EXCHANGE_LITERAL,
    symbol: str,
    provider: NEWS_PROVIDER_LITERAL | None = None,
    area: AREA_LITERAL | None = None,
    sort_by: Literal["latest", "oldest", "most_urgent", "least_urgent"] = "latest",
    section: Literal["all", "esg", "press_release", "financial_statement"] = "all",
    language: str = "en",
) -> dict[str, Any]
```

Sorting for this method is applied client-side after fetch.

## Method: `get_news_content()`

Retrieves the full text content of a news article.

```python
def get_news_content(
    story_id: str,
    language: str = "en",
) -> dict[str, Any]
```

### Behavior

- Parses output into: `id`, `title`, `published`, `storyPath`, `description`.
- `description` is built by merging AST-style paragraph nodes (`type == "p"`) from the response.

## Usage Examples

### Fetching News Flow with Filters

```python
from tv_scraper.scrapers.social import News

scraper = News()
result = scraper.get_news(
    market_country=["US", "IN"],
    market=["crypto", "stock"],
    sector=["Finance", "Technology Services"],
    limit=10
)
```

### Fetching Article Content

```python
# First get headlines or flow items
flow = scraper.get_news(symbol="NASDAQ:AAPL", limit=1)

if flow["status"] == "success" and flow["data"]:
    story_id = flow["data"][0]["id"]
    content = scraper.get_news_content(story_id=story_id)
    print(content["data"]["description"])
```
