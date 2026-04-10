# CandleStreamer API

The `CandleStreamer` class streams OHLCV candles and optional indicator series from TradingView over WebSocket.

This page documents the current implementation in `tv_scraper/streaming/candle_streamer.py`.

## Installation

```python
from tv_scraper.streaming import CandleStreamer
```

## Constructor

```python
cs = CandleStreamer(
    export_result=False,
    export_type="json",  # "json" or "csv"
    cookie="<TRADINGVIEW_COOKIE>",
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `export_result` | `bool` | `False` | Whether to export successful results |
| `export_type` | `str` | `"json"` | Export format (`"json"` or `"csv"`) |
| `cookie` | `str \| None` | `None` | TradingView cookie used for JWT resolution and private indicator access |

## Method

### `get_candles()`

```python
result = cs.get_candles(
    exchange="BINANCE",
    symbol="BTCUSDT",
    timeframe="1h",
    numb_candles=10,
    indicators=[("STD;RSI", "37.0")],
)
```

Signature:

```python
def get_candles(
    exchange: EXCHANGE_LITERAL,
    symbol: str,
    timeframe: str = "1m",
    numb_candles: int = 10,
    indicators: list[tuple[str, str]] | None = None,
) -> dict[str, Any]
```

## Validation Rules

Validation happens at the beginning of `get_candles()`:

1. `verify_symbol_exchange(exchange, symbol)`
2. `validate_timeframe(timeframe)`
3. `validate_range("numb_candles", numb_candles, 1, 5000)`

### Exchange and symbol verification

- `exchange` must be a non-empty string and a known exchange.
- `symbol` must be a non-empty string.
- The `exchange:symbol` pair is verified against TradingView scanner endpoint.
- On success, both exchange and symbol are normalized to uppercase.

### Timeframe validation

- Must be one of the keys in `TIMEFRAMES`:
  - `"1m"`, `"5m"`, `"15m"`, `"30m"`, `"1h"`, `"2h"`, `"4h"`, `"1d"`, `"1w"`, `"1M"`

### Candle count validation

- `numb_candles` must be numeric and within `1..5000`.

### Indicator input validation

- There is no upfront validator for indicator IDs/versions in `get_candles()`.
- Validation effectively happens when metadata is fetched in `_add_indicators()`.

## Timeframe Behavior

`_add_symbol_to_sessions()` maps the user timeframe to TradingView series interval:

| Input timeframe | Sent interval |
|----------------|---------------|
| `"1m"` | `"1"` |
| `"5m"` | `"5"` |
| `"15m"` | `"15"` |
| `"30m"` | `"30"` |
| `"1h"` | `"60"` |
| `"2h"` | `"120"` |
| `"4h"` | `"240"` |
| `"1d"` | `"1D"` |
| `"1w"` | `"1W"` |
| `"1M"` | `"1M"` |

Implementation detail: mapping uses `TIMEFRAMES.get(timeframe, "1")`. Because timeframe is validated first, the fallback `"1"` should not be used in normal flow.

## Indicator Handling

When `indicators` is truthy (`bool(indicators)`):

1. `_add_indicators()` runs once per `(script_id, script_version)` tuple.
2. Metadata is fetched from pine-facade using `fetch_indicator_metadata(...)`.
3. A chart study ID is assigned as `st{9 + idx}` (for example, `st9`, `st10`, ...).
4. Study ID is mapped back to indicator script ID in `self.study_id_to_name_map`.
5. `create_study` is sent to WebSocket for each indicator.

Indicator extraction from stream:

- Only `du` packets are inspected.
- Only entries whose key starts with `st` and exists in `study_id_to_name_map` are used.
- Each indicator row is shaped as:

```python
{
    "index": item["i"],
    "timestamp": item["v"][0],
    "0": item["v"][1],
    "1": item["v"][2],
    # ... more numeric string keys if present
}
```

The output indicator dictionary is keyed by script ID (for example `"STD;RSI"`), not by study ID.

## Stop Conditions and Timeout Behavior

The receive loop processes packets from `handler.receive_packets()` and updates:

- `ohlcv_data` when a `timescale_update` packet is received
- `indicator_data` when a `du` packet contains tracked studies

Loop stop conditions:

1. Success stop: `len(ohlcv_data) >= numb_candles` and indicator requirement is met.
2. Timeout stop: when packet index `i > 15`.

Important timeout details:

- This is packet-count based, not wall-clock based.
- Timeout only logs a warning and breaks the loop.
- Timeout does not automatically return failed status.
- After break, post-processing and success/failure checks still run.

Post-processing after loop:

- OHLCV is sorted by `index` and truncated to last `numb_candles`.
- Each indicator series is sorted by `index` and truncated to last `numb_candles`.

## Output Schema

All public calls are wrapped by `@catch_errors`, so output is always the standardized envelope:

```python
{
    "status": "success" | "failed",
    "data": <payload or None>,
    "metadata": {...},
    "error": None | "message"
}
```

### Success payload (`status="success"`)

```python
{
    "status": "success",
    "data": {
        "ohlcv": [
            {
                "index": int,
                "timestamp": int | float,
                "open": int | float,
                "high": int | float,
                "low": int | float,
                "close": int | float,
                "volume": int | float,  # Present only when provided by stream
            }
        ],
        "indicators": {
            "STD;RSI": [
                {"index": int, "timestamp": int | float, "0": int | float, "1": int | float}
            ]
        },
    },
    "metadata": {
        "exchange": "BINANCE",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "numb_candles": 10,
        # "indicators" appears only when non-None was provided
    },
    "error": None,
}
```

Behavior note: a successful response can contain fewer than `numb_candles` rows if the loop stops before enough candles are collected but at least one OHLCV entry exists and indicator checks pass.

## Failure Paths

`get_candles()` can return `status="failed"` in these cases:

1. Validation failure (`verify_symbol_exchange`, `validate_timeframe`, `validate_range`).
2. No OHLCV parsed from stream:
   - Error: `"No OHLCV data received from stream."`
3. Indicators requested but at least one requested script ID missing in final `indicator_data`:
   - Error: `"Failed to fetch indicator data for: <comma-separated-script-ids>"`
4. Any unexpected exception in method body (including connection/JWT errors, indicator metadata failures, websocket send failures):
   - Error format from decorator: `"Unexpected error: <exception message>"`

Notes on failures and partial data:

- Missing-indicator failure returns `data=None` (no partial OHLCV payload attached).
- Timeout by itself is not an error path; it becomes failure only if one of the explicit failure checks is triggered afterward.

## `connect()`

`CandleStreamer` inherits `connect()` from `BaseStreamer`.

- Uses `unauthorized_user_token` when no cookie is set.
- If cookie exists, attempts JWT resolution.
- JWT resolution failure raises `RuntimeError`, which is converted by `@catch_errors` into a failed envelope when called from `get_candles()`.
