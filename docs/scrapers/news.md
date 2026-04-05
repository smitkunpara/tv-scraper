# News Scraper

## Overview

Scrape headlines and full article content from TradingView news providers.

## API Reference

### Constructor

```python
scraper = News(export_result=False, export_type="json", timeout=10, cookie=None)
```

| Parameter       | Type   | Default  | Description                        |
|-----------------|--------|----------|------------------------------------|
| `export_result` | bool   | `False`  | Export results to file             |
| `export_type`   | str    | `"json"` | `"json"` or `"csv"`               |
| `timeout`       | int    | `10`     | HTTP request timeout in seconds    |
| `cookie`        | str    | `None`   | TradingView cookie for captcha     |

### `get_news_headlines()`

```python
get_news_headlines(
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

**Validation:**
- Exchange and symbol are verified against TradingView's symbol database
- `sort_by` must be one of: `latest`, `oldest`, `most_urgent`, `least_urgent`
- `section` must be one of: `all`, `esg`, `press_release`, `financial_statement`
- `provider` must be a valid news provider (case-insensitive)
- `area` must be a valid area code
- `language` must be a valid language code

Code:

```python
result = scraper.get_news_headlines(
    exchange="NASDAQ",
    symbol="AAPL",
    provider="reuters",
    sort_by="latest",
)

print(result)
```

Output:

```json
{
  "status": "success",
  "data": [
    {
      "id": "tag:reuters.com,2026:newsml_L4N3Z9104:0",
      "title": "Apple shares rise on strong guidance",
      "shortDescription": "Apple reported stronger than expected guidance...",
      "published": 1705350000,
      "storyPath": "/news/story_12345-apple-shares-rise/"
    }
  ],
  "metadata": {
    "exchange": "NASDAQ",
    "symbol": "AAPL",
    "total": 1
  },
  "error": null
}
```

Other details:

- `metadata.total` reflects the number of returned items in this response.
- Use the headline `id` with `get_news_content()`.

### `get_news_content()`

```python
get_news_content(
    story_id: str,
    language: str = "en",
) -> Dict[str, Any]
```

| Parameter    | Type         | Default | Description                                    |
|--------------|--------------|---------|------------------------------------------------|
| `story_id`   | str          | —       | Story ID from news API (e.g. `"tag:reuters.com,2026:newsml_L4N3Z9104:0"`) |
| `language`   | str          | `"en"`  | Language code (e.g. `"en"`, `"fr"`)            |

**Validation:**
- `story_id` cannot be empty or whitespace-only
- `language` must be a valid language code

Code:

```python
result = scraper.get_news_content(
    story_id="tag:reuters.com,2026:newsml_L4N3Z9104:0",
    language="en",
)
```

Output:

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
