# Symbol Markets

Find all markets and exchanges where a symbol is traded.

## Quick Start

```python
from tv_scraper.scrapers.screening import SymbolMarkets

sm = SymbolMarkets()
result = sm.scrape(symbol="AAPL")

for item in result["data"]:
    print(item["symbol"], item["exchange"], item["close"])
```

## API Reference

### `SymbolMarkets(export_result=False, export_type="json", timeout=10)`

| Parameter       | Type   | Default | Description                  |
|-----------------|--------|---------|------------------------------|
| `export_result` | `bool` | `False` | Export results to file       |
| `export_type`   | `str`  | `"json"`| Export format: `"json"` / `"csv"` |
| `timeout`       | `int`  | `10`    | HTTP request timeout (seconds) |

### `scrape(symbol, fields=None, scanner="global", limit=150)`

| Parameter | Type             | Default          | Description                            |
|-----------|------------------|------------------|----------------------------------------|
| `symbol`  | `str`            | *(required)*     | Symbol to search for (e.g. `"AAPL"`)   |
| `fields`  | `list[str]|None` | `DEFAULT_FIELDS` | Columns to retrieve                    |
| `scanner` | `str`            | `"global"`       | Scanner region                         |
| `limit`   | `int`            | `150`            | Maximum number of results              |

**Supported scanners:** `global`, `america`, `crypto`, `forex`, `cfd`

**Default fields:** `name`, `close`, `change`, `change_abs`, `volume`, `exchange`, `type`, `description`, `currency`, `market_cap_basic`

### Response Format

```python
{
    "status": "success",        # or "failed"
    "data": [                   # list of dicts (None on error)
        {
            "symbol": "NASDAQ:AAPL",
            "name": "AAPL",
            "close": 150.25,
            "exchange": "NASDAQ",
            ...
        }
    ],
    "metadata": {
        "scanner": "global",
        "total": 5,
        "total_available": 5,
    },
    "error": None               # error message string on failure
}
```

## Examples

### Find all exchanges for a symbol

```python
sm = SymbolMarkets()
result = sm.scrape(symbol="AAPL")

print(f"AAPL is traded on {result['metadata']['total']} markets")
for item in result["data"]:
    print(f"  {item['symbol']} — {item['exchange']}")
```

### Search crypto markets only

```python
result = sm.scrape(symbol="BTCUSD", scanner="crypto", limit=50)
```

### Custom fields

```python
result = sm.scrape(
    symbol="TSLA",
    fields=["name", "close", "volume", "exchange"],
    scanner="america",
)
```

### Export results

```python
sm = SymbolMarkets(export_result=True, export_type="csv")
result = sm.scrape(symbol="AAPL")
# File saved to export/ directory
```

## Migration from `tradingview_scraper`

| Old (`tradingview_scraper`)             | New (`tv_scraper`)                          |
|-----------------------------------------|---------------------------------------------|
| `from tradingview_scraper.symbols.symbol_markets import SymbolMarkets` | `from tv_scraper.scrapers.screening import SymbolMarkets` |
| `scrape(symbol, columns=...)` | `scrape(symbol, fields=...)` |
| `scanner='global'` (same) | `scanner="global"` (same) |
| Returns `{"status", "data", "total", "totalCount"}` | Returns `{"status", "data", "metadata", "error"}` |
| `SCANNER_ENDPOINTS` dict | Uses `SCANNER_URL` constant + `SUPPORTED_SCANNERS` set |
| `DEFAULT_COLUMNS` | `DEFAULT_FIELDS` |
