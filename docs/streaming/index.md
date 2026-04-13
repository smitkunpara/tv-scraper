# Streaming Overview

Use the streaming classes when you need WebSocket-backed data from TradingView.

## Which Class To Use

| Class | Use it for |
|-------|------------|
| `CandleStreamer` | candles, realtime price streaming, and optional indicator studies |
| `ForecastStreamer` | analyst forecast data for stock symbols |
| `Streamer` | legacy wrapper kept for backward compatibility |

## Recommended Starting Points

### Candles and realtime prices

```python
from tv_scraper.streaming import CandleStreamer

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
    "error": None,
}
```

### Forecast data

```python
from tv_scraper.streaming import ForecastStreamer

streamer = ForecastStreamer()
result = streamer.get_forecast(exchange="NASDAQ", symbol="AAPL")
```

Output structure:

```python
{
    "status": "success",
    "data": {
        "revenue_currency": "USD",
        "previous_close_price": 171.2,
        "average_price_target": 195.0,
        "highest_price_target": 220.0,
        "lowest_price_target": 175.0,
        "median_price_target": 193.0,
        "yearly_eps_data": [
            {
                "Actual": 2.3025,
                "Estimate": 2.248051,
                "FiscalPeriod": "2017",
                "IsReported": True,
                "Type": 22,
            },
            # ... more yearly EPS rows
        ],
        "quarterly_eps_data": [
            {
                "Actual": 1.4,
                "Estimate": 0.986396,
                "FiscalPeriod": "2021-Q2",
                "IsReported": True,
                "Type": 22,
            },
            # ... more quarterly EPS rows
        ],
        "yearly_revenue_data": [
            {
                "Actual": 229234000000,
                "Estimate": 227461939394,
                "FiscalPeriod": "2017",
                "IsReported": True,
                "Type": 22,
            },
            # ... more yearly revenue rows
        ],
        "quarterly_revenue_data": [
            {
                "Actual": 89584000000,
                "Estimate": 77088700724,
                "FiscalPeriod": "2021-Q2",
                "IsReported": True,
                "Type": 22,
            },
            # ... more quarterly revenue rows
        ],
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
            "yearly_revenue_data",
        ],
    },
    "error": None,
}
```

## Common Inputs

- exchange values: [Exchanges](../supported_data.md#exchanges)
- timeframe values: [Timeframes](../supported_data.md#timeframes)
- built-in indicator IDs: `CandleStreamer.get_available_indicators()`

## Output Pattern

Streaming methods still use the standard response envelope:

```python
{
    "status": "success" | "failed",
    "data": ...,
    "metadata": {...},
    "error": None | "message",
}
```

The one exception is `stream_realtime_price()`, which is a generator and yields tick dictionaries instead of returning an envelope.

## Legacy Wrapper

`Streamer` is deprecated. New code should prefer:

- [CandleStreamer](candle_streamer.md)
- [ForecastStreamer](forecast_streamer.md)

Use [Streamer (Legacy Wrapper)](streamer.md) only when you need the older combined interface.
