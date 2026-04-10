# Market Movers

## Overview

`MarketMovers` wraps TradingView scanner endpoints for predefined "movers"
categories (gainers, losers, most-active, etc.) and returns the standardized
response envelope used across `tv_scraper`.

Public method:

```python
get_market_movers(
    market: str = "stocks-usa",
    category: str = "gainers",
    fields: list[str] | None = None,
    limit: int = 50,
    language: str = "en",
) -> dict[str, Any]
```

## Constructor

`MarketMovers` does not override `BaseScraper.__init__`, so it accepts:

```python
MarketMovers(
    export_result: bool = False,
    export_type: str = "json",
    timeout: int = 10,
    cookie: str | None = None,
)
```

| Parameter | Type | Default | Behavior |
|---|---|---|---|
| `export_result` | `bool` | `False` | Export mapped rows after successful fetch. |
| `export_type` | `str` | `"json"` | Must be `"json"` or `"csv"`. |
| `timeout` | `int` | `10` | Request timeout used by `_request()`. |
| `cookie` | `str \| None` | `None` | Optional TradingView cookie header value. |

## Supported Markets and Categories

### Markets

| `market` value | Scanner segment | Request URL |
|---|---|---|
| `stocks-usa` | `america` | `https://scanner.tradingview.com/america/scan` |
| `stocks-uk` | `uk` | `https://scanner.tradingview.com/uk/scan` |
| `stocks-india` | `india` | `https://scanner.tradingview.com/india/scan` |
| `stocks-australia` | `australia` | `https://scanner.tradingview.com/australia/scan` |
| `stocks-canada` | `canada` | `https://scanner.tradingview.com/canada/scan` |
| `crypto` | `crypto` | `https://scanner.tradingview.com/crypto/scan` |
| `forex` | `forex` | `https://scanner.tradingview.com/forex/scan` |
| `bonds` | `bonds` | `https://scanner.tradingview.com/bonds/scan` |
| `futures` | `futures` | `https://scanner.tradingview.com/futures/scan` |

### Categories

Stock markets (`market.startswith("stocks")`) allow:

- `gainers`
- `losers`
- `most-active`
- `penny-stocks`
- `pre-market-gainers`
- `pre-market-losers`
- `after-hours-gainers`
- `after-hours-losers`

Non-stock markets (`crypto`, `forex`, `bonds`, `futures`) allow only:

- `gainers`
- `losers`
- `most-active`

## Validation Rules (Execution Order)

`get_market_movers()` validates in this exact order:

1. `limit`: `validators.validate_range("limit", limit, 1, 1000)`
2. `market`: `validators.validate_choice("market", market, SUPPORTED_MARKETS)`
3. `category`: allowed set depends on whether market starts with `"stocks"`
4. `language`: `validators.validate_language(language)`
5. `fields`:
   - If `fields is None`, defaults are used by market.
   - Then `validators.validate_fields(resolved_fields, resolved_fields, "fields")` is called.

`fields` validation therefore enforces structure/type (list/tuple of strings), but
does not restrict names to a global allowlist because the allowed set is the
same list passed in.

## Default Fields by Market

### Stock markets (`stocks-*`)

- `name`
- `close`
- `change`
- `change_abs`
- `volume`
- `market_cap_basic`
- `price_earnings_ttm`
- `earnings_per_share_basic_ttm`
- `logoid`
- `description`

### Crypto (`crypto`)

- `name`
- `close`
- `change`
- `change_abs`
- `volume`
- `market_cap_calc`
- `logoid`
- `description`

### Forex (`forex`)

- `name`
- `close`
- `change`
- `change_abs`
- `logoid`
- `description`

### Bonds and futures (`bonds`, `futures`)

- `name`
- `close`
- `change`
- `change_abs`
- `logoid`
- `description`

## Filter Rules

`payload["filter"]` is built by `_get_filter_conditions(market, category)`.

### Market filter

If `market.startswith("stocks")`, a market filter is always added:

```json
{"left": "market", "operation": "equal", "right": "<segment>"}
```

No `market` filter is added for `crypto`, `forex`, `bonds`, or `futures`.

### Category filters

