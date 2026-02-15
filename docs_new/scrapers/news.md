# News Scraper

## Overview

Scrape headlines and full article content from TradingView news providers.

## Quick Start

```python
from tv_scraper.scrapers.social import News

scraper = News()

# Get headlines
result = scraper.scrape_headlines(exchange="BINANCE", symbol="BTCUSD")
if result["status"] == "success":
    for item in result["data"]:
        print(item["title"])

# Get full article content
if result["data"]:
    content = scraper.scrape_content(result["data"][0]["storyPath"])
    print(content["data"]["title"])
```

## API Reference

### Constructor

```python
News(export_result=False, export_type="json", timeout=10, cookie=None)
```

| Parameter       | Type   | Default  | Description                        |
|-----------------|--------|----------|------------------------------------|
| `export_result` | bool   | `False`  | Export results to file             |
| `export_type`   | str    | `"json"` | `"json"` or `"csv"`               |
| `timeout`       | int    | `10`     | HTTP request timeout in seconds    |
| `cookie`        | str    | `None`   | TradingView cookie for captcha     |

### `scrape_headlines()`

```python
scrape_headlines(
    exchange: str,
    symbol: str,
    provider: str | None = None,
    area: str | None = None,
    sort_by: str = "latest",
    section: str = "all",
    language: str = "en",
) -> Dict[str, Any]
```

| Parameter  | Type         | Default    | Description                                       |
|------------|--------------|------------|---------------------------------------------------|
| `exchange` | str          | —          | Exchange name (e.g. `"BINANCE"`)                  |
| `symbol`   | str          | —          | Trading symbol (e.g. `"BTCUSD"`)                  |
| `provider` | str \| None  | `None`     | News provider (e.g. `"cointelegraph"`)            |
| `area`     | str \| None  | `None`     | Region: `world`, `americas`, `europe`, `asia`, `oceania`, `africa` |
| `sort_by`  | str          | `"latest"` | `latest`, `oldest`, `most_urgent`, `least_urgent` |
| `section`  | str          | `"all"`    | `all`, `esg`, `press_release`, `financial_statement` |
| `language` | str          | `"en"`     | Language code (e.g. `"en"`, `"fr"`, `"ja"`)       |

### `scrape_content()`

```python
scrape_content(story_path: str) -> Dict[str, Any]
```

| Parameter    | Type | Description                                    |
|--------------|------|------------------------------------------------|
| `story_path` | str  | Relative path from headline (e.g. `"/news/story/123"`) |

## Response Format

All methods return a standardized response envelope:

```json
{
  "status": "success",
  "data": [
    {
      "id": "story_12345",
      "title": "Bitcoin Surges as Institutional Interest Grows",
      "provider": "cointelegraph",
      "published": 1705350000,
      "urgency": 2,
      "storyPath": "/news/story_12345-bitcoin-surges/",
      "link": "https://www.tradingview.com/news/story_12345/"
    }
  ],
  "metadata": {
    "exchange": "BINANCE",
    "symbol": "BTCUSD",
    "provider": "cointelegraph"
  },
  "error": null
}
```

### Headline Item

```json
{
    "id": "12345",
    "title": "Bitcoin Hits New High",
    "provider": "cointelegraph",
    "published": 1678900000,
    "urgency": 2,
    "storyPath": "/news/story/12345",
    "link": "https://..."
}
```

### Article Content

```json
{
  "status": "success",
  "data": {
    "breadcrumbs": "Markets > Crypto",
    "title": "Bitcoin Hits New High",
    "published_datetime": "2025-01-15T10:00:00Z",
    "related_symbols": [{"symbol": "BTCUSD", "logo": "https://..."}],
    "body": [
        {"type": "text", "content": "Paragraph text..."},
        {"type": "image", "src": "https://...", "alt": "Chart"}
    ],
    "tags": ["Bitcoin", "Crypto"]
  },
  "metadata": {
    "symbol": "BTCUSD",
    "exchange": "BINANCE"
  },
  "error": null
}
```

## Migration from `NewsScraper`

| Old (`tradingview_scraper`)                    | New (`tv_scraper`)                            |
|------------------------------------------------|-----------------------------------------------|
| `from tradingview_scraper.symbols.news import NewsScraper` | `from tv_scraper.scrapers.social import News` |
| `NewsScraper(cookie=cookie)`                   | `News(cookie=cookie)`                         |
| `scraper.scrape_headlines(symbol=..., exchange=...)` | `scraper.scrape_headlines(exchange=..., symbol=...)` |
| `sort="latest"`                                | `sort_by="latest"`                            |
| `scraper.scrape_news_content(story_path)`      | `scraper.scrape_content(story_path)`          |
| Returns `list` of headlines                    | Returns `{"status", "data", "metadata", "error"}` |
| Raises `ValueError` / `RuntimeError`           | Returns error response, never raises          |

### Key Changes

1. **Class rename**: `NewsScraper` → `News`
2. **Parameter order**: `exchange` before `symbol` (was `symbol` first)
3. **Parameter rename**: `sort` → `sort_by`
4. **Method rename**: `scrape_news_content()` → `scrape_content()`
5. **Response format**: All methods return a standardized envelope dict instead of raw lists/dicts
6. **Error handling**: Never raises — always returns `{"status": "failed", ...}` on error
7. **Inherits**: `BaseScraper` for shared functionality (export, validation, HTTP)
