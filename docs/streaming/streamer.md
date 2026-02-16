# Streamer API

The `Streamer` class provides OHLCV candle retrieval, indicator data, and
continuous realtime price streaming via TradingView's WebSocket API.

## Performance Optimizations (v1.0.0+)

The WebSocket connection includes several optimizations for low-latency streaming:

- **TCP_NODELAY Socket Option**: Disables Nagle's algorithm for immediate packet transmission
- **Dual Session Subscription**: Subscribes to both quote session (QSD) and chart session (DU) for maximum update frequency
- **Enhanced Message Processing**: Handles both QSD (quote data) and DU (chart data updates) message types

These optimizations deliver update frequencies of approximately 1 update every 3-4 seconds, matching browser performance for real-time price streaming.

## Constructor

```python
from tv_scraper.streaming import Streamer

s = Streamer(
    export_result=False,       # Save results to file
    export_type="json",        # "json" or "csv"
    websocket_jwt_token="unauthorized_user_token",  # JWT for indicator access
)
```

## Methods

### `get_available_indicators()`

Fetch the list of available standard built-in indicators.

> **Note:** This is specifically for use with candle and indicator streaming. Use these IDs and versions with `get_candles()`.

```python
indicators = Streamer.get_available_indicators()
# Returns: [{"name": "Relative Strength Index", "id": "STD;RSI", "version": "45.0"}, ...]
```

### `get_candles()`

Fetch historical OHLCV candles with optional technical indicators.

```python
result = s.get_candles(
    exchange="BINANCE",
    symbol="BTCUSDT",
    timeframe="1h",         # 1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1w, 1M
    numb_candles=10,
    indicators=[("STD;RSI", "37.0")],  # Optional
)
```

**Response:**

```python
{
    "status": "success",
    "data": {
        "ohlcv": [
            {
                "index": 0,
                "timestamp": 1700000000,
                "open": 42000.0,
                "high": 42100.0,
                "low": 41950.0,
                "close": 42050.2,
                "volume": 125.5
            },
            ...
        ],
        "indicators": {
            "STD;RSI": [
                {"index": 0, "timestamp": 1700000000, "0": 55.5, "1": 60.0},
                ...
            ]
        }
    },
    "metadata": {
        "exchange": "BINANCE",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "numb_candles": 10
    },
    "error": null
}
```

### `stream_realtime_price()`

Persistent generator yielding normalized quote updates including bid, ask, and daily statistics.

```python
for tick in s.stream_realtime_price(exchange="BINANCE", symbol="BTCUSDT"):
    print(f"Price: {tick['price']}, Bid: {tick['bid']}, Ask: {tick['ask']}, Volume: {tick['volume']}")
```

**Yielded dict:**

```python
{
    "exchange": "BINANCE",
    "symbol": "BTCUSDT",
    "price": 42000.0,
    "volume": 12345.6,
    "change": 150.0,
    "change_percent": 0.36,
    "high": 42150.0,
    "low": 41800.0,
    "open": 41850.0,
    "prev_close": 41845.0,
    "bid": 41998.0,
    "ask": 42002.0
}
```

## Timeframe Mapping

| Input | TradingView value |
|-------|------------------|
| `1m`  | `1`              |
| `5m`  | `5`              |
| `15m` | `15`             |
| `30m` | `30`             |
| `1h`  | `60`             |
| `2h`  | `120`            |
| `4h`  | `240`            |
| `1d`  | `1D`             |
| `1w`  | `1W`             |
| `1M`  | `1M`             |

## Export

When `export_result=True`, OHLCV and indicator data are saved to the `export/`
directory with timestamped filenames:

```python
s = Streamer(export_result=True, export_type="csv")
s.get_candles(exchange="NASDAQ", symbol="AAPL")
# Creates: export/ohlcv_aapl_20260215-120000.csv
```

## Error Handling

Public methods never raise exceptions. Errors are returned as:

```python
{
    "status": "failed",
    "data": null,
    "metadata": {"exchange": "BAD", "symbol": "XXX"},
    "error": "Invalid exchange:symbol 'BAD:XXX'"
}
```
