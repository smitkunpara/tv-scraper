# Symbol Markets

## Overview

`SymbolMarkets` finds all exchanges/markets where a symbol appears in TradingView scanner results.

It sends a scanner request to:

```text
{SCANNER_URL}/{scanner}/scan
```

with a name-match filter on the parsed symbol value.

## Quick Start

```python
from tv_scraper.scrapers.screening import SymbolMarkets

sm = SymbolMarkets()
result = sm.get_symbol_markets(symbol="AAPL")

for item in result["data"]:
    print(item["symbol"], item["exchange"], item["close"])
```

## API Reference

### Constructor

```python
SymbolMarkets(
    export_result: bool = False,
    export_type: str = "json",
    timeout: int = 10,
    cookie: str | None = None,
)
```

| Parameter       | Type          | Default | Description |
|----------------|---------------|---------|-------------|
| `export_result` | `bool`        | `False` | Export successful results to file. |
| `export_type`   | `str`         | `"json"` | Export format: `"json"` or `"csv"`. |
| `timeout`       | `int`         | `10`    | HTTP timeout in seconds. |
| `cookie`        | `str \| None` | `None`  | Optional TradingView cookie (falls back to `TRADINGVIEW_COOKIE` env var). |

### `get_symbol_markets()`

```python
get_symbol_markets(
    symbol: str,
    fields: list[str] | None = None,
    scanner: Literal["global", "america", "crypto", "forex", "cfd"] = "global",
    limit: int = 150,
) -> dict[str, Any]
```

| Parameter | Type | Default | Implementation behavior |
|-----------|------|---------|--------------------------|
| `symbol` | `str` | *(required)* | Search symbol. If it contains `:`, only the part after the first `:` is used for search/validation (for example, `"NASDAQ:AAPL"` searches for `"AAPL"`). |
| `fields` | `list[str] \| None` | `None` | If `None`, uses `DEFAULT_FIELDS`. If provided, values are passed through directly (no local field-name validation in this method). |
| `scanner` | `"global" \| "america" \| "crypto" \| "forex" \| "cfd"` | `"global"` | Validated with `validate_choice` against `SUPPORTED_SCANNERS`. |
| `limit` | `int` | `150` | Validated with `validate_range("limit", limit, 1, 1000)`. |

### Supported scanners

`global`, `america`, `crypto`, `forex`, `cfd`

### Default fields

`name`, `close`, `change`, `change_abs`, `volume`, `exchange`, `type`, `description`, `currency`, `market_cap_basic`

## Request Payload

After symbol parsing and validation, the method sends this payload:

```python
{
    "filter": [
        {"left": "name", "operation": "match", "right": search_symbol},
    ],
    "columns": resolved_fields,
    "options": {"lang": "en"},
    "range": [0, limit],
}
```

Notes:

- `search_symbol` is parsed from `symbol` (`EXCHANGE:SYMBOL` -> `SYMBOL`).
- The filter always uses `left="name"` and `operation="match"`.
- The request method is `POST`.

## Response Mapping

Raw scanner rows are mapped with `_map_scanner_rows(items, resolved_fields)`.

Input row shape from TradingView:

```python
{"s": "EXCHANGE:SYMBOL", "d": [value0, value1, ...]}
```

Mapped output row:

```python
{
    "symbol": item.get("s", ""),
    field_0: d[0],
    field_1: d[1],
    ...
}
```

If `d` has fewer values than requested fields, missing field values are set to `None`.

If mapped rows are empty, the method returns:

```python
{
    "status": "failed",
    "data": None,
    "error": f"No markets found for symbol: {symbol}",
    "metadata": {...}
}
```

## Metadata Behavior

`get_symbol_markets` is decorated with `@catch_errors`.

That means metadata starts from bound method arguments (excluding `None` values), then success-specific values are merged in.

### What appears in metadata

- Always: `symbol`, `scanner`, `limit`
- Included only when provided: `fields`
- Added on success: `total`, `total_available`

Important details:

- `symbol` in metadata is the original argument value, not the parsed `search_symbol`.
- `total` is `len(formatted_data)`.
- `total_available` is `json_response.get("totalCount", len(formatted_data))`.

## Response Envelope

Success shape:

```python
{
    "status": "success",
    "data": [
        {
            "symbol": "NASDAQ:AAPL",
            "name": "AAPL",
            "close": 150.25,
            "exchange": "NASDAQ",
            # ...other requested fields
        }
    ],
    "metadata": {
        "symbol": "AAPL",
        "scanner": "global",
        "limit": 150,
        "total": 5,
        "total_available": 5,
    },
    "error": None,
}
```

Failure shape:

```python
{
    "status": "failed",
    "data": None,
    "metadata": {
        "symbol": "AAPL",
        "scanner": "global",
        "limit": 150,
        # fields included only when explicitly provided
    },
    "error": "...",
}
```

## Examples

### Basic search

```python
sm = SymbolMarkets()
result = sm.get_symbol_markets(symbol="AAPL")
```

### Input with exchange prefix

```python
# Parses search symbol as "AAPL" for filtering/validation
result = sm.get_symbol_markets(symbol="NASDAQ:AAPL")
```

### Scanner selection

```python
result = sm.get_symbol_markets(symbol="BTCUSD", scanner="crypto", limit=50)
```

### Custom fields

```python
result = sm.get_symbol_markets(
    symbol="TSLA",
    fields=["name", "close", "volume", "exchange"],
    scanner="america",
)
```

### Export

```python
sm = SymbolMarkets(export_result=True, export_type="csv")
result = sm.get_symbol_markets(symbol="AAPL")
# Saved under export/ when status is success
```
