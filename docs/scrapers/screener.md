# Screener

## Overview

`Screener` posts scan payloads to TradingView's scanner endpoint and maps tabular
rows into dictionaries keyed by requested column names.

Request endpoint per call:

- `POST https://scanner.tradingview.com/{market}/scan`

The method returns the standardized response envelope used across the project
(`status`, `data`, `metadata`, `error`).

## Constructor

`Screener` does not override `__init__`, so it uses `BaseScraper` constructor
arguments directly:

```python
Screener(
    export_result: bool = False,
    export_type: str = "json",   # "json" or "csv"
    timeout: int = 10,             # integer in [1, 300]
    cookie: str | None = None,
)
```

| Parameter | Type | Default | Behavior |
|---|---|---|---|
| `export_result` | `bool` | `False` | When `True`, successful results are exported via `_export()`. |
| `export_type` | `str` | `"json"` | Must be `"json"` or `"csv"`; invalid values raise `ValueError` at init time. |
| `timeout` | `int` | `10` | Must be an integer in `[1, 300]`; invalid values raise `ValueError` at init time. |
| `cookie` | `str \| None` | `None` | Optional cookie header; if `None`, `TRADINGVIEW_COOKIE` env var is used. |

## Method

### `get_screener(...)`

```python
get_screener(
    market: Literal[
        "america", "australia", "canada", "germany", "india", "israel",
        "italy", "luxembourg", "mexico", "spain", "turkey", "uk",
        "crypto", "forex", "cfd", "futures", "bonds", "global",
    ] = "america",
    filters: list[dict[str, Any]] | None = None,
    fields: list[str] | None = None,
    sort_by: str | None = None,
    sort_order: Literal["asc", "desc"] = "desc",
    limit: int = 50,
    symbols: dict[str, Any] | None = None,
    filter2: dict[str, Any] | None = None,
) -> dict[str, Any]
```

| Parameter | Type | Default | Implementation behavior |
|---|---|---|---|
| `market` | `str` | `"america"` | Validated with `validate_choice` against `SUPPORTED_MARKETS`. |
| `filters` | `list[dict[str, Any]] \| None` | `None` | If not `None`, each entry is validated by `_validate_filter()` (see below). |
| `fields` | `list[str] \| None` | `None` | If `None`, market-specific defaults are used. Otherwise passed through as provided (no field-name validation). |
| `sort_by` | `str \| None` | `None` | If truthy, adds a `sort` block to payload. No validation of field name. |
| `sort_order` | `"asc" \| "desc"` | `"desc"` | Always validated, even when `sort_by` is not provided. |
| `limit` | `int` | `50` | Validated by `validate_range("limit", limit, 1, 10000)` then used in payload `range=[0, limit]`. |
| `symbols` | `dict[str, Any] \| None` | `None` | Not validated for schema/content. Included only when truthy. |
| `filter2` | `dict[str, Any] \| None` | `None` | If not `None`, validated by `_validate_filter2()` (must be dict with `operator`). Included only when truthy. |

## Validation Behavior

Validation performed directly in `get_screener`:

- `market` must be in supported markets.
- `sort_order` must be `"asc"` or `"desc"`.
- `limit` must be numeric and between `1` and `10000` (inclusive).

`filters` validation (`_validate_filter`):

- Each element must be a dictionary.
- Each dictionary must include keys `left` and `operation`.
- `operation` must be one of:
  `greater`, `less`, `egreater`, `eless`, `equal`, `nequal`, `in_range`,
  `not_in_range`, `above`, `below`, `crosses`, `crosses_above`,
  `crosses_below`, `has`, `has_none_of`.
- `right` is not validated by this method.

`filter2` validation (`_validate_filter2`):

- Must be a dictionary.
- Must include key `operator`.
- Other keys (such as `operands`, `expression`) are not validated.

No direct validation is applied to:

- `fields` content
- `sort_by` value
- `symbols` structure

## `filters`, `filter2`, and `symbols` Inclusion Rules

Payload inclusion uses truthiness checks after validation:

- `filters` is included only when `filters` is truthy.
  - `filters=[]` passes validation loop but is omitted from payload.
