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

# Get full article content using the 'id' from headlines
if result["status"] == "success" and result["data"]:
    article_id = result["data"][0]["id"]
    content = scraper.scrape_content(story_id=article_id)
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
scrape_content(
    story_id: str,
    language: str = "en",
) -> Dict[str, Any]
```

| Parameter    | Type         | Default | Description                                    |
|--------------|--------------|---------|------------------------------------------------|
| `story_id`   | str          | —       | Story ID from headlines API (e.g. `"tag:reuters.com,2026:newsml_L4N3Z9104:0"`) |
| `language`   | str          | `"en"`  | Language code (e.g. `"en"`, `"fr"`)            |

## Response Format

All methods return a standardized response envelope:

```json
{
  "status": "success",
  "data": [
    {
      "id": "tag:reuters.com,2026:newsml_L4N3Z9104:0",
      "title": "Bitcoin Surges as Institutional Interest Grows",
      "shortDescription": "Bitcoin reached new highs today as institutional investors...",
      "published": 1705350000,
      "storyPath": "/news/story_12345-bitcoin-surges/"
    },
    ...
  ],
  "metadata": {
    "exchange": "BINANCE",
    "symbol": "BTCUSD",
    "total": 25
  },
  "error": null
}
```

### Headline Schema

Each item in the `data` array contains:

```json
{
  "id": "tag:reuters.com,2026:newsml_L4N3Z9104:0",
  "title": "Bitcoin Hits New High",
  "shortDescription": "Brief summary of the news article...",
  "published": 1678900000,
  "storyPath": "/news/story/12345"
}
```

### Article Content Response

```json
{
  "status": "success",
  "data": {
    "title": "Bitcoin Hits New High",
    "description": "Full article content with paragraphs separated by newlines.\nSecond paragraph here...",
    "published": 1643097623,
    "storyPath": "/news/story/12345"
  },
  "metadata": {
    "story_id": "tag:reuters.com,2026:newsml_L4N3Z9104:0"
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
