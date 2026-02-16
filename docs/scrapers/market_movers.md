# Market Movers

## Overview

The `MarketMovers` scraper retrieves top gainers, losers, most-active
instruments, penny stocks, and pre-market / after-hours movers from TradingView's
scanner API.

## Quick Start

```python
from tv_scraper.scrapers.screening import MarketMovers

movers = MarketMovers()
result = movers.scrape(market="stocks-usa", category="gainers", limit=20)

for stock in result["data"]:
    print(f"{stock['symbol']}: {stock['change']}%")
```

## API Reference

### Constructor

```python
MarketMovers(
    export_result: bool = False,
    export_type: str = "json",
    timeout: int = 10,
)
```

| Parameter       | Type   | Default | Description                        |
|-----------------|--------|---------|------------------------------------|
| `export_result` | `bool` | `False` | Export results to a file.          |
| `export_type`   | `str`  | `"json"`| Export format: `"json"` or `"csv"`.|
| `timeout`       | `int`  | `10`    | HTTP request timeout in seconds.   |

### `scrape()`

```python
scrape(
    market: str = "stocks-usa",
    category: str = "gainers",
    fields: Optional[List[str]] = None,
    limit: int = 50,
) -> Dict[str, Any]
```

| Parameter  | Type              | Default        | Description                              |
|------------|-------------------|----------------|------------------------------------------|
| `market`   | `str`             | `"stocks-usa"` | Market to query (see supported list).    |
| `category` | `str`             | `"gainers"`    | Movers category (see supported list).    |
| `fields`   | `List[str]|None`  | `None`         | Columns to retrieve; `None` = defaults. |
| `limit`    | `int`             | `50`           | Maximum number of results.               |

### Supported Markets

`stocks-usa`, `stocks-uk`, `stocks-india`, `stocks-australia`, `stocks-canada`,
`crypto`, `forex`, `bonds`, `futures`.

### Supported Categories

**Stock markets:** `gainers`, `losers`, `most-active`, `penny-stocks`,
`pre-market-gainers`, `pre-market-losers`, `after-hours-gainers`,
`after-hours-losers`.

**Non-stock markets:** `gainers`, `losers`, `most-active`.

### Default Fields

`name`, `close`, `change`, `change_abs`, `volume`, `market_cap_basic`,
`price_earnings_ttm`, `earnings_per_share_basic_ttm`, `logoid`, `description`.

## Response Format

All responses follow the standard envelope:

```python
{
    "status": "success",          # or "failed"
    "data": [                     # list of dicts, or None on failure
        {
            "symbol": "NASDAQ:AAPL",
            "name": "Apple Inc.",
            "close": 190.5,
            "change": 3.2,
            ...
        }
    ],
    "metadata": {
        "market": "stocks-usa",
        "category": "gainers",
        "total": 20,
    },
    "error": None,                # error message string on failure
}
```

## Examples

### Losers and Most Active

```python
movers = MarketMovers()

losers = movers.scrape(category="losers", limit=10)
active = movers.scrape(category="most-active", limit=10)
```

### Pre-Market / After-Hours

```python
pre_gainers = movers.scrape(category="pre-market-gainers")
ah_losers   = movers.scrape(category="after-hours-losers")
```

### Custom Fields

```python
result = movers.scrape(
    fields=["name", "close", "change", "volume"],
    limit=5,
)
```

### Multiple Markets

```python
for mkt in ["stocks-usa", "crypto", "forex"]:
    r = movers.scrape(market=mkt, category="gainers", limit=5)
    print(f"{mkt}: {len(r['data'])} results")
```

### Export to CSV

```python
movers = MarketMovers(export_result=True, export_type="csv")
movers.scrape(market="stocks-usa", category="gainers")
# File saved to export/ directory
```

## Migration from `tradingview_scraper`

| Old (`tradingview_scraper`)                         | New (`tv_scraper`)                                |
|-----------------------------------------------------|---------------------------------------------------|
| `from tradingview_scraper.symbols.market_movers import MarketMovers` | `from tv_scraper.scrapers.screening import MarketMovers` |
| Raises `ValueError` on invalid market/category      | Returns error response (never raises)             |
| Response: `{"status", "data", "total"}`             | Response: `{"status", "data", "metadata", "error"}` |
| `result["total"]`                                   | `result["metadata"]["total"]`                     |
| No `timeout` parameter                              | Constructor accepts `timeout`                     |
