# Options

## Overview

The `Options` scraper fetches option-chain rows from TradingView's options scanner endpoint.

It exposes two public methods:

- `get_options_by_expiry(...)`: filter by expiration and root
- `get_options_by_strike(...)`: filter by strike

Both methods return the standardized envelope:

- `status`: `"success"` or `"failed"`
- `data`: list of mapped option rows on success, `None` on failure
- `metadata`: captured call arguments plus scraper-added metadata keys
- `error`: `None` on success, error string on failure

## Constructor

```python
Options(
    export_result: bool = False,
    export_type: str = "json",   # "json" or "csv"
    timeout: int = 10,
)
```

## Endpoints Used

### Validation endpoints (via `validators.verify_options_symbol`)

Before querying options data, both public methods validate exchange/symbol and options availability:

1. Symbol-exchange existence check:
   - `GET https://scanner.tradingview.com/symbol?symbol={EXCHANGE}%3A{SYMBOL}&fields=market&no_404=false`
2. Options availability check:
   - `GET https://symbol-search.tradingview.com/symbol_search/v3/?text={SYMBOL}&exchange={EXCHANGE}&lang=en&search_type=undefined&only_has_options=true&domain=production`

### Options data endpoint

- `POST https://scanner.tradingview.com/options/scan2?label-product=symbols-options`
- Body format: JSON payload with `columns`, `filter`, and `index_filters`

## Default and Allowed Columns

If `columns` is omitted (`None`), the scraper uses:

`ask`, `bid`, `currency`, `delta`, `expiration`, `gamma`, `iv`, `option-type`, `pricescale`, `rho`, `root`, `strike`, `theoPrice`, `theta`, `vega`, `bid_iv`, `ask_iv`

When `columns` is provided, each value must be one of the above strings.

## Methods

### `get_options_by_expiry(exchange, symbol, expiration, root, columns=None)`

Fetch option rows filtered by expiration and root for one underlying symbol.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `exchange` | `str` | — | Exchange slug, e.g. `"BSE"` |
| `symbol` | `str` | — | Underlying symbol slug, e.g. `"SENSEX"` |
| `expiration` | `int` | — | Expiration value passed directly to API filter |
| `root` | `str` | — | Root value passed directly to API filter |
| `columns` | `list[str] \| None` | `None` | Optional output fields list |

Validation behavior:

- Calls `validators.verify_options_symbol(exchange, symbol)` first
- If `columns` is not `None`, calls `validators.validate_fields(columns, list(VALID_OPTION_COLUMNS), "columns")`
- No additional explicit runtime validation is performed for `expiration` or `root`

Request payload shape:

```python
{
    "columns": columns_or_default,
    "filter": [
        {"left": "type", "operation": "equal", "right": "option"},
        {"left": "expiration", "operation": "equal", "right": expiration},
        {"left": "root", "operation": "equal", "right": root},
    ],
    "index_filters": [
        {"name": "underlying_symbol", "values": [f"{exchange}:{symbol}"]}
    ],
}
```

Notes:

- The underlying value uses the incoming `exchange` and `symbol` exactly as provided.
- Success metadata includes `filter_value=<expiration>` and `total`.

### `get_options_by_strike(exchange, symbol, strike, columns=None)`

Fetch option rows filtered by strike for one underlying symbol.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `exchange` | `str` | — | Exchange slug, e.g. `"BSE"` |
| `symbol` | `str` | — | Underlying symbol slug, e.g. `"SENSEX"` |
| `strike` | `int \| float` | — | Strike value passed directly to API filter |
| `columns` | `list[str] \| None` | `None` | Optional output fields list |

Validation behavior:

- Calls `validators.verify_options_symbol(exchange, symbol)` first
- If `columns` is not `None`, validates with `validators.validate_fields(..., "columns")`
- Enforces `strike` type with `isinstance(strike, (int, float))`
- On invalid type, raises `ValidationError("Invalid strike value: {strike!r}. Must be int or float.")`

Request payload shape:

```python
{
    "columns": columns_or_default,
    "filter": [
        {"left": "type", "operation": "equal", "right": "option"},
        {"left": "strike", "operation": "equal", "right": strike},
    ],
    "index_filters": [
        {"name": "underlying_symbol", "values": [f"{exchange}:{symbol}"]}
    ],
}
```

Notes:

- Success metadata includes `filter_value=<strike>` and `total`.

## Response Schema

### Success envelope

```python
{
    "status": "success",
    "data": [
        {
            "symbol": "EXCHANGE:OPTION_SYMBOL",
            # plus one key per field name in response["fields"]
            # for example: "strike", "bid", "ask", "delta", ...
        }
    ],
    "metadata": {
        # Captured method arguments except None values,
        # plus:
        "filter_value": 20260219,  # or strike value
        "total": 14,
    },
    "error": None,
}
```

### Error envelope

```python
{
    "status": "failed",
    "data": None,
    "metadata": {
        # Captured method arguments; may also include filter_value
    },
    "error": "...",
}
```

Data mapping details:

- Reads `fields = response["fields"]` and `symbols = response["symbols"]`
- Each symbol row is expected as `{"s": symbol_name, "f": [values...]}`
- Output row starts as `{"symbol": item.get("s")}`
- For each index `i` in `fields`, sets `row[fields[i]] = values[i]` if value exists
- Non-dict entries in `symbols` are skipped

## Metadata Behavior

Metadata is built by combining:

1. Captured method arguments from the decorator (`exchange`, `symbol`, method-specific args, and `columns` only if not `None`)
2. Scraper-added keys from `_execute_request`:
   - Always on `_execute_request` path: `filter_value`
   - On success only: `total`

Per method:

| Method | Always present from args | Conditionally present | Added by scraper |
|--------|---------------------------|------------------------|------------------|
| `get_options_by_expiry` | `exchange`, `symbol`, `expiration`, `root` | `columns` (if provided) | `filter_value`, `total` (success only) |
| `get_options_by_strike` | `exchange`, `symbol`, `strike` | `columns` (if provided) | `filter_value`, `total` (success only) |

## Error Behavior

### Validation and decorator-caught errors

These are returned as failed envelopes with `data=None` and captured input metadata:

- Invalid exchange/symbol/options availability from `verify_options_symbol`
	(including 403 or missing match from options search)
- Invalid `columns` from `validate_fields`
- Invalid strike type from method check
- Any unexpected exception as `"Unexpected error: ..."`

### Request and response-shape errors inside `_execute_request`

| Condition | Returned error string |
|-----------|-----------------------|
| `_request` returns error containing `"404"` | `Options chain not found for symbol '{exchange}:{symbol}'. This symbol may not have options available on TradingView.` |
| `_request` returns any other error | Original error message from `_request` |
| Response is not a dict | `Invalid API response format: expected a dictionary` |
| `fields` or `symbols` is not a list | `Invalid API response: 'fields' and 'symbols' must be lists` |
| `symbols` is empty | `No options found for symbol '{exchange}:{symbol}'. This symbol may not have options available on TradingView.` |

## Export Behavior

If `export_result=True`, successful mapped `data` is exported through the base exporter with:

- `data_category="options"`
- `symbol="{exchange}_{symbol}_{filter_value}"`
- format selected by `export_type` (`json` or `csv`)
