# CandleStreamer

`CandleStreamer` streams OHLCV candles over TradingView WebSocket sessions. It can also attach indicator studies and provides a realtime price generator.

## Quick Use

### Candles only

```python
from tv_scraper import CandleStreamer

streamer = CandleStreamer()
result = streamer.get_candles(
    exchange="BINANCE",
    symbol="BTCUSDT",
    timeframe="1h",
    numb_candles=25,
)
```

Output structure:

```python
{
    "status": "success",
    "data": {
        "ohlcv": [
            {
                "index": 0,
                "timestamp": 1700000000,
                "open": 185.0,
                "high": 187.0,
                "low": 184.0,
                "close": 186.0,
                "volume": 50000000,
            },
            # ... more candles (one row per candle index)
        ],
        "indicators": {},
    },
    "metadata": {
        "exchange": "BINANCE",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "numb_candles": 25,
    },
    "warnings": [],
    "error": None,
}
```

### Candles with indicators

```python
result = streamer.get_candles(
    exchange="BINANCE",
    symbol="BTCUSDT",
    timeframe="15m",
    numb_candles=20,
    indicators=[("STD;RSI", "37.0")],
)
```

Output structure:

```python
{
    "status": "success",
    "data": {
        "ohlcv": [
            {
                "index": 0,
                "timestamp": 1700000000,
                "open": 185.0,
                "high": 187.0,
                "low": 184.0,
                "close": 186.0,
                "volume": 50000000,
            },
            # ... more candles (one row per candle index)
        ],
        "indicators": {
            "STD;RSI": [
                {"index": 0, "timestamp": 1700000000, "0": 55.5},
                # ... more rows (one per candle index)
            ]
        },
    },
    "metadata": {
        "exchange": "BINANCE",
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "numb_candles": 20,
        "indicators": [("STD;RSI", "37.0")],
    },
    "warnings": [],
    "error": None,
}
```

!!! note "Multiple rows"
    Both `ohlcv` and indicator arrays contain **one row per candle index**. If you request 5 candles with an indicator, you'll get 5 rows in both arrays. The indicator rows are keyed by study name (for example, `"STD;RSI"`) and contain an array of values for each candle.

### Realtime prices
 
```python
indicators = [("STD;RSI", "37.0")]
for tick in streamer.stream_realtime_price(
    exchange="BINANCE", 
    symbol="BTCUSDT",
    indicators=indicators
):
    price = tick["price"]
    rsi = tick["indicators"].get("STD;RSI", {}).get("0")
    print(f"Price: {price}, RSI: {rsi}")
```
 
Output structure (yielded per update):
 
```python
{
    "exchange": "BINANCE",
    "symbol": "BTCUSDT",
    "price": 60125.0,
    "volume": 1234.56,
    "change": 45.0,
    "change_percent": 0.08,
    "high": 60250.0,
    "low": 59800.0,
    "open": 60010.0,
    "prev_close": 60080.0,
    "bid": 60124.5,
    "ask": 60125.5,
    "indicators": {
        "STD;RSI": {
            "index": 299, 
            "timestamp": 1700000000, 
            "0": 55.5,
            # ... other fields
        }
    },
}
```

## Inputs

| Parameter | Notes |
|-----------|-------|
| `exchange` | Use a supported exchange from [Exchanges](../supported_data.md#exchanges) |
| `symbol` | Exchange symbol slug such as `BTCUSDT` |
| `timeframe` | Use a supported timeframe from [Timeframes](../supported_data.md#timeframes) |
| `numb_candles` | Must be between `1` and `5000` |
| `indicators` | Optional list of `(script_id, version)` tuples |

## Finding Indicator IDs

For built-in indicators:

```python
result = CandleStreamer.get_available_indicators()
```

For custom indicators or private scripts, use your Pine script ID and version. A cookie may be required if your TradingView account owns the script.

!!! failure "wrong input"
    This fails because `numb_candles` must be at least `1`.

    ```python
    streamer.get_candles(
        exchange="BINANCE",
        symbol="BTCUSDT",
        timeframe="1h",
        numb_candles=0,
    )
    ```

!!! note "Notes"
    - The receive loop uses a packet-count cutoff, not a wall-clock timeout.
    - If no OHLCV data arrives, the method returns `status="failed"`.
    - If you request indicators and one or more studies never resolve, the method returns `status="failed"` with the missing indicator IDs in the error message.
