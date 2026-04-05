# Market Movers

## Overview

The `MarketMovers` scraper retrieves top gainers, losers, most-active
instruments, penny stocks, and pre-market / after-hours movers from TradingView's
scanner API.

## Quick Start

```python
from tv_scraper.scrapers.screening import MarketMovers

movers = MarketMovers()
result = movers.get_market_movers(market="stocks-usa", category="gainers", limit=20)

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

### `get_market_movers()`

```python
get_market_movers(
    market: str = "stocks-usa",
    category: str = "gainers",
    fields: Optional[List[str]] = None,
    limit: int = 50,
    language: str = "en",
) -> Dict[str, Any]
```

| Parameter  | Type              | Default        | Description                              |
|------------|-------------------|----------------|------------------------------------------|
| `market`   | `str`             | `"stocks-usa"` | Market to query (see supported list).    |
| `category` | `str`             | `"gainers"`    | Movers category (see supported list).    |
| `fields`   | `List[str]|None`  | `None`         | Columns to retrieve; `None` = defaults. |
| `limit`    | `int`             | `50`           | Maximum results (1-1000).                |
| `language` | `str`             | `"en"`         | Language code (e.g., "en", "es", "de"). |

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
        "totalCount": 4500,       # total available in category
    },
    "error": None,                # error message string on failure
}
```

## Validation Errors

The method validates inputs and returns error responses for:

- **Invalid limit**: Must be an integer between 1 and 1000
- **Unsupported market**: Must be one of the supported markets
- **Unsupported category**: Must be valid for the selected market
- **Invalid language**: Must be a valid language code
- **Invalid fields**: Must be a list of strings

## Examples

### Losers and Most Active

```python
movers = MarketMovers()

losers = movers.get_market_movers(category="losers", limit=10)
active = movers.get_market_movers(category="most-active", limit=10)
```

### Pre-Market / After-Hours

```python
pre_gainers = movers.get_market_movers(category="pre-market-gainers")
ah_losers   = movers.get_market_movers(category="after-hours-losers")
```

### Custom Fields

```python
result = movers.get_market_movers(
    fields=["name", "close", "change", "volume"],
    limit=5,
)
```

### Multiple Markets

```python
for mkt in ["stocks-usa", "crypto", "forex"]:
    r = movers.get_market_movers(market=mkt, category="gainers", limit=5)
    print(f"{mkt}: {len(r['data'])} results")
```

### Export to CSV

```python
movers = MarketMovers(export_result=True, export_type="csv")
movers.get_market_movers(market="stocks-usa", category="gainers")
# File saved to export/ directory
```
