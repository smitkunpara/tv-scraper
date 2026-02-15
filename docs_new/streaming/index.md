# Streaming Overview

The `tv_scraper.streaming` package provides real-time and historical market data
via TradingView's WebSocket API. There are two main entry points:

| Class | Use case |
|---|---|
| [`Streamer`](streamer.md) | Fetch OHLCV candles, indicators, and continuous price updates |
| [`RealTimeData`](realtime-price.md) | Simple generators for raw OHLCV and watchlist packets |

## Architecture

```
tv_scraper/streaming/
├── __init__.py          # Package exports
├── stream_handler.py    # Low-level WebSocket protocol handler
├── streamer.py          # Streamer class (candles + indicators + realtime)
├── price.py             # RealTimeData class (simple OHLCV + watchlist)
└── utils.py             # Symbol validation, indicator metadata fetching
```

### StreamHandler (Low-level)

`StreamHandler` manages the raw WebSocket connection:

- Connects to `wss://data.tradingview.com/socket.io/websocket`
- Generates session identifiers (`qs_*` for quotes, `cs_*` for charts)
- Frames messages with TradingView's `~m~{length}~m~{payload}` protocol
- Initialises sessions (auth, locale, chart/quote creation, field setup)

You rarely need to use `StreamHandler` directly — `Streamer` and `RealTimeData`
compose it internally.

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

## Migration from `tradingview_scraper`

| Old API | New API |
|---|---|
| `Streamer().stream(exchange, symbol, ...)` | `Streamer().get_candles(exchange, symbol, ...)` |
| Combined `exchange:symbol` params | Separate `exchange` and `symbol` args |
| Raises exceptions on errors | Returns `{"status": "failed", ...}` |
| `from tradingview_scraper.symbols.stream import Streamer` | `from tv_scraper.streaming import Streamer` |

The old `stream()` method is kept as a compatibility alias.
