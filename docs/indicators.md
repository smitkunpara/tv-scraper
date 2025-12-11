# Technical Indicators

## Overview

The Technical Indicators module provides functionality to scrape technical analysis indicators from TradingView for various financial instruments. This module allows users to retrieve technical indicator values for specific symbols, exchanges, and timeframes.

## Why This Feature Exists

The technical indicators feature exists to:

- Enable quantitative analysis of financial markets
- Provide access to 81+ technical indicators from TradingView
- Support multiple timeframes for comprehensive market analysis
- Allow both individual indicator selection and bulk retrieval
- Facilitate automated trading strategies and market research

## Input Specification

### Arguments

| Parameter | Type | Default | Description | Required |
|-----------|------|---------|-------------|----------|
| `exchange` | str | "BITSTAMP" | The exchange to scrape data from | No |
| `symbol` | str | "BTCUSD" | The symbol to scrape data for | No |
| `timeframe` | str | "1d" | Timeframe for analysis (1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1w, 1M) | No |
| `indicators` | List[str] | None | List of specific indicators to retrieve | Conditional |
| `allIndicators` | bool | False | Retrieve all available indicators | No |

### Constraints

- **Exchange**: Must be a valid exchange from [`tradingview_scraper/data/exchanges.txt`](https://github.com/smitkunpara/tradingview-scraper/blob/main/tradingview_scraper/data/exchanges.txt)
- **Symbol**: Must be a valid trading symbol for the specified exchange
- **Timeframe**: Must be one of the supported timeframes from [`tradingview_scraper/data/timeframes.json`](https://github.com/smitkunpara/tradingview-scraper/blob/main/tradingview_scraper/data/timeframes.json)
- **Indicators**: Must be valid indicator names from [`tradingview_scraper/data/indicators.txt`](https://github.com/smitkunpara/tradingview-scraper/blob/main/tradingview_scraper/data/indicators.txt)
- **Conditional Logic**: If `allIndicators=False`, then `indicators` list cannot be empty

## Output Specification

### Response Schema

```python
{
    "status": str,  # "success" or "failed"
    "data": dict    # Dictionary of indicator names and values (only present on success)
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | str | Indicates success or failure of the request |
| `data` | dict | Contains indicator names as keys and their values |

### Example Response

```python
{
    "status": "success",
    "data": {
        "RSI": 50.0,
        "Stoch.K": 80.0,
        "MACD.macd": 1.23,
        "EMA50": 50123.45
    }
}
```

## Behavioral Notes from Code and Tests

### Key Behaviors

1. **Timeframe Handling**: The `1d` timeframe is treated specially - no timeframe suffix is appended to indicators
2. **Indicator Validation**: All specified indicators are validated against the supported list
3. **Error Handling**: Invalid exchanges, indicators, or timeframes raise `ValueError` exceptions
4. **Export Functionality**: Results can be exported to JSON or CSV files when `export_result=True`
5. **Rate Limiting**: Free TradingView accounts are limited to 2 indicators maximum when streaming

### Test-Driven Behaviors

- ✅ **Required Parameters**: When `allIndicators=False`, indicators list cannot be empty
- ✅ **Default Timeframe**: Defaults to "1d" if not specified
- ✅ **Response Structure**: Returns status and data fields with cleaned indicator keys
- ✅ **Validation**: Validates exchanges, indicators, and timeframes before making API calls
- ✅ **Error Handling**: Returns `{"status": "failed"}` on request failures

## Code Examples

### Basic Usage

```python
from tradingview_scraper.symbols.technicals import Indicators

# Create indicators scraper instance
indicators_scraper = Indicators()

# Scrape specific indicators
result = indicators_scraper.scrape(
    exchange="BINANCE",
    symbol="BTCUSDT",
    timeframe="1d",
    indicators=["RSI", "Stoch.K"]
)

print(result)
```

### Advanced Usage

```python
# Scrape with custom timeframe
result = indicators_scraper.scrape(
    exchange="COINBASE",
    symbol="ETHUSD",
    timeframe="1h",
    indicators=["RSI", "MACD.macd", "MACD.signal", "EMA50"]
)

# Scrape all indicators
all_indicators = indicators_scraper.scrape(
    exchange="KRAKEN",
    symbol="BTCUSD",
    timeframe="4h",
    allIndicators=True
)

# With export functionality
export_scraper = Indicators(export_result=True, export_type='json')
result = export_scraper.scrape(
    exchange="BINANCE",
    symbol="BTCUSDT",
    timeframe="1d",
    indicators=["RSI", "Stoch.K"]
)
```

### Multiple Timeframes

```python
# Compare indicators across different timeframes
timeframes = ["1h", "4h", "1d", "1w"]

for tf in timeframes:
    result = indicators_scraper.scrape(
        exchange="BINANCE",
        symbol="BTCUSDT",
        timeframe=tf,
        indicators=["RSI", "Stoch.K"]
    )
    print(f"Timeframe {tf}: RSI = {result['data']['RSI']}")
```

## Common Mistakes and Solutions

### Mistake: Using Invalid Exchange

```python
# Wrong - Invalid exchange
result = indicators_scraper.scrape(
    exchange="INVALID_EXCHANGE",
    symbol="BTCUSD",
    indicators=["RSI"]
)

# Right - Valid exchange
result = indicators_scraper.scrape(
    exchange="BINANCE",
    symbol="BTCUSD",
    indicators=["RSI"]
)
```

**Solution**: Check [`tradingview_scraper/data/exchanges.txt`](https://github.com/smitkunpara/tradingview-scraper/blob/main/tradingview_scraper/data/exchanges.txt) for valid exchanges.

### Mistake: Empty Indicators List

```python
# Wrong - Empty indicators with allIndicators=False
result = indicators_scraper.scrape(
    exchange="BINANCE",
    symbol="BTCUSD",
    indicators=[]  # This will raise ValueError
)

# Right - Either provide indicators or use allIndicators=True
result = indicators_scraper.scrape(
    exchange="BINANCE",
    symbol="BTCUSD",
    allIndicators=True  # This works
)
```

**Solution**: Either provide a non-empty indicators list or set `allIndicators=True`.

### Mistake: Invalid Timeframe

```python
# Wrong - Invalid timeframe
result = indicators_scraper.scrape(
    exchange="BINANCE",
    symbol="BTCUSD",
    timeframe="2d",  # Not supported
    indicators=["RSI"]
)

# Right - Use supported timeframes
result = indicators_scraper.scrape(
    exchange="BINANCE",
    symbol="BTCUSD",
    timeframe="1d",  # Supported
    indicators=["RSI"]
)
```

**Solution**: Use timeframes from [`tradingview_scraper/data/timeframes.json`](https://github.com/smitkunpara/tradingview-scraper/blob/main/tradingview_scraper/data/timeframes.json).

### Mistake: Unsupported Indicators

```python
# Wrong - Invalid indicator
result = indicators_scraper.scrape(
    exchange="BINANCE",
    symbol="BTCUSD",
    indicators=["INVALID_INDICATOR"]  # Will raise ValueError
)

# Right - Use supported indicators
result = indicators_scraper.scrape(
    exchange="BINANCE",
    symbol="BTCUSD",
    indicators=["RSI", "Stoch.K"]  # Valid indicators
)
```

**Solution**: Check [`tradingview_scraper/data/indicators.txt`](https://github.com/smitkunpara/tradingview-scraper/blob/main/tradingview_scraper/data/indicators.txt) for valid indicators.

## Environment Setup

To use the indicators functionality, ensure your environment is properly set up:

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# Install dependencies
uv sync
```

## Supported Indicators Reference

The system supports 81 technical indicators organized into several categories:

### Momentum Indicators
- `RSI`, `RSI[1]`
- `Stoch.K`, `Stoch.D`, `Stoch.K[1]`, `Stoch.D[1]`
- `CCI20`, `CCI20[1]`
- `ADX`, `ADX+DI`, `ADX-DI`, `ADX+DI[1]`, `ADX-DI[1]`
- `AO`, `AO[1]`, `AO[2]`
- `Mom`, `Mom[1]`

### Moving Averages
- `EMA10`, `EMA20`, `EMA30`, `EMA50`, `EMA100`, `EMA200`
- `SMA10`, `SMA20`, `SMA30`, `SMA50`, `SMA100`, `SMA200`
- `VWMA`, `HullMA9`

### MACD Components
- `MACD.macd`, `MACD.signal`

### Pivot Points
- **Classic**: `Pivot.M.Classic.S3` through `Pivot.M.Classic.R3`
- **Fibonacci**: `Pivot.M.Fibonacci.S3` through `Pivot.M.Fibonacci.R3`
- **Camarilla**: `Pivot.M.Camarilla.S3` through `Pivot.M.Camarilla.R3`
- **Woodie**: `Pivot.M.Woodie.S3` through `Pivot.M.Woodie.R3`
- **DeMark**: `Pivot.M.Demark.S1`, `Pivot.M.Demark.Middle`, `Pivot.M.Demark.R1`

### Recommendation Indicators
- `Recommend.Other`, `Recommend.All`, `Recommend.MA`
- `Rec.Stoch.RSI`, `Rec.WR`, `Rec.BBPower`, `Rec.UO`, `Rec.Ichimoku`, `Rec.VWMA`, `Rec.HullMA9`

### Other Indicators
- `BBPower`, `UO`, `Ichimoku.BLine`, `close`, `W.R`

For the complete and most up-to-date list, refer to [`tradingview_scraper/data/indicators.txt`](https://github.com/smitkunpara/tradingview-scraper/blob/main/tradingview_scraper/data/indicators.txt).