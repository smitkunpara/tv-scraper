# Real-Time Streaming

## Overview

The real-time streaming module provides functionality to connect to TradingView's WebSocket API for receiving live market data. This includes OHLCV (Open, High, Low, Close) data and technical indicator values in real-time.

The module consists of three main components:
- `RealTimeData`: Low-level WebSocket connection handler for raw price data
- `Streamer`: High-level interface for streaming OHLCV and indicator data
- `StreamHandler`: Session management and message handling

!!! note "Supported Data"
    For a complete list of supported indicators, timeframes, and exchanges, see [Supported Data](supported_data.md).

## Input Specification

### RealTimeData Class

```python
RealTimeData()
```

**Methods:**

- `get_ohlcv(exchange_symbol: str)` - Returns generator for OHLCV data
- `get_latest_trade_info(exchange_symbol: List[str])` - Returns generator for multiple symbols

**Parameters:**
- `exchange_symbol`: String or list in format "EXCHANGE:SYMBOL" (e.g., "BINANCE:BTCUSDT")

### Streamer Class

```python
Streamer(
    export_result=False,
    export_type='json',
    websocket_jwt_token="unauthorized_user_token"
)
```

**Parameters:**
- `export_result` (bool): Whether to export results to file (default: False)
- `export_type` (str): Export format, either 'json' or 'csv' (default: 'json')
- `websocket_jwt_token` (str): JWT token for authenticated access (default: "unauthorized_user_token")

**Methods:**

- `stream(exchange, symbol, timeframe='1m', numb_price_candles=10, indicators=None)`

**Parameters:**
- `exchange` (str): Exchange name (e.g., "BINANCE")
- `symbol` (str): Symbol name (e.g., "BTCUSDT")
- `timeframe` (str): Timeframe for data (default: "1m")
- `numb_price_candles` (int): Number of price candles to retrieve (default: 10)
- `indicators` (List[Tuple[str, str]]): List of (indicator_id, indicator_version) tuples

## Output Specification

### RealTimeData Output

The `get_data()` generator yields parsed JSON objects with the following structure:

```python
{
    "m": "message_type",  # e.g., "timescale_update", "du"
    "p": [
        # Message parameters
    ]
}
```

### Streamer Output

The `stream()` method returns a dictionary with two keys:

```python
{
    "ohlcv": [
        {
            "index": int,
            "timestamp": int,
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "volume": float
        },
        # ... more OHLCV candles
    ],
    "indicator": {
        "STD;RSI": [
            {
                "index": int,
                "timestamp": int,
                "0": float,  # RSI value
                # ... additional indicator values
            },
            # ... more indicator data points
        ],
        # ... additional indicators
    }
}
```

## Code Examples

### Basic OHLCV Streaming

```python
from tradingview_scraper.symbols.stream import Streamer

# Create streamer instance
streamer = Streamer(
    export_result=True,
    export_type='json',
    websocket_jwt_token="your_jwt_token_here"
)

# Stream OHLCV data only
result = streamer.stream(
    exchange="BINANCE",
    symbol="BTCUSDT",
    timeframe="1m",
    numb_price_candles=10
)

print(f"Received {len(result['ohlcv'])} OHLCV candles")
print(f"First candle: {result['ohlcv'][0]}")
```

### Streaming with Single Indicator

```python
# Stream with RSI indicator
result = streamer.stream(
    exchange="BINANCE",
    symbol="BTCUSDT",
    indicators=[("STD;RSI", "37.0")],
    timeframe="1m",
    numb_price_candles=5
)

print(f"OHLCV candles: {len(result['ohlcv'])}")
print(f"RSI data points: {len(result['indicator']['STD;RSI'])}")
```

### Streaming with Multiple Indicators

```python
# Stream with multiple indicators (max 2 for free accounts)
result = streamer.stream(
    exchange="BINANCE",
    symbol="BTCUSDT",
    indicators=[
        ("STD;RSI", "37.0"),
        ("STD;MACD", "31.0")
    ],
    timeframe="5m",
    numb_price_candles=8
)

print(f"Indicators received: {list(result['indicator'].keys())}")
```

### Using RealTimeData Directly

```python
from tradingview_scraper.symbols.stream import RealTimeData

# Create real-time data instance
real_time_data = RealTimeData()

# Get OHLCV data generator
data_generator = real_time_data.get_ohlcv("BINANCE:BTCUSDT")

# Process real-time data
for i, packet in enumerate(data_generator):
    print(f"Packet {i}: {packet}")
    if i >= 20:  # Process 20 packets
        break
```

## JWT Token Requirements

Real-time streaming requires a valid TradingView JWT token for full functionality:

1. **Unauthorized Access**: Uses "unauthorized_user_token" by default with limited functionality
2. **Authenticated Access**: Set `TRADINGVIEW_JWT_TOKEN` environment variable for full access
3. **Token Usage**: Pass token to Streamer constructor or set environment variable

```python
# Using environment variable
import os
jwt_token = os.getenv("TRADINGVIEW_JWT_TOKEN")

streamer = Streamer(websocket_jwt_token=jwt_token)
```

## Reconnection Behavior

The streaming system handles connection issues automatically:

1. **Heartbeat Management**: Automatically responds to WebSocket heartbeats
2. **Connection Loss**: Detects WebSocketConnectionClosedException and attempts reconnection
3. **Error Recovery**: Continues processing after transient errors
4. **Graceful Shutdown**: Properly closes WebSocket connections on exit

## Edge Cases

### Symbol Validation Failures

- **Invalid Format**: Symbols not in "EXCHANGE:SYMBOL" format are rejected
- **Nonexistent Symbols**: Returns 404 errors for invalid exchange/symbol combinations
- **Retry Logic**: Attempts validation up to 3 times before failing

### Data Processing Edge Cases

- **Empty Packets**: Skips packets with no meaningful data
- **Malformed JSON**: Logs parsing errors and continues processing
- **Missing Fields**: Handles optional fields like volume gracefully
- **Timeout Scenarios**: Stops after 15 packets if data requirements not met

### Indicator-Specific Edge Cases

- **Indicator Timeouts**: Some indicators may fail to load within timeout period
- **Data Format Variations**: Different indicators may have different data structures
- **Free Account Limits**: Only 2 indicators can be streamed simultaneously on free accounts
- **Premium Features**: Some indicators require premium TradingView accounts

## Performance Considerations

1. **Rate Limiting**: Avoid making too many requests in quick succession
2. **Connection Reuse**: Create Streamer instances and reuse them when possible
3. **Sleep Between Requests**: Add delays between requests to avoid "forbidden" errors
4. **Resource Management**: Properly close WebSocket connections when done

```python
# Example with proper resource management
streamer = Streamer(websocket_jwt_token=jwt_token)

try:
    result = streamer.stream(
        exchange="BINANCE",
        symbol="BTCUSDT",
        timeframe="1m",
        numb_price_candles=5
    )
    # Process results
finally:
    # Connection is automatically closed by Streamer
    pass
```
