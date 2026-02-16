# RealTimeData API

The `RealTimeData` class provides simple generators for raw OHLCV data and
multi-symbol watchlist streaming.

> **Tip:** For normalised price updates, use
> [`Streamer.stream_realtime_price()`](streamer.md#stream_realtime_price) instead.

## Performance Optimizations

As of version 1.0.0, the WebSocket connection includes performance optimizations:

- **TCP_NODELAY**: Disables Nagle's algorithm for lower latency data delivery
- **Dual Session Subscription**: Subscribes to both quote and chart sessions for faster updates
- **Enhanced Message Handling**: Processes both QSD (quote) and DU (data update) messages

These optimizations provide update frequencies of ~1 update every 3-4 seconds, matching browser performance.

## Constructor

```python
from tv_scraper.streaming import RealTimeData

rt = RealTimeData()
```

No arguments required. Creates a WebSocket connection using the screener
endpoint.

## Methods

### `get_ohlcv()`

Stream OHLCV packets for a single symbol.

```python
gen = rt.get_ohlcv(exchange="BINANCE", symbol="BTCUSDT")

for packet in gen:
    print(packet)
```

**Args:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `exchange` | `str` | Exchange name (e.g. `"BINANCE"`) |
| `symbol` | `str` | Symbol name (e.g. `"BTCUSDT"`) |

**Returns:** A generator yielding raw parsed JSON packets from the WebSocket feed.

### `get_latest_trade_info()`

Stream summary information for multiple symbols simultaneously.

```python
gen = rt.get_latest_trade_info(
    exchanges=["BINANCE", "NASDAQ"],
    symbols=["BTCUSDT", "AAPL"],
)

for packet in gen:
    print(packet)
```

**Args:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `exchanges` | `list[str]` | List of exchange names |
| `symbols` | `list[str]` | List of symbol names (same order as exchanges) |

**Returns:** A generator yielding raw parsed JSON packets.

## Migration from `tradingview_scraper`

| Old API | New API |
|---|---|
| `RealTimeData().get_ohlcv("BINANCE:BTCUSDT")` | `RealTimeData().get_ohlcv(exchange="BINANCE", symbol="BTCUSDT")` |
| `get_latest_trade_info(["BINANCE:BTCUSDT", ...])` | `get_latest_trade_info(exchanges=[...], symbols=[...])` |
| Combined `EXCHANGE:SYMBOL` strings | Separate `exchange` and `symbol` parameters |

## Heartbeat Handling

TradingView sends periodic heartbeat messages (`~h~{number}`). These are
automatically echoed back by `RealTimeData` and never yielded to your code.
