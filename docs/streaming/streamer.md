# Streamer API

The `Streamer` class provides OHLCV candle retrieval, indicator data,
analyst forecast snapshots, and continuous realtime price streaming via
TradingView's WebSocket API.

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
    cookie="<TRADINGVIEW_COOKIE>",  # Optional: session cookie for indicator access
)
```

### Why Cookies instead of JWT?

The previous manual `websocket_jwt_token` approach was prone to disruptions because TradingView's JWT tokens typically expire after a few hours. By providing a `cookie` instead:

1.  **Continuous Streaming**: The library can automatically detect expired tokens and resolve fresh ones in the background without interrupting your stream.
2.  **Pine Script Verification**: Cookies are required to verify and access your personal/private Pine scripts when used as indicators in `get_candles()`.
3.  **Simulated Browser Auth**: It mimics a real browser session, reducing the risk of authentication-related blocks.

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
s = Streamer(cookie="<TRADINGVIEW_COOKIE>")

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

### `get_forecast()`

Fetch analyst forecast data for stock symbols only.

```python
result = s.get_forecast(
    exchange="NYSE",
    symbol="A",
)
```

**Success response:**

```python
{
    "status": "success",
    "data": {
        "revenue_currency": "USD",
        "previous_close_price": 114.5,
        "average_price_target": 162.8,
        "highest_price_target": 185,
        "lowest_price_target": 145,
        "median_price_target": 160,
        "yearly_eps_data": [
            {"FiscalPeriod": "2026", "Estimate": 5.9}
            ...
        ],
        "quarterly_eps_data": [
            {"FiscalPeriod": "2026-Q1", "Estimate": 1.36}
            ...
        ],
        "yearly_revenue_data": [{
            "FiscalPeriod": "2026", "Estimate": 7395056494}
            ...
        ],
        "quarterly_revenue_data": [{
            "FiscalPeriod": "2026-Q1", "Estimate": 1807792308}
            ...
        ]
    },
    "metadata": {
        "exchange": "NYSE",
        "symbol": "A",
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
            "yearly_revenue_data"
        ]
    },
    "error": null
}
```

**Failed response (non-stock symbol):**

```python
{
    "status": "failed",
    "data": null,
    "metadata": {
        "exchange": "BINANCE",
        "symbol": "BTCUSDT"
    },
    "error": "forecast is not available for this symbol because it is type: crypto"
}
```

**Failed response (partial data / missing keys):**

```python
{
    "status": "failed",
    "data": {
        "revenue_currency": "USD",
        "previous_close_price": null,
        "average_price_target": 162.8,
        "highest_price_target": 185,
        "lowest_price_target": 145,
        "median_price_target": 160,
        "yearly_eps_data": null,
        "quarterly_eps_data": [{"FiscalPeriod": "2026-Q1", "Estimate": 1.36}],
        "yearly_revenue_data": null,
        "quarterly_revenue_data": [{"FiscalPeriod": "2026-Q1", "Estimate": 1807792308}]
    },
    "metadata": {
        "exchange": "NYSE",
        "symbol": "A",
        "available_output_keys": [
            "average_price_target",
            "highest_price_target",
            "lowest_price_target",
            "median_price_target",
            "quarterly_eps_data",
            "quarterly_revenue_data",
            "revenue_currency"
        ]
    },
    "error": "failed to fetch keys: previous_close_price, yearly_eps_data, yearly_revenue_data"
}
```

Notes:

- Uses WebSocket quote updates as the source of forecast data.
- Output key mappings are fixed and deterministic.
- Public API follows the standard envelope: `status`, `data`, `metadata`, `error`.

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
