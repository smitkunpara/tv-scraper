# Markets Scraper

## Overview

The `Markets` scraper retrieves ranked stock lists from TradingView's scanner API across multiple market regions. Stocks can be sorted by market cap, volume, price change, closing price, or volatility.

## Quick Start

```python
from tv_scraper.scrapers.market_data import Markets

markets = Markets()
result = markets.get_top_stocks(market="america", sort_by="market_cap", limit=20)

for stock in result["data"]:
    print(stock["symbol"], stock["close"], stock["market_cap_basic"])
```

## API Reference

### Constructor

```python
Markets(export_result: bool = False, export_type: str = "json", timeout: int = 10)
```

| Parameter       | Type   | Default | Description                          |
|-----------------|--------|---------|--------------------------------------|
| `export_result` | `bool` | `False` | Whether to export results to file    |
| `export_type`   | `str`  | `"json"`| Export format (`"json"` or `"csv"`)  |
| `timeout`       | `int`  | `10`    | HTTP request timeout in seconds      |

### `get_top_stocks()`

```python
get_top_stocks(
    market: str = "america",
    sort_by: str = "market_cap",
    fields: Optional[List[str]] = None,
    sort_order: str = "desc",
    limit: int = 50,
) -> Dict[str, Any]
```

| Parameter    | Type             | Default        | Description                            |
|--------------|------------------|----------------|----------------------------------------|
| `market`     | `str`            | `"america"`    | Market region to scan                  |
| `sort_by`    | `str`            | `"market_cap"` | Sort criterion key                     |
| `fields`     | `List[str]|None` | `None`         | Scanner fields; defaults to built-in   |
| `sort_order` | `str`            | `"desc"`       | `"desc"` or `"asc"`                    |
| `limit`      | `int`            | `50`           | Maximum number of results              |

## Supported Markets

| Key         | Region          |
|-------------|-----------------|
| `america`   | United States   |
| `australia` | Australia       |
| `canada`    | Canada          |
| `germany`   | Germany         |
| `india`     | India           |
| `uk`        | United Kingdom  |
| `crypto`    | Cryptocurrency  |
| `forex`     | Forex           |
| `global`    | All markets     |

## Sort Criteria

| Key          | Scanner Field     | Description               |
|--------------|-------------------|---------------------------|
| `market_cap` | `market_cap_basic`| Market capitalization     |
| `volume`     | `volume`          | Trading volume            |
| `change`     | `change`          | Price change percentage   |
| `price`      | `close`           | Current closing price     |
| `volatility` | `Volatility.D`    | Daily volatility          |

## Default Fields

`name`, `close`, `change`, `change_abs`, `volume`, `Recommend.All`, `market_cap_basic`, `price_earnings_ttm`, `earnings_per_share_basic_ttm`, `sector`, `industry`

## Response Format

```json
{
    "status": "success",
    "data": [
        {
            "symbol": "NASDAQ:AAPL",
            "name": "Apple Inc.",
            "close": 150.25,
            "change": 2.5124,
            "change_abs": 3.68,
            "volume": 54231200,
            "Recommend.All": 0.5,
            "market_cap_basic": 2500000000000.0,
            "price_earnings_ttm": 28.5,
            "earnings_per_share_basic_ttm": 5.2,
            "sector": "Electronic Technology",
            "industry": "Telecommunications Equipment"
        },
        {
            "symbol": "NASDAQ:MSFT",
            "name": "Microsoft Corp.",
            "close": 310.15,
            "change": -1.2,
            "change_abs": -3.75,
            "volume": 28145000,
            "Recommend.All": 0.45,
            "market_cap_basic": 2300000000000.0,
            "price_earnings_ttm": 32.1,
            "earnings_per_share_basic_ttm": 9.5,
            "sector": "Technology Services",
            "industry": "Packaged Software"
        }
    ],
    "metadata": {
        "market": "america",
        "sort_by": "market_cap",
        "total": 2,
        "total_count": 5000
    },
    "error": null
}
```

## Examples

### Most Active Stocks by Volume

```python
result = markets.get_top_stocks(market="america", sort_by="volume", limit=15)
```

### Top Indian Stocks Ascending by Price

```python
result = markets.get_top_stocks(market="india", sort_by="price", sort_order="asc", limit=10)
```

### Custom Fields

```python
result = markets.get_top_stocks(
    fields=["name", "close", "volume", "market_cap_basic", "sector"],
    limit=10,
)
```

### Export to CSV

```python
markets = Markets(export_result=True, export_type="csv")
result = markets.get_top_stocks(market="uk", sort_by="market_cap")
```

## Migration from `tradingview_scraper`

| Old (`tradingview_scraper`)                        | New (`tv_scraper`)                                     |
|----------------------------------------------------|--------------------------------------------------------|
| `from tradingview_scraper.symbols.markets import Markets` | `from tv_scraper.scrapers.market_data import Markets` |
| `get_top_stocks(by="market_cap")`                  | `get_top_stocks(sort_by="market_cap")`                 |
| `get_top_stocks(columns=[...])`                    | `get_top_stocks(fields=[...])`                         |
| Raises `ValueError` on invalid input               | Returns error response (`status="failed"`)             |
| Response: `{"status", "data", "total", "totalCount"}` | Response: `{"status", "data", "metadata", "error"}`  |
| No `sort_order` parameter                          | `sort_order="desc"` (or `"asc"`) parameter added       |
