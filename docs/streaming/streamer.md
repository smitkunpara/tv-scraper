# Streamer API

The `Streamer` class provides OHLCV candle retrieval, indicator data, and
continuous realtime price streaming via TradingView's WebSocket API.

## 🌲 New in v1.2.0: Custom Pine Indicators in Streamer

Streamer can now be used as the consumption layer for custom Pine indicators managed by `tv_scraper.scrapers.scripts.Pine`.

Core workflow:

1. Build and maintain your Pine script from Python.
2. Merge multiple indicator formulas into one Pine script when needed.
3. Fetch that custom indicator in `get_candles()` using its TradingView indicator id/version.

This is ideal when you want one script to emit multiple related signals and retrieve them in one pipeline.

Why this is useful:

- If your TradingView plan limits simultaneous indicator usage (for example, 2 on free usage), this approach helps you pack multiple calculations into one Pine script.
- Streamer can then fetch that merged script output as one custom indicator target.

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
result = s.get_available_indicators()
```

**Response:**

```python
{
    "status": "success",
    "data": [
        {
            "name": "Relative Strength Index",
            "id": "STD;RSI",
            "version": "45.0"
        },
        {
            "name": "Average True Range",
            "id": "STD;ATR",
            "version": "12.0"
        }
        ...(other indicators)
    ],
    "metadata": {},
    "error": null
}
```

**Error response:**

```python
{
    "status": "failed",
    "data": null,
    "metadata": {},
    "error": "Failed to fetch available indicators: 503 Server Error"
}
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

### Example: Use a Custom Pine Indicator

```python
from tv_scraper.scrapers.scripts import Pine
from tv_scraper.streaming import Streamer

pine = Pine(cookie="<TRADINGVIEW_COOKIE>")
s = Streamer()

source_code = """
//@version=6
indicator("Merged Momentum Pack", overlay=false)

rsi = ta.rsi(close, 14)
macd = ta.macd(close, 12, 26, 9)
plot(rsi, title="RSI")
plot(macd[0], title="MACD")
"""

pine.create_script(name="Merged Momentum Pack", source=source_code)

saved = pine.list_saved_scripts()
script = saved["data"][0]

result = s.get_candles(
    exchange="BINANCE",
    symbol="BTCUSDT",
    timeframe="1h",
    numb_candles=50,
    indicators=[(script["id"], str(script["version"]))],
)
```

> Tip: If your strategy uses many indicator formulas, combine them in one Pine script and fetch them together instead of managing many separate indicator subscriptions.

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
