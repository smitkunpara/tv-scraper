# Options

## Overview

The Options scraper fetches option-chain rows from TradingView's options scanner endpoint.

It exposes one public method:

- get_options(...): filter by expiration, strike, or both

The method returns the standardized envelope:

- status: success or failed
- data: list of mapped option rows on success, None on failure
- metadata: captured call arguments plus scraper-added metadata keys
- error: None on success, error string on failure

## Constructor

```python
Options(
    export_result: bool = False,
    export_type: str = "json",   # "json" or "csv"
    timeout: int = 10,
)
```

## Endpoints Used

### Validation endpoints (via validators.verify_options_symbol)

Before querying options data, the public method validates exchange and symbol and verifies options availability:

1. Symbol-exchange existence check:
   - GET https://scanner.tradingview.com/symbol?symbol={EXCHANGE}%3A{SYMBOL}&fields=market&no_404=false
2. Options availability check:
   - GET https://symbol-search.tradingview.com/symbol_search/v3/?text={SYMBOL}&exchange={EXCHANGE}&lang=en&search_type=undefined&only_has_options=true&domain=production

### Options data endpoint

- POST https://scanner.tradingview.com/options/scan2?label-product=symbols-options
- Body format: JSON payload with columns, filter, and index_filters

## Default and Allowed Columns

If columns is omitted (None), the scraper uses:

ask, bid, currency, delta, expiration, gamma, iv, option-type, pricescale, rho, root, strike, theoPrice, theta, vega, bid_iv, ask_iv

When columns is provided, each value must be one of the above strings.

### IDE Literal Support For Columns

The method uses a Literal-based type alias for better autocomplete in IDEs:

```python
from tv_scraper.core.validation_data import OPTION_COLUMN_LITERAL

columns: list[OPTION_COLUMN_LITERAL] = ["strike", "bid", "ask", "iv"]
```

## Method

### get_options(exchange, symbol, expiration=None, strike=None, columns=None)

Fetch option rows for one underlying symbol using expiration filter, strike filter, or both.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| exchange | str | - | Exchange slug, for example BSE |
| symbol | str | - | Underlying symbol slug, for example SENSEX |
| expiration | int \| None | None | Expiration date in YYYYMMDD format |
| strike | int \| float \| None | None | Strike value |
| columns | list[OPTION_COLUMN_LITERAL] \| None | None | Optional output fields list with IDE suggestions |

Validation behavior:

- Calls validators.verify_options_symbol(exchange, symbol)
- If columns is not None, validates with validators.validate_fields(columns, list(VALID_OPTION_COLUMNS), "columns")
- Requires at least one of expiration or strike
- Validates expiration using validators.validate_yyyymmdd_date("expiration", expiration)
    - Format must be YYYYMMDD (8 digits)
    - Month must satisfy 0 < MM <= 12
    - Day must satisfy 0 < DD <= 31
    - Date must be a real calendar date (for example, 20260231 is rejected)
- Validates strike as int or float when provided

Request payload shape:

```python
{
    "columns": columns_or_default,
    "filter": [
        {"left": "type", "operation": "equal", "right": "option"},
        # Optional:
        {"left": "expiration", "operation": "equal", "right": expiration},
        {"left": "strike", "operation": "equal", "right": strike},
    ],
    "index_filters": [
        {"name": "underlying_symbol", "values": [f"{exchange}:{symbol}"]}
    ],
}
```

Filter combinations:

- expiration only: filters chain by expiration
- strike only: filters chain by strike
- expiration + strike: applies both filters, returning the specific strike at the specific expiration when available

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
        "filter_value": 20260219,  # or strike value, or {"expiration": ..., "strike": ...}
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

- Reads fields = response["fields"] and symbols = response["symbols"]
- Each symbol row is expected as {"s": symbol_name, "f": [values...]}
- Output row starts as {"symbol": item.get("s")}
- For each index i in fields, sets row[fields[i]] = values[i] if value exists
- Non-dict entries in symbols are skipped

## Metadata Behavior

Metadata combines:

1. Captured method arguments from the decorator (exchange, symbol, expiration, strike, columns)
2. Scraper-added keys from _execute_request:
   - Always on _execute_request path: filter_value
   - On success only: total

## Error Behavior

### Validation and decorator-caught errors

These are returned as failed envelopes with data=None and captured input metadata:

- Invalid exchange/symbol/options availability from verify_options_symbol
- Invalid columns from validate_fields
- Missing both filters (expiration and strike)
- Invalid expiration type/format/date values
- Invalid strike type
- Any unexpected exception as Unexpected error: ...

### Request and response-shape errors inside _execute_request

| Condition | Returned error string |
|-----------|-----------------------|
| _request returns error containing 404 | Options chain not found for symbol '{exchange}:{symbol}'. This symbol may not have options available on TradingView. |
| _request returns any other error | Original error message from _request |
| Response is not a dict | Invalid API response format: expected a dictionary |
| fields or symbols is not a list | Invalid API response: 'fields' and 'symbols' must be lists |
| symbols is empty | No options found for symbol '{exchange}:{symbol}'. This symbol may not have options available on TradingView. |

## Export Behavior

If export_result=True, successful mapped data is exported through the base exporter with:

- data_category="options"
- symbol suffix including selected filter context:
  - exchange_symbol_exp_<expiration> when only expiration is used
  - exchange_symbol_<strike> when only strike is used
  - exchange_symbol_exp_<expiration>_strike_<strike> when both are used
- format selected by export_type (json or csv)
