# Screener

## Overview

The `Screener` module screens financial instruments across 18 markets (stocks, crypto, forex, bonds, futures, CFDs) using the TradingView scanner API with custom filters, sorting, and field selection.

## Quick Start

```python
from tv_scraper.scrapers.screening import Screener

screener = Screener()

# Basic US stock screen
result = screener.screen(market="america", limit=10)

# Screen with filters and sorting
result = screener.screen(
    market="america",
    filters=[
        {"left": "close", "operation": "greater", "right": 100},
        {"left": "volume", "operation": "greater", "right": 1000000},
    ],
    sort_by="volume",
    sort_order="desc",
    limit=20,
)

for stock in result["data"]:
    print(f"{stock['symbol']}: ${stock['close']} - Vol: {stock['volume']}")
```

## API Reference

### Constructor

```python
Screener(
    export_result: bool = False,
    export_type: str = "json",
    timeout: int = 10,
)
```

| Parameter       | Type   | Default | Description                          |
|----------------|--------|---------|--------------------------------------|
| `export_result` | `bool` | `False` | Whether to export results to file.   |
| `export_type`   | `str`  | `"json"`| Export format: `"json"` or `"csv"`.  |
| `timeout`       | `int`  | `10`    | HTTP timeout in seconds.             |

### `screen()` Method

```python
screen(
    market: str = "america",
    filters: Optional[List[Dict[str, Any]]] = None,
    fields: Optional[List[str]] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
    limit: int = 50,
) -> Dict[str, Any]
```

| Parameter    | Type                        | Default     | Description                              |
|-------------|-----------------------------|-------------|------------------------------------------|
| `market`     | `str`                       | `"america"` | Market to screen.                        |
| `filters`    | `List[Dict]` or `None`      | `None`      | Filter conditions.                       |
| `fields`     | `List[str]` or `None`       | `None`      | Columns to retrieve (market defaults).   |
| `sort_by`    | `str` or `None`             | `None`      | Field to sort by.                        |
| `sort_order` | `str`                       | `"desc"`    | Sort direction: `"asc"` or `"desc"`.     |
| `limit`      | `int`                       | `50`        | Maximum number of results.               |

## Response Format

All responses use the standardized envelope:

```json
{
    "status": "success",
    "data": [
        {
            "symbol": "NASDAQ:AAPL",
            "name": "Apple Inc.",
            "close": 150.25,
            "change": 2.512,
            "change_abs": 3.68,
            "volume": 54231000,
            "market_cap_basic": 2500000000000.0,
            "price_earnings_ttm": 28.5,
            "earnings_per_share_basic_ttm": 5.2,
            "sector": "Electronic Technology"
        },
        {
            "symbol": "NYSE:TSLA",
            "name": "Tesla, Inc.",
            "close": 210.5,
            "change": 1.15,
            "change_abs": 2.4,
            "volume": 85000000,
            "market_cap_basic": 600000000000.0,
            "price_earnings_ttm": 65.2,
            "earnings_per_share_basic_ttm": 3.2,
            "sector": "Consumer Durables"
        }
    ],
    "metadata": {
        "market": "america",
        "total": 2,
        "total_available": 1500
    },
    "error": null
}
```

## Supported Markets

| Key          | Description        |
|--------------|--------------------|
| `america`    | US Stocks          |
| `australia`  | Australian Stocks  |
| `canada`     | Canadian Stocks    |
| `germany`    | German Stocks      |
| `india`      | Indian Stocks      |
| `israel`     | Israeli Stocks     |
| `italy`      | Italian Stocks     |
| `luxembourg` | Luxembourg Stocks  |
| `mexico`     | Mexican Stocks     |
| `spain`      | Spanish Stocks     |
| `turkey`     | Turkish Stocks     |
| `uk`         | UK Stocks          |
| `crypto`     | Cryptocurrencies   |
| `forex`      | Forex Pairs        |
| `cfd`        | CFDs               |
| `futures`    | Futures            |
| `bonds`      | Bonds              |
| `global`     | Global Markets     |

## Filter Operations

| Operation       | Description          | Example                                                        |
|----------------|----------------------|----------------------------------------------------------------|
| `greater`       | Greater than         | `{"left": "close", "operation": "greater", "right": 100}`     |
| `less`          | Less than            | `{"left": "close", "operation": "less", "right": 50}`         |
| `egreater`      | Equal or greater     | `{"left": "volume", "operation": "egreater", "right": 1e6}`   |
| `eless`         | Equal or less        | `{"left": "pe", "operation": "eless", "right": 20}`           |
| `equal`         | Equal to             | `{"left": "change", "operation": "equal", "right": 0}`        |
| `nequal`        | Not equal            | `{"left": "change", "operation": "nequal", "right": 0}`       |
| `in_range`      | Within range         | `{"left": "close", "operation": "in_range", "right": [50, 200]}` |
| `not_in_range`  | Outside range        | `{"left": "close", "operation": "not_in_range", "right": [10, 50]}` |
| `above`         | Above value          | `{"left": "close", "operation": "above", "right": 150}`       |
| `below`         | Below value          | `{"left": "close", "operation": "below", "right": 50}`        |
| `crosses`       | Crosses value        | `{"left": "close", "operation": "crosses", "right": 100}`     |
| `crosses_above` | Crosses above        | `{"left": "close", "operation": "crosses_above", "right": 200}` |
| `crosses_below` | Crosses below        | `{"left": "close", "operation": "crosses_below", "right": 50}` |
| `has`           | Contains value       | `{"left": "name", "operation": "has", "right": "Apple"}`      |
| `has_none_of`   | Contains none of     | `{"left": "name", "operation": "has_none_of", "right": ["Bank"]}` |

## Default Fields by Market

**Stock markets** (america, uk, etc.): `name`, `close`, `change`, `change_abs`, `volume`, `Recommend.All`, `market_cap_basic`, `price_earnings_ttm`, `earnings_per_share_basic_ttm`

**Crypto**: `name`, `close`, `change`, `change_abs`, `volume`, `market_cap_calc`, `Recommend.All`

**Forex**: `name`, `close`, `change`, `change_abs`, `Recommend.All`

## Examples

### Crypto Screening

```python
result = screener.screen(
    market="crypto",
    filters=[{"left": "market_cap_calc", "operation": "greater", "right": 1e9}],
    fields=["name", "close", "market_cap_calc", "change"],
    limit=50,
)
```

### Range Filtering

```python
result = screener.screen(
    market="america",
    filters=[{"left": "close", "operation": "in_range", "right": [50, 200]}],
    sort_by="close",
    sort_order="asc",
)
```

### Export to CSV

```python
screener = Screener(export_result=True, export_type="csv")
result = screener.screen(
    market="america",
    fields=["name", "close", "volume", "market_cap_basic"],
    limit=30,
)
# File saved automatically
```

## Migration from Old API

| Old (`tradingview_scraper`)              | New (`tv_scraper`)                       |
|------------------------------------------|------------------------------------------|
| `from tradingview_scraper.symbols.screener import Screener` | `from tv_scraper.scrapers.screening import Screener` |
| `screener.screen(columns=[...])`         | `screener.screen(fields=[...])`          |
| Raises `ValueError` on invalid market    | Returns error response envelope          |
| `result["totalCount"]`                   | `result["metadata"]["total_available"]`  |
| `result["total"]`                        | `result["metadata"]["total"]`            |
| `result["status"] == "failed"`           | Same, but envelope always has all 4 keys |
