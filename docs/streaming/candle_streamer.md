# CandleStreamer API

The `CandleStreamer` class provides OHLCV candle retrieval and technical indicator data via TradingView's WebSocket API. Use this for historical candlestick data with optional technical indicators.

## Installation

```python
from tv_scraper.streaming import CandleStreamer
```

## Constructor

```python
cs = CandleStreamer(
    export_result=False,        # Save results to file
    export_type="json",        # "json" or "csv"
    cookie="<TRADINGVIEW_COOKIE>",  # Optional: session cookie for indicator access
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `export_result` | `bool` | `False` | Whether to save results to file |
| `export_type` | `str` | `"json"` | Export format: `"json"` or `"csv"` |
| `cookie` | `str \| None` | `None` | TradingView session cookie for private indicators |

## Methods

### `get_candles()`

Fetch historical OHLCV candles with optional technical indicators.

```python
result = cs.get_candles(
    exchange="BINANCE",
    symbol="BTCUSDT",
    timeframe="1h",         # 1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1w, 1M
    numb_candles=10,
    indicators=[("STD;RSI", "37.0")],  # Optional: list of (script_id, version)
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `exchange` | `str` | **required** | Exchange name (e.g., `"BINANCE"`, `"NASDAQ"`, `"NYSE"`) |
| `symbol` | `str` | **required** | Symbol name (e.g., `"BTCUSDT"`, `"AAPL"`) |
| `timeframe` | `str` | `"1m"` | Candle timeframe |
| `numb_candles` | `int` | `10` | Number of candles to retrieve |
| `indicators` | `list[tuple[str, str]] \| None` | `None` | Optional list of `(script_id, version)` tuples |

#### Supported Timeframes

| Timeframe | Description |
|-----------|-------------|
| `"1m"` | 1 minute |
| `"5m"` | 5 minutes |
| `"15m"` | 15 minutes |
| `"30m"` | 30 minutes |
| `"1h"` | 1 hour |
| `"2h"` | 2 hours |
| `"4h"` | 4 hours |
| `"1d"` | 1 day |
| `"1w"` | 1 week |
| `"1M"` | 1 month |

#### Success Response

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
            {
                "index": 1,
                "timestamp": 1700003600,
                "open": 42050.2,
                "high": 42150.0,
                "low": 42000.0,
                "close": 42100.0,
                "volume": 150.0
            }
        ],
        "indicators": {
            "STD;RSI": [
                {"index": 0, "timestamp": 1700000000, "0": 55.5, "1": 60.0},
                {"index": 1, "timestamp": 1700003600, "0": 58.2, "1": 62.1}
            ]
        }
    },
    "metadata": {
        "exchange": "BINANCE",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "numb_candles": 10,
        "indicators": [["STD;RSI", "37.0"]]
    },
    "error": null
}
```

#### Error Response - Invalid Exchange

```python
{
    "status": "failed",
    "data": null,
    "metadata": {
        "exchange": "INVALID_EXCHANGE",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "numb_candles": 10
    },
    "error": "Invalid exchange: 'INVALID_EXCHANGE'. Did you mean: 'BINANCE'?"
}
```

#### Error Response - Invalid Symbol

```python
{
    "status": "failed",
    "data": null,
    "metadata": {
        "exchange": "BINANCE",
        "symbol": "INVALID_SYMBOL",
        "timeframe": "1h",
        "numb_candles": 10
    },
    "error": "Symbol 'INVALID_SYMBOL' not found on exchange 'BINANCE'"
}
```

#### Error Response - No Data Received

```python
{
    "status": "failed",
    "data": null,
    "metadata": {
        "exchange": "BINANCE",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "numb_candles": 10
    },
    "error": "No OHLCV data received from stream."
}
```

#### Error Response - Missing Indicators

```python
{
    "status": "failed",
    "data": null,
    "metadata": {
        "exchange": "BINANCE",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "numb_candles": 10,
        "indicators": [["STD;INVALID", "1.0"]]
    },
    "error": "Failed to fetch indicator data for: STD;INVALID"
}
```

### `connect()`

Create and return a connected StreamHandler with JWT token.

```python
handler = cs.connect()
```

Returns a connected `StreamHandler` instance.

## Usage Examples

### Basic - Get 10 candles

```python
from tv_scraper.streaming import CandleStreamer

cs = CandleStreamer()
result = cs.get_candles(
    exchange="BINANCE",
    symbol="BTCUSDT",
    timeframe="1h",
    numb_candles=10
)

if result["status"] == "success":
    for candle in result["data"]["ohlcv"]:
        print(f"Open: {candle['open']}, Close: {candle['close']}")
```

### With RSI Indicator

```python
from tv_scraper.streaming import CandleStreamer

cs = CandleStreamer()

# First, get available indicators
indicators = cs.get_available_indicators()
print(indicators["data"][:3])  # Show first 3

# Use RSI
result = cs.get_candles(
    exchange="NASDAQ",
    symbol="AAPL",
    timeframe="1d",
    numb_candles=50,
    indicators=[("STD;RSI", "37.0")]
)

if result["status"] == "success":
    print(f"OHLCV: {len(result['data']['ohlcv'])} candles")
    print(f"RSI values: {result['data']['indicators']['STD;RSI']}")
```

### Multiple Indicators

```python
result = cs.get_candles(
    exchange="NASDAQ",
    symbol="AAPL",
    timeframe="1h",
    numb_candles=100,
    indicators=[
        ("STD;RSI", "37.0"),
        ("STD;MACD", "12.0"),
        ("STD;ATR", "12.0")
    ]
)
```

### Custom Pine Indicator

```python
from tv_scraper.scrapers.scripts import Pine
from tv_scraper.streaming import CandleStreamer

# Create a custom Pine script
pine = Pine(cookie="<TRADINGVIEW_COOKIE>")
pine.create_script(
    name="My Custom Indicator",
    source="""
    //@version=6
    indicator("My Custom Indicator", overlay=false)
    rsi = ta.rsi(close, 14)
    plot(rsi, title="RSI")
    """
)

# Get saved scripts
saved = pine.list_saved_scripts()
script = saved["data"][0]

# Use in CandleStreamer
cs = CandleStreamer(cookie="<TRADINGVIEW_COOKIE>")
result = cs.get_candles(
    exchange="NASDAQ",
    symbol="AAPL",
    numb_candles=50,
    indicators=[(script["id"], str(script["version"]))]
)
```

### Export to CSV

```python
cs = CandleStreamer(export_result=True, export_type="csv")
result = cs.get_candles(
    exchange="BINANCE",
    symbol="BTCUSDT",
    timeframe="4h",
    numb_candles=100
)
# Creates: export/ohlcv_btcusdt_20260215-120000.csv
```

## Error Handling

All public methods return standardized response envelopes and never raise exceptions.

```python
result = cs.get_candles(exchange="INVALID", symbol="XXX")

# Always check status
if result["status"] == "failed":
    print(f"Error: {result['error']}")
    print(f"Metadata: {result['metadata']}")
```

## Inheritance

`CandleStreamer` extends `BaseStreamer` which extends `BaseScraper`, providing:

- `_success_response()` - Build standardized success response
- `_error_response()` - Build standardized error response
- `_export()` - Export data to file
- `validator` - DataValidator singleton for exchange/symbol validation
