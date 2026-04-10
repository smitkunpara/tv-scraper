# Markets Scraper

## Overview

`Markets` fetches ranked stock rows from the TradingView scanner endpoint for a
selected market region.

- HTTP method: `POST`
- URL template: `https://scanner.tradingview.com/{market}/scan`

The scraper always applies built-in stock filters and returns the standard
response envelope (`status`, `data`, `metadata`, `error`).

## Constructor

`Markets` does not override `__init__`, so it uses `BaseScraper.__init__`.

```python
from tv_scraper.scrapers.market_data import Markets

scraper = Markets(
        export_result=False,
        export_type="json",
        timeout=10,
        cookie=None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `export_result` | `bool` | `False` | Export successful results when `True`. |
| `export_type` | `str` | `"json"` | Export format: `"json"` or `"csv"`. |
| `timeout` | `int` | `10` | Request timeout in seconds. Must be an integer between `1` and `300`. |
| `cookie` | `str \| None` | `None` | Optional TradingView cookie. Falls back to `TRADINGVIEW_COOKIE` env var when available. |

## Method Signature

```python
get_markets(
        market: MARKET_LITERAL = "america",
        sort_by: MARKET_SORT_LITERAL = "market_cap",
        fields: list[str] | None = None,
        sort_order: SORT_ORDER_LITERAL = "desc",
        limit: int = 50,
) -> dict[str, Any]
```

`MARKET_LITERAL` values:

- `america`
- `australia`
- `canada`
- `germany`
- `india`
- `uk`
- `crypto`
- `forex`
- `global`

`MARKET_SORT_LITERAL` values:

- `market_cap`
- `volume`
- `change`
- `price`
- `volatility`

`SORT_ORDER_LITERAL` values:

- `asc`
- `desc`

## Parameters And Validation

| Parameter | Type | Default | Validation / Behavior |
|-----------|------|---------|------------------------|
| `market` | `MARKET_LITERAL` | `"america"` | `validators.validate_choice("market", market, VALID_MARKETS)` |
| `sort_by` | `MARKET_SORT_LITERAL` | `"market_cap"` | `validators.validate_choice("sort_by", sort_by, SORT_CRITERIA.keys())` |
| `fields` | `list[str] \| None` | `None` | If `None`, uses `DEFAULT_FIELDS`. No explicit `validate_fields(...)` call in this method. |
| `sort_order` | `SORT_ORDER_LITERAL` | `"desc"` | `validators.validate_choice("sort_order", sort_order, ["asc", "desc"])` |
| `limit` | `int` | `50` | `validators.validate_range("limit", limit, 1, 1000)` |

Validation errors are handled by `@catch_errors` and returned as failed envelopes
instead of raising to callers.

## Sorting Options

`sort_by` maps to scanner `sort.sortBy` as follows:

| `sort_by` | Scanner field |
|-----------|---------------|
| `market_cap` | `market_cap_basic` |
| `volume` | `volume` |
| `change` | `change` |
| `price` | `close` |
| `volatility` | `Volatility.D` |

## Built-In Filters

This scraper always sends these filters (not user configurable):

```python
[
        {"left": "type", "operation": "equal", "right": "stock"},
        {"left": "market_cap_basic", "operation": "nempty"},
]
```

## Default Fields

Used when `fields=None`:

`name`, `close`, `change`, `change_abs`, `volume`, `Recommend.All`, `market_cap_basic`, `price_earnings_ttm`, `earnings_per_share_basic_ttm`, `sector`, `industry`

## Request Payload Schema

`get_markets` builds this payload:

```python
payload = {
        "columns": used_fields,
        "options": {"lang": "en"},
        "range": [0, limit],
        "sort": {
                "sortBy": SORT_CRITERIA[sort_by],
                "sortOrder": sort_order,
        },
        "filter": STOCK_FILTERS,
}
```

Then it posts to:

```python
url = f"{SCANNER_URL}/{market}/scan"
```

## Response Schema

### Success

```json
{
    "status": "success",
    "data": [
        {
            "symbol": "NASDAQ:AAPL",
            "name": "Apple Inc.",
            "close": 190.5,
            "change": 1.2
        }
    ],
    "metadata": {
        "market": "america",
        "sort_by": "market_cap",
        "sort_order": "desc",
        "limit": 50,
        "total": 1,
        "total_count": 5000
    },
    "error": null
}
```

### Failed

```json
{
    "status": "failed",
    "data": null,
    "metadata": {
        "market": "america",
        "sort_by": "market_cap",
        "sort_order": "desc",
        "limit": 50
    },
    "error": "error message"
}
```

## Metadata Behavior

Metadata comes from two sources:

1. `@catch_errors` captures bound method arguments with defaults.
2. `_success_response(..., total=..., total_count=...)` adds result metadata.

Important detail:

- Arguments with value `None` are omitted from metadata by the decorator.
- Because of this, `fields` appears in metadata only when explicitly provided as
    a non-`None` list.

## Row Mapping Behavior

Scanner rows are mapped with `_map_scanner_rows(items, used_fields)`:

- Input row shape: `{"s": "EXCHANGE:SYMBOL", "d": [v1, v2, ...]}`
- Output row shape: `{"symbol": "EXCHANGE:SYMBOL", <field1>: v1, ...}`
- If `d` has fewer values than requested fields, missing field values are set to
    `None`.

## Failure Behavior

`get_markets` returns `status="failed"` in these cases:

1. Validation failure:
     - invalid `market`, `sort_by`, `sort_order`
     - invalid `limit` (outside `1..1000`)

2. Request failure from `_request(...)`:
     - network / HTTP error
     - captcha detection
     - JSON parse error
     - empty response body

3. Empty scanner data:
     - if `json_data.get("data", [])` is empty, returns:
         `"No data found for market: {market}"`

4. Unexpected runtime error:
     - handled by `@catch_errors` as
         `"Unexpected error: <message>"`

All failures return `data: null`.

## Examples

### Default Usage

```python
from tv_scraper.scrapers.market_data import Markets

markets = Markets()
result = markets.get_markets()
```

### Sort By Volume

```python
result = markets.get_markets(market="america", sort_by="volume", limit=15)
```

### Ascending Price

```python
result = markets.get_markets(
        market="india",
        sort_by="price",
        sort_order="asc",
        limit=10,
)
```

### Custom Fields

```python
result = markets.get_markets(
        fields=["name", "close", "volume", "market_cap_basic", "sector"],
        limit=10,
)
```

### Export To CSV

```python
markets = Markets(export_result=True, export_type="csv")
result = markets.get_markets(market="uk", sort_by="market_cap")
```
