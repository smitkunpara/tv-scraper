# Streamer (Legacy Wrapper)

!!! warning "Deprecated"
    `Streamer` is deprecated. New code should use [CandleStreamer](candle_streamer.md) and [ForecastStreamer](forecast_streamer.md) directly.

!!! info "Version Note"
    The deprecation is documented in the current changelog for the `1.4.0` line of development.

## What It Still Does

`Streamer` keeps the older combined interface:

- `get_candles(...)`
- `get_forecast(...)`
- `stream_realtime_price(...)`
- `get_available_indicators()`

Internally:

- candle-related calls delegate to `CandleStreamer`
- forecast calls delegate to `ForecastStreamer`

## Replacement Mapping

| Legacy call | Preferred replacement |
|-------------|-----------------------|
| `Streamer.get_candles(...)` | `CandleStreamer.get_candles(...)` |
| `Streamer.stream_realtime_price(...)` | `CandleStreamer.stream_realtime_price(...)` |
| `Streamer.get_available_indicators()` | `CandleStreamer.get_available_indicators()` |
| `Streamer.get_forecast(...)` | `ForecastStreamer.get_forecast(...)` |

!!! tip "Legacy Example"
    ```python
    from tv_scraper.streaming import Streamer

    streamer = Streamer()
    result = streamer.get_candles(
        exchange="BINANCE",
        symbol="BTCUSDT",
        timeframe="1h",
        numb_candles=10,
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
            "numb_candles": 10,
        },
        "error": None,
    }
    ```

## Recommendation

Keep this page only for migration or backward compatibility. For new examples, prefer the dedicated streamer classes.
