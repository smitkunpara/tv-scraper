# Ideas Scraper

## Overview

The Ideas scraper fetches user-published trading ideas from TradingView for a specified symbol. It supports pagination, sorting by popularity or recency, concurrent page scraping, and optional cookie authentication for captcha bypass.

## API

### Constructor

```python
from tv_scraper.scrapers.social import Ideas

scraper = Ideas(
    export_result=False,   # Whether to export results to file
    export_type="json",    # Export format: "json" or "csv"
    timeout=10,            # HTTP timeout in seconds
    cookie=None,           # TradingView session cookie (or set TRADINGVIEW_COOKIE env var)
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `export_result` | `bool` | `False` | Export results to file |
| `export_type` | `str` | `"json"` | Export format (`"json"` or `"csv"`) |
| `timeout` | `int` | `10` | HTTP request timeout in seconds |
| `cookie` | `str \| None` | `None` | Session cookie for captcha bypass |

### `scrape()`

```python
result = scraper.scrape(
    exchange="CRYPTO",
    symbol="BTCUSD",
    start_page=1,
    end_page=1,
    sort_by="popular",
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `exchange` | `str` | — | Exchange name (metadata only) |
| `symbol` | `str` | — | Trading symbol slug |
| `start_page` | `int` | `1` | First page to scrape |
| `end_page` | `int` | `1` | Last page to scrape (inclusive) |
| `sort_by` | `str` | `"popular"` | `"popular"` or `"recent"` |

### Response Format

All responses use the standard envelope:

```json
{
  "status": "success",
  "data": [
    {
      "title": "BTCUSD: Bullish Breakout Confirmed",
      "description": "Bitcoin has broken above the key resistance level of $45k...",
      "author": "CryptoAnalyst99",
      "comments_count": 24,
      "views_count": 1250,
      "likes_count": 85,
      "timestamp": 1705350400,
      "chart_url": "https://www.tradingview.com/chart/BTCUSD/abc123xyz/",
      "preview_image": ["https://s3.tradingview.com/i/abc123xyz_mid.png"]
    }
  ],
  "metadata": {
    "exchange": "CRYPTO",
    "symbol": "BTCUSD",
    "sort_by": "popular",
    "pages": 1,
    "total": 1
  },
  "error": null
}
```

Each idea dict:

| Field | Type | Description |
|-------|------|-------------|
| `title` | `str` | Idea title |
| `description` | `str` | Content/description |
| `preview_image` | `list` | Logo/preview image URLs |
| `chart_url` | `str` | Link to TradingView chart |
| `comments_count` | `int` | Number of comments |
| `views_count` | `int` | Number of views |
| `author` | `str` | Author username |
| `likes_count` | `int` | Number of likes |
| `timestamp` | `int` | Unix timestamp of publication |

## Examples

### Basic Usage

```python
from tv_scraper.scrapers.social import Ideas

scraper = Ideas()
result = scraper.scrape(exchange="CRYPTO", symbol="BTCUSD")

if result["status"] == "success":
    for idea in result["data"]:
        print(f"{idea['title']} by {idea['author']} ({idea['likes_count']} likes)")
```

### Multi-Page Scrape

```python
result = scraper.scrape(
    exchange="CRYPTO",
    symbol="BTCUSD",
    start_page=1,
    end_page=5,
    sort_by="recent",
)
print(f"Found {result['metadata']['total']} ideas across {result['metadata']['pages']} pages")
```

### With Cookie Authentication

```python
scraper = Ideas(cookie="sessionid=abc123; _sp_id=xyz789")
result = scraper.scrape(exchange="CRYPTO", symbol="BTCUSD")
```

Or set the `TRADINGVIEW_COOKIE` environment variable and omit the `cookie` parameter.

### Export to File

```python
scraper = Ideas(export_result=True, export_type="csv")
result = scraper.scrape(exchange="CRYPTO", symbol="ETHUSD", end_page=3)
```

## Migration from `tradingview_scraper`

| Old (`tradingview_scraper`) | New (`tv_scraper`) |
|---|---|
| `from tradingview_scraper.symbols.ideas import Ideas` | `from tv_scraper.scrapers.social import Ideas` |
| `Ideas(cookie=...)` | `Ideas(cookie=..., timeout=10)` |
| `.scrape(symbol=..., startPage=1, endPage=5, sort="popular")` | `.scrape(exchange=..., symbol=..., start_page=1, end_page=5, sort_by="popular")` |
| Returns `List[Dict]` | Returns `Dict` with `status/data/metadata/error` envelope |
| Returns `[]` on error | Returns `{"status": "failed", "data": None, "error": "..."}` |
| Raises on invalid args | Never raises from public methods |