- `symbols` is included only when `symbols` is truthy.
  - `symbols={}` is omitted from payload.
- `filter2` is included only when `filter2` is truthy.
  - `filter2={"operator": "and"}` is included.

Common `symbols` patterns supported by TradingView (passed through by this
implementation without schema checks):

- `{"symbolset": ["SYML:SP;SPX"]}`
- `{"symbolset": ["SYML:NASDAQ;NDX"]}`
- `{"tickers": ["NASDAQ:AAPL", "NYSE:JPM"]}`

## `sort_by` and `limit` Behavior

- `sort_order` is validated on every call, regardless of whether sorting is
  requested.
- Sorting is applied only when `sort_by` is truthy; then payload includes:

```python
"sort": {
    "sortBy": sort_by,
    "sortOrder": sort_order,
}
```

- `limit` is not used for client-side slicing after response.
- The method sends `"range": [0, limit]` and returns whatever rows are
  returned by the API.

## Default Fields by Market Type

When `fields is None`, defaults come from `_get_default_fields(market)`:

### Stock-like markets (all except `crypto` and `forex`)

Used for:
`america`, `australia`, `canada`, `germany`, `india`, `israel`, `italy`,
`luxembourg`, `mexico`, `spain`, `turkey`, `uk`, `cfd`, `futures`, `bonds`,
`global`.

Fields:

- `name`
- `close`
- `change`
- `change_abs`
- `volume`
- `Recommend.All`
- `market_cap_basic`
- `price_earnings_ttm`
- `earnings_per_share_basic_ttm`

### `crypto`

- `name`
- `close`
- `change`
- `change_abs`
- `volume`
- `market_cap_calc`
- `Recommend.All`

### `forex`

- `name`
- `close`
- `change`
- `change_abs`
- `Recommend.All`

## Request Payload Shape

Base payload always sent:

```python
{
    "columns": resolved_fields,
    "options": {"lang": "en"},
    "range": [0, limit],
    "markets": [market],
}
```

Optional keys:

- `filter` (when `filters` is truthy)
- `sort` (when `sort_by` is truthy)
- `symbols` (when `symbols` is truthy)
- `filter2` (when `filter2` is truthy)

## Response Envelope and Mapping

All responses follow:

```python
{
    "status": "success" | "failed",
    "data": Any,
    "metadata": dict[str, Any],
    "error": str | None,
}
```

### Success behavior

- `status` = `"success"`
- `error` = `None`
- `data` = mapped rows from scanner response `data`
- `metadata` = captured call arguments (non-`None` only) plus:
  - `total`: `len(formatted_data)`
  - `total_available`: `json_response.get("totalCount", len(formatted_data))`

Row mapping uses `_map_scanner_rows(raw_items, resolved_fields)`:

- Each row starts with: `{"symbol": item.get("s", "")}`
- For each requested field index `i`, sets:
  - `row[field] = values[i]` when present
  - `row[field] = None` when missing

Example success envelope:

```python
{
    "status": "success",
    "data": [
        {
            "symbol": "NASDAQ:AAPL",
            "name": "Apple Inc.",
            "close": 187.21,
            "change": 1.1,
            "change_abs": 2.04,
            "volume": 51234567,
            "Recommend.All": 0.2,
            "market_cap_basic": 2800000000000.0,
            "price_earnings_ttm": 29.4,
            "earnings_per_share_basic_ttm": 6.37,
        }
    ],
    "metadata": {
        "market": "america",
        "sort_order": "desc",
        "limit": 50,
        "total": 1,
        "total_available": 8143,
    },
    "error": None,
}
```

### Failure behavior

- `status` = `"failed"`
- `error` = validation/network/unexpected error message
- `data` = `None` for current screener failure paths
- `metadata` = captured method arguments (non-`None`), without
  `total`/`total_available`

Representative failures:

- Invalid `market` / `sort_order` / `limit`
- Invalid `filters` item shape or operation
- Invalid `filter2` type or missing `operator`
- HTTP/network/captcha/parse errors returned by `_request()`
