# Streamer API

The `Streamer` class provides OHLC candle retrieval, indicator data, and
continuous realtime price streaming via TradingView's WebSocket API.

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

### `get_candles()`

Fetch historical OHLC candles with optional technical indicators.

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
        "ohlc": [
            {
                "index": 0,
                "timestamp": 1700000000,
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,
                "close": 102.0,
                "volume": 5000
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

### `stream()` (Compatibility Alias)

```python
result = s.stream(exchange="BINANCE", symbol="BTCUSDT")
```

Identical to `get_candles()`. Kept for backward compatibility.

### `stream_realtime_price()`

Persistent generator yielding normalized quote updates.

```python
for tick in s.stream_realtime_price(exchange="BINANCE", symbol="BTCUSDT"):
    print(f"Price: {tick['price']}, Change: {tick['change_percent']}%")
```

**Yielded dict:**

```python
{
    "exchange": "BINANCE",
    "symbol": "BTCUSDT",
    "price": 42000.0,
    "volume": 12345,
    "change": 150.0,
    "change_percent": 0.36
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

When `export_result=True`, OHLC and indicator data are saved to the `export/`
directory with timestamped filenames:

```python
s = Streamer(export_result=True, export_type="csv")
s.get_candles(exchange="NASDAQ", symbol="AAPL")
# Creates: export/ohlc_aapl_20260215-120000.csv
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
