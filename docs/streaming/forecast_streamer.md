# ForecastStreamer API

The `ForecastStreamer` class captures forecast fields from TradingView quote stream (`qsd` packets) and returns them in a standardized response envelope.

## Installation

```python
from tv_scraper.streaming import ForecastStreamer
```

## Constructor

```python
fs = ForecastStreamer(
    export_result=False,
    export_type="json",
    cookie="<TRADINGVIEW_COOKIE>",
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `export_result` | `bool` | `False` | Whether to export successful forecast results |
| `export_type` | `str` | `"json"` | Export format: `"json"` or `"csv"` |
| `cookie` | `str \| None` | `None` | TradingView cookie (used for JWT resolution in `connect()`) |

## Method

### `get_forecast(exchange, symbol)`

```python
result = fs.get_forecast(exchange="NASDAQ", symbol="AAPL")
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `exchange` | `str` | Yes | Exchange name |
| `symbol` | `str` | Yes | Symbol name |

## Runtime Flow (Exact Behavior)

1. Validates and normalizes symbol via `validators.verify_symbol_exchange(exchange, symbol)`.
2. Builds `exchange_symbol` with `format_symbol(exchange, normalized_symbol)`.
3. Resolves instrument type using HTTP GET to `f"{SCANNER_URL}/symbol"` with params:
   - `symbol=<EXCHANGE:SYMBOL>`
   - `fields=type`
   - `no_404=false`
4. Enforces stock-only access:
   - If resolved type is not `"stock"`, returns failed response with error:
     - `forecast is not available for this symbol because it is type: <type>`
5. Opens WebSocket handler through `connect()`.
6. Sends quote-stream setup messages in this order:
   - `set_data_quality`, `["low"]`
   - `quote_set_fields`, `[quote_session, *capture_fields]`
   - `quote_hibernate_all`, `[quote_session]`
   - `quote_add_symbols`, `[quote_session, f"={resolve_symbol_json}"]`
   - `quote_fast_symbols`, `[quote_session, exchange_symbol]`
7. Captures packets from `handler.receive_packets()` and accumulates snapshot values.

## Packet Capture Behavior

- Every packet increments `packet_count` and is appended to internal `raw_packets`.
- Only packets with `m == "qsd"` are parsed for forecast values.
- A `qsd` packet is parsed only when:
  - `p` exists with at least 2 items,
  - `p[1]` is a dict,
  - `p[1]["v"]` is a dict.
- Parsed values are merged with `snapshot.update(values)`.
- Non-`qsd` packets are ignored for field extraction.
- `raw_packets` is internal only and is not included in the method response.

## Required Output Key Mapping

The method always produces this fixed output schema by mapping output keys to TradingView source keys.

| Output key | Source key in snapshot |
|------------|------------------------|
| `revenue_currency` | `fundamental_currency_code` |
| `previous_close_price` | `regular_close` |
| `average_price_target` | `price_target_average` |
| `highest_price_target` | `price_target_high` |
| `lowest_price_target` | `price_target_low` |
| `median_price_target` | `price_target_median` |
| `yearly_eps_data` | `earnings_fy_h` |
| `quarterly_eps_data` | `earnings_fq_h` |
| `yearly_revenue_data` | `revenues_fy_h` |
| `quarterly_revenue_data` | `revenues_fq_h` |

`capture_fields` sent to `quote_set_fields` is `sorted(set(source_keys))` from the mapping above.

## Stop Conditions

The receive loop stops when either condition is met:

1. All required output keys are found with non-`None` values.
2. Timeout branch triggers when `packet_count > 15` (checked inside the parsed `qsd` branch).

On timeout, a warning is logged with currently found keys.

## Response Semantics

All responses follow:

```python
{
    "status": "success" | "failed",
    "data": <payload or None>,
    "metadata": {...},
    "error": <string or None>
}
```

### Success Response

When all required keys are present and non-`None`:

```python
{
    "status": "success",
    "data": {
        "revenue_currency": "USD",
        "previous_close_price": 114.5,
        "average_price_target": 162.8,
        "highest_price_target": 185.0,
        "lowest_price_target": 145.0,
        "median_price_target": 160.0,
        "yearly_eps_data": [...],
        "quarterly_eps_data": [...],
        "yearly_revenue_data": [...],
        "quarterly_revenue_data": [...]
    },
    "metadata": {
        "exchange": "NASDAQ",
        "symbol": "AAPL",
        "available_output_keys": [
            "average_price_target",
            "highest_price_target",
            "lowest_price_target",
            "median_price_target",
            "previous_close_price",
            "quarterly_eps_data",
            "quarterly_revenue_data",
            "revenue_currency",
            "yearly_eps_data",
            "yearly_revenue_data"
        ]
    },
    "error": null
}
```

### Failed Response: Missing Keys

If any required output key is missing (`None` in final cleaned payload):

- `status` is `"failed"`
- `data` is still returned (all 10 output keys, with missing ones set to `None`)
- `metadata.available_output_keys` contains only non-`None` keys
- `error` is exactly:
  - `failed to fetch keys: <comma-separated-missing-keys>`

```python
{
    "status": "failed",
    "data": {
        "revenue_currency": "USD",
        "previous_close_price": null,
        "average_price_target": 162.8,
        "highest_price_target": 185.0,
        "lowest_price_target": 145.0,
        "median_price_target": 160.0,
        "yearly_eps_data": null,
        "quarterly_eps_data": [...],
        "yearly_revenue_data": null,
        "quarterly_revenue_data": [...]
    },
    "metadata": {
        "exchange": "NASDAQ",
        "symbol": "AAPL",
        "available_output_keys": [
            "average_price_target",
            "highest_price_target",
            "lowest_price_target",
            "median_price_target",
            "quarterly_eps_data",
            "quarterly_revenue_data",
            "revenue_currency"
        ]
    },
    "error": "failed to fetch keys: previous_close_price, yearly_eps_data, yearly_revenue_data"
}
```

### Failed Response: Non-Stock Symbol

```python
{
    "status": "failed",
    "data": null,
    "metadata": {
        "exchange": "BINANCE",
        "symbol": "BTCUSDT"
    },
    "error": "forecast is not available for this symbol because it is type: crypto"
}
```

### Failed Response: Unexpected Errors

Unexpected runtime exceptions (for example symbol-type lookup failures) are wrapped by `@catch_errors`:

```python
{
    "status": "failed",
    "data": null,
    "metadata": {
        "exchange": "NASDAQ",
        "symbol": "AAPL"
    },
    "error": "Unexpected error: <exception message>"
}
```

## Output Metadata

`metadata` always starts with method arguments captured by `@catch_errors` and is then extended by method-level metadata:

- Always includes: `exchange`, `symbol`
- On success and missing-keys failure: includes `available_output_keys`

## Export Behavior

- Export runs only on successful completion (all required keys present).
- Export call is `_export(cleaned_data, symbol, "forecast")`.

## Data Field Notes

- Values are passed through from TradingView snapshot values.
- No additional schema transformation is applied beyond source-to-output key mapping.
- Any field may be `None` when unavailable in the captured snapshot.
