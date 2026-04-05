# Streaming Overview

The `tv_scraper.streaming` package provides real-time and historical market data
via TradingView's WebSocket API.

| Class | Use case | Documentation |
|-------|----------|---------------|
| `CandleStreamer` | OHLCV candles + indicators | [candle_streamer.md](candle_streamer.md) |
| `ForecastStreamer` | Analyst forecast data (stocks) | [forecast_streamer.md](forecast_streamer.md) |
| `Streamer` | Combined: candles + forecast + realtime | [streamer.md](streamer.md) |
| `BaseStreamer` | Base class for custom streamers | [base_streamer.md](base_streamer.md) |

## Performance Optimizations

As of version 1.0.2, the streaming module includes WebSocket optimizations for low-latency real-time data:

- **TCP_NODELAY**: Socket option enabled to disable Nagle's algorithm, reducing packet transmission latency
- **Dual Session Subscription**: Real-time price streaming subscribes to both quote and chart sessions
- **Multi-Message Processing**: Handles QSD (quote session data) and DU (data update) messages for maximum update frequency

These optimizations deliver approximately 1 update every 3-4 seconds for active symbols, matching browser performance.

## Architecture

```
tv_scraper/streaming/
├── __init__.py              # Package exports
├── stream_handler.py       # Low-level WebSocket protocol handler
├── base_streamer.py        # Base class extending BaseScraper, provides WebSocket connection
├── candle_streamer.py      # Candle + indicator streaming (extends BaseStreamer)
├── forecast_streamer.py    # Forecast data streaming (extends BaseStreamer)
├── streamer.py             # Streamer class (combines all features for convenience)
└── utils.py                # Symbol validation, indicator metadata fetching
```

### Inheritance Hierarchy

- **`BaseScraper`** (core/base.py) - Provides export, success/error responses, cookie handling
- **`BaseStreamer`** - Extends BaseScraper, provides WebSocket connection via StreamHandler
- **`CandleStreamer`** - Extends BaseStreamer, adds get_candles() method
- **`ForecastStreamer`** - Extends BaseStreamer, adds get_forecast() method
- **`Streamer`** - Convenience class combining all streaming features

### Extending Streamer

To add new streaming features, extend `BaseStreamer`:

```python
from tv_scraper.streaming.base_streamer import BaseStreamer

class MyCustomStreamer(BaseStreamer):
    def get_custom_data(self, exchange: str, symbol: str):
        handler = self.connect()  # Get WebSocket connection
        # ... implement custom streaming logic
        return self._success_response(data, exchange=exchange, symbol=symbol)
```

### StreamHandler (Low-level)

`StreamHandler` manages the raw WebSocket connection:

- Connects to `wss://data.tradingview.com/socket.io/websocket`
- Generates session identifiers (`qs_*` for quotes, `cs_*` for charts)
- Frames messages with TradingView's `~m~{length}~m~{payload}` protocol
- Initialises sessions (auth, locale, chart/quote creation, field setup)
- Applies TCP_NODELAY socket option for low-latency streaming

You rarely need to use `StreamHandler` directly — `Streamer` composes it
internally.

### Response Format

All `Streamer` methods return the standard response envelope:

```python
{
    "status": "success" | "failed",
    "data": { ... },
    "metadata": { "exchange": "...", "symbol": "...", ... },
    "error": None | "error message"
}
```

Errors are returned (not raised) from public methods.

## Quick Start

```python
from tv_scraper.streaming import Streamer

# Fetch 10 candles
s = Streamer()
result = s.get_candles(exchange="BINANCE", symbol="BTCUSDT", timeframe="1h")
print(result["data"]["ohlcv"])

# Continuous realtime price updates
for tick in s.stream_realtime_price(exchange="BINANCE", symbol="BTCUSDT"):
    print(tick["price"], tick["change_percent"])
```
