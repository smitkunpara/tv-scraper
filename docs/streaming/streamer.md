# Streamer API

`Streamer` is a convenience class that combines:

- `CandleStreamer.get_candles()` via proxy
- `ForecastStreamer.get_forecast()` via proxy
- `stream_realtime_price()` implemented directly in `Streamer`

This page documents the behavior of `tv_scraper/streaming/streamer.py` exactly, including proxy and export side effects.

## Constructor

```python
from tv_scraper.streaming import Streamer

s = Streamer(
    export_result=False,
    export_type="json",   # "json" or "csv"
    cookie="<TRADINGVIEW_COOKIE>",
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `export_result` | `bool` | `False` | Enables export writing in both proxy methods and underlying streamers |
| `export_type` | `str` | `"json"` | Export format (`"json"` or `"csv"`) |
| `cookie` | `str \| None` | `None` | TradingView cookie used for JWT resolution in WebSocket connections |

## Method Summary

| Method | Kind | Returns |
|--------|------|---------|
| `get_candles()` | Proxy to `CandleStreamer.get_candles()` | Standard response envelope |
| `get_forecast()` | Proxy to `ForecastStreamer.get_forecast()` | Standard response envelope |
| `stream_realtime_price()` | Native `Streamer` implementation | `Generator[dict[str, Any], None, None]` |
| `get_available_indicators()` | Static passthrough | Standard response envelope |

## `get_candles()` (Proxy)

```python
result = s.get_candles(
    exchange="BINANCE",
    symbol="BTCUSDT",
    timeframe="1h",
    numb_candles=50,
    indicators=[("STD;RSI", "37.0")],
)
```

### Proxy behavior

1. Calls `self._candle_streamer.get_candles(...)` with the same arguments.
2. Returns that response object unchanged.
3. If `self.export_result` is `True` and returned `status == "success"`, it also calls:
   `self._export(result["data"], symbol, "get_candles")`.

### Validation and metadata origin

- Validation is performed inside `CandleStreamer.get_candles()`:
  - `verify_symbol_exchange(exchange, symbol)`
  - `validate_timeframe(timeframe)`
  - `validate_range("numb_candles", numb_candles, 1, 5000)`
- Standard response envelope is produced by the underlying method.
- Metadata is therefore sourced from the underlying `CandleStreamer` call.

### Response shape

```python
{
    "status": "success" | "failed",
    "data": {
        "ohlcv": [
            {
                "index": int,
                "timestamp": int,
                "open": float,
                "high": float,
                "low": float,
                "close": float,
                "volume": float  # optional if not present in packet
            }
        ],
        "indicators": {
            "STD;RSI": [
                {"index": int, "timestamp": int, "0": float, "1": float}
            ]
        }
    } | None,
    "metadata": {
        "exchange": str,
        "symbol": str,
        "timeframe": str,
        "numb_candles": int,
        # included only when provided:
        "indicators": list[tuple[str, str]]
    },
    "error": None | str
}
```

## `get_forecast()` (Proxy)

```python
result = s.get_forecast(exchange="NASDAQ", symbol="AAPL")
```

### Proxy behavior

1. Calls `self._forecast_streamer.get_forecast(exchange=..., symbol=...)`.
2. Returns that response object unchanged.
3. If `self.export_result` is `True` and returned `status == "success"`, it also calls:
   `self._export(result["data"], symbol, "forecast")`.

### Validation and metadata origin

- Validation is performed inside `ForecastStreamer.get_forecast()`:
  - `verify_symbol_exchange(exchange, symbol)`
  - Symbol type lookup via scanner endpoint (`fields=type`)
  - Forecast allowed only when `type == "stock"`
- On partial data, returned envelope is failed with `data` containing keys mapped from forecast sources and metadata including `available_output_keys`.

### Forecast output keys

`data` always uses these output keys:

- `revenue_currency`
- `previous_close_price`
- `average_price_target`
- `highest_price_target`
- `lowest_price_target`
- `median_price_target`
- `yearly_eps_data`
- `quarterly_eps_data`
- `yearly_revenue_data`
- `quarterly_revenue_data`

If any value is missing, status is `"failed"` and error starts with `"failed to fetch keys:"`.

## `stream_realtime_price()` (Generator)

```python
for tick in s.stream_realtime_price(exchange="BINANCE", symbol="BTCUSDT"):
    print(tick)
