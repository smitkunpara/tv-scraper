# Minds Community Discussions

## Overview

The `Minds` scraper fetches community-generated discussions from TradingView's Minds feature, including questions, trading ideas, and sentiment.

## API

```python
from tv_scraper.scrapers.social import Minds

scraper = Minds(export_result=False, export_type="json")
result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL", limit=50)
```

### Constructor

| Parameter       | Type   | Default   | Description                          |
|----------------|--------|-----------|--------------------------------------|
| `export_result` | `bool` | `False`   | Whether to export results to file    |
| `export_type`   | `str`  | `"json"`  | Export format: `"json"` or `"csv"`   |
| `timeout`       | `int`  | `10`      | HTTP request timeout in seconds      |

### `get_minds()`

| Parameter  | Type           | Default | Description                                  |
|-----------|----------------|---------|----------------------------------------------|
| `exchange` | `str`          | —       | Exchange name (e.g. `"NASDAQ"`)              |
| `symbol`   | `str`          | —       | Trading symbol (e.g. `"AAPL"`)              |
| `limit`    | `Optional[int]`| `None`  | Max results to retrieve. `None` = fetch all  |

## Response Format

All responses use the standard envelope:

```json
{
  "status": "success",
  "data": [
    {
      "text": "AAPL looking bullish today",
      "url": "https://www.tradingview.com/minds/abc123",
      "author": {
        "username": "trader1",
        "profile_url": "https://www.tradingview.com/u/trader1/",
        "is_broker": false
      },
      "created": "2025-01-07 12:00:00",
      "total_likes": 10,
      "total_comments": 5
    },
    ...
  ],
  "metadata": {
    "total": 42,
    "pages": 2,
    "symbol_info": {"short_name": "AAPL", "exchange": "NASDAQ"}
  },
  "error": null
}
```

### Mind Item Schema

Each item in the `data` array contains:

```json
{
  "text": "AAPL looking bullish today",
  "url": "https://www.tradingview.com/minds/abc123",
  "author": {
    "username": "trader1",
    "profile_url": "https://www.tradingview.com/u/trader1/",
    "is_broker": false
  },
  "created": "2025-01-07 12:00:00",
  "total_likes": 10,
  "total_comments": 5
}
```

## Examples

### Basic Usage

```python
from tv_scraper.scrapers.social import Minds

scraper = Minds()
result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

if result["status"] == "success":
    for mind in result["data"]:
        print(f"{mind['author']['username']}: {mind['text'][:60]}...")
```

### With Limit

```python
result = scraper.get_minds(exchange="BITSTAMP", symbol="BTCUSD", limit=20)
print(f"Retrieved {result['metadata']['total']} discussions")
```

### With Export

```python
scraper = Minds(export_result=True, export_type="csv")
result = scraper.get_minds(exchange="NYSE", symbol="TSLA")
```

## Migration from `tradingview_scraper`

| Old (`tradingview_scraper`)                          | New (`tv_scraper`)                                   |
|------------------------------------------------------|------------------------------------------------------|
| `from tradingview_scraper.symbols.minds import Minds` | `from tv_scraper.scrapers.social import Minds`       |
| `minds.get_minds(symbol="NASDAQ:AAPL")`              | `minds.get_minds(exchange="NASDAQ", symbol="AAPL")`  |
| Response: `{"status", "data", "total", "pages", ...}` | Response: `{"status", "data", "metadata", "error"}`  |
| Empty results → `{"status": "failed"}`                | Empty results → `{"status": "success", "data": []}`  |

### Key Changes

1. **Separate `exchange` and `symbol` parameters** — no more combined `"EXCHANGE:SYMBOL"` strings.
2. **Standard response envelope** — all responses have `status`, `data`, `metadata`, `error`.
3. **Empty results are success** — an empty list is valid data, not an error.
4. **Exchange validation** — invalid exchanges are caught before making HTTP calls.