| Category | Extra filter |
|---|---|
| `penny-stocks` | `{"left": "close", "operation": "less", "right": 5}` |
| `gainers` | `{"left": "change", "operation": "greater", "right": 0}` |
| `pre-market-gainers` | `{"left": "change", "operation": "greater", "right": 0}` |
| `after-hours-gainers` | `{"left": "change", "operation": "greater", "right": 0}` |
| `losers` | `{"left": "change", "operation": "less", "right": 0}` |
| `pre-market-losers` | `{"left": "change", "operation": "less", "right": 0}` |
| `after-hours-losers` | `{"left": "change", "operation": "less", "right": 0}` |
| `most-active` | No category-specific extra filter |

## Sort Rules

`payload["sort"]` is selected by `_CATEGORY_SORT`:

| Category | `sortBy` | `sortOrder` |
|---|---|---|
| `gainers` | `change` | `desc` |
| `losers` | `change` | `asc` |
| `most-active` | `volume` | `desc` |
| `penny-stocks` | `volume` | `desc` |
| `pre-market-gainers` | `change` | `desc` |
| `pre-market-losers` | `change` | `asc` |
| `after-hours-gainers` | `change` | `desc` |
| `after-hours-losers` | `change` | `asc` |

Note: `_get_sort_config()` has a fallback to `{"sortBy": "change", "sortOrder": "desc"}` for unknown categories, but public validation rejects unknown categories before that fallback is used.

## Request Payload Schema

The request is:

- Method: `POST`
- URL: market-specific scanner URL from table above
- JSON body:

```json
{
  "columns": ["<field1>", "<field2>", "..."],
  "filter": [
    {
      "left": "<field>",
      "operation": "<operation>",
      "right": "<value>"
    }
  ],
  "options": {
    "lang": "<language>"
  },
  "range": [0, <limit>],
  "sort": {
    "sortBy": "<change|volume>",
    "sortOrder": "<asc|desc>"
  }
}
```

## Output Mapping

`ScannerScraper._map_scanner_rows(raw_items, fields)` maps scanner rows as:

- Input row shape: `{"s": "EXCHANGE:SYMBOL", "d": [v1, v2, ...]}`
- Output row shape:

```python
{
    "symbol": item.get("s", ""),
    fields[0]: d[0] if present else None,
    fields[1]: d[1] if present else None,
    ...
}
```

Behavior details:

- Missing `s` becomes `""`.
- If `d` has fewer values than requested fields, missing values are `None`.
- `totalCount` in metadata comes from `json_response.get("totalCount", 0)`.
- `raw_items` comes from `json_response.get("data", [])`.

## Response Envelope

### Success

```python
{
    "status": "success",
    "data": [
        {
            "symbol": "NASDAQ:AAPL",
            "name": "Apple Inc.",
            "close": 175.5,
            "change": 2.5
        }
    ],
    "metadata": {
        "market": "stocks-usa",
        "category": "gainers",
        "limit": 10,
        "language": "en",
        "total": 1,
        "totalCount": 1
    },
    "error": None
}
```

### Failure

```python
{
    "status": "failed",
    "data": None,
    "metadata": {
        "market": "stocks-usa",
        "category": "gainers",
        "limit": 10,
        "language": "en"
    },
    "error": "<message>"
}
```

Metadata notes:

- Metadata starts from bound method arguments captured by `@catch_errors`.
- `fields` appears in metadata only when explicitly passed (not when `None`).
- On success, method-specific metadata (`total`, `totalCount`) is appended.

## Failure Behavior

Public method behavior is "no-raise": errors are returned in envelope form.

Failure paths:

1. Validation failures (`market`, `category`, `limit`, `language`, `fields` type)
   return `status="failed"`, `data=None`, and a validation error string.
2. Request-layer failures from `_request()` are forwarded via `_error_response()`:
   - captcha challenge
   - network/HTTP errors
   - empty server response
   - JSON parse errors
3. Non-dict API response returns:
   - `error`: `"Invalid response format: expected dictionary."`
4. Any unexpected runtime exception is caught by `@catch_errors` and returned as:
   - `error`: `"Unexpected error: <exception>"`

Non-failure edge behavior:

- Empty API data (`{"data": [], "totalCount": 0}`) is treated as success with
  `data=[]`, `metadata.total=0`, and `metadata.totalCount=0`.