```

This method is not wrapped by `@catch_errors` and does not return the standard envelope.

### Execution model

- Return type: `Generator[dict[str, Any], None, None]`
- Validation and connection setup happen when the generator is iterated:
  - `verify_symbol_exchange(exchange, symbol)`
  - `format_symbol(exchange, normalized_symbol)`
  - `self.connect()`

### Session and subscription flow

`self.connect()` creates `StreamHandler`, which initializes:

1. `set_auth_token`
2. `set_locale`
3. `chart_create_session`
4. `quote_create_session`
5. `quote_set_fields`
6. `quote_hibernate_all`

Then `stream_realtime_price()` sends:

1. `quote_add_symbols` with resolved symbol payload
2. `quote_fast_symbols`
3. `resolve_symbol` on chart session (`"sds_sym_1"`)
4. `create_series` for `"sds_1"` with timeframe mapped from `TIMEFRAMES["1m"]` (fallback `"1"`) and series length `1`

### Yielded dict shapes

#### From `qsd` packets

Yielded only when `lp` exists:

```python
{
    "exchange": v.get("exchange", exchange),
    "symbol": v.get("short_name", symbol),
    "price": v.get("lp"),
    "volume": v.get("volume"),
    "change": v.get("ch"),
    "change_percent": v.get("chp"),
    "high": v.get("high_price"),
    "low": v.get("low_price"),
    "open": v.get("open_price"),
    "prev_close": v.get("prev_close_price"),
    "bid": v.get("bid"),
    "ask": v.get("ask"),
}
```

#### From `du` packets

For each entry in `p[1]["sds_1"]["s"]` where `len(entry["v"]) >= 5`:

```python
{
    "exchange": exchange,
    "symbol": symbol,
    "price": close_price,
    "volume": volume_or_none,
    "change": close_price - last_price if last_price is not None else None,
    "change_percent": ((change / last_price) * 100) if last_price not in (None, 0) else (0 if last_price == 0 else None),
    "high": entry["v"][2],
    "low": entry["v"][3],
    "open": entry["v"][1],
    "prev_close": None,
    "bid": None,
    "ask": None,
}
```

`last_price` is updated from both `qsd` (`lp`) and `du` (`close_price`).

### Generator termination

The method has no explicit stop condition. It ends when `handler.receive_packets()` ends (for example, WebSocket close/error).

## `get_available_indicators()`

Static method that directly returns `fetch_available_indicators()`.

```python
result = Streamer.get_available_indicators()
```

Behavior:

- No use of instance state
- Returns standard envelope from `fetch_available_indicators()`
- Metadata is empty unless that utility changes

## Export Behavior (Exact)

When `export_result=True`:

- `get_candles()` can attempt export twice on success:
  1. inside `CandleStreamer.get_candles()`
  2. again inside `Streamer.get_candles()`
- `get_forecast()` can attempt export twice on success:
  1. inside `ForecastStreamer.get_forecast()`
  2. again inside `Streamer.get_forecast()`

Export categories used by the proxy methods are:

- `get_candles`
- `forecast`

Filenames are generated under `export/` by `generate_export_filepath(...)`.

## Metadata and Error Nuances

1. `get_candles()` and `get_forecast()` are decorated with `@catch_errors`, but on normal execution they return the delegated streamer's envelope unchanged.
2. If an exception happens in proxy-only code (for example, proxy export call), proxy-level `@catch_errors` can replace the delegated response with a new failed envelope.
3. Metadata values in success/failure envelopes come from the delegated methods in the normal path.
4. `stream_realtime_price()` does not use envelope wrapping; validation/network errors can propagate during iteration.
