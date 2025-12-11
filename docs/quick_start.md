# Quick Start Guide

## Overview

This guide provides minimal working examples to help you quickly get started with the TradingView Scraper library. These examples cover the core functionality including ideas scraping, indicators fetching, and real-time streaming.

## Why This Quick Start Exists

The quick start guide exists to:

- Provide immediate, working examples for new users
- Demonstrate core functionality with minimal code
- Help users understand basic usage patterns
- Serve as a foundation for more advanced usage
- Reduce time-to-first-success for new developers

## Prerequisites

Before running these examples, ensure you have:

1. Completed the [installation process](installation.md)
2. Activated your virtual environment
3. Installed all required dependencies

## Basic Examples

### 1. Scraping Ideas

```python
from tradingview_scraper.symbols.ideas import Ideas

# Initialize ideas scraper
ideas_scraper = Ideas()

# Scrape recent ideas for BTCUSD
ideas = ideas_scraper.scrape(
    symbol="BTCUSD",
    sort="recent",
    startPage=1,
    endPage=1
)

print(f"Found {len(ideas)} ideas")
for idea in ideas:
    print(f"Title: {idea['title']}")
    print(f"Author: {idea['author']}")
    print(f"Likes: {idea['likes_count']}")
    print("---")
```

**Expected Output:**
```text
Found 5 ideas
Title: Bitcoin Analysis: Bullish Momentum Building
Author: CryptoAnalyst
Likes: 45
---
Title: BTCUSD Technical Breakdown
Author: MarketTrader
Likes: 32
---
```

### 2. Fetching Indicators

```python
from tradingview_scraper.symbols.technicals import Indicators

# Initialize indicators scraper
indicators_scraper = Indicators()

# Fetch RSI and Stochastic indicators for BTCUSD on Binance
indicators = indicators_scraper.scrape(
    exchange="BINANCE",
    symbol="BTCUSD",
    timeframe="1d",
    indicators=["RSI", "Stoch.K"]
)

print("Indicators Data:")
print(f"RSI: {indicators['data']['RSI']}")
print(f"Stoch.K: {indicators['data']['Stoch.K']}")
```

**Expected Output:**
```text
Indicators Data:
RSI: 46.34926112
Stoch.K: 40.40173723
```

### 3. Real-Time Streaming (Basic)

```python
from tradingview_scraper.symbols.stream import Streamer

# Initialize streamer (requires JWT token for indicators)
streamer = Streamer(
    export_result=False,
    export_type='json'
)

# Stream OHLC data for BTCUSD
result = streamer.stream(
    exchange="BINANCE",
    symbol="BTCUSD",
    timeframe="1m",
    numb_price_candles=3
)

print("Streaming Result:")
print(f"OHLC candles: {len(result['ohlc'])}")
print(f"Indicators: {len(result['indicator'])}")
```

**Expected Output:**
```text
Streaming Result:
OHLC candles: 3
Indicators: 0
```

### 4. Streaming with Indicators

```python
from tradingview_scraper.symbols.stream import Streamer

# Initialize streamer with JWT token
streamer = Streamer(
    export_result=False,
    export_type='json',
    websocket_jwt_token="your_jwt_token_here"  # Replace with your token
)

# Stream with RSI indicator
result = streamer.stream(
    exchange="BINANCE",
    symbol="BTCUSD",
    indicators=[("STD;RSI", "37.0")],
    timeframe="1m",
    numb_price_candles=3
)

print("Streaming with Indicators:")
print(f"OHLC candles: {len(result['ohlc'])}")
print(f"RSI data points: {len(result['indicator']['STD;RSI'])}")
```

**Expected Output:**
```text
Streaming with Indicators:
OHLC candles: 3
RSI data points: 3
```

## Advanced Examples

### 5. Exporting Data

```python
from tradingview_scraper.symbols.ideas import Ideas

# Enable export to JSON
ideas_scraper = Ideas(export_result=True, export_type='json')

# Scrape and export ideas
ideas = ideas_scraper.scrape(
    symbol="ETHUSD",
    sort="popular",
    startPage=1,
    endPage=2
)

print(f"Exported {len(ideas)} ideas to JSON file")
```

### 6. Using Cookies for Captcha Bypass

```python
from tradingview_scraper.symbols.ideas import Ideas

# Use TradingView cookie to bypass captcha
ideas_scraper = Ideas(
    cookie="your_tradingview_cookie_here"  # Get from browser dev tools
)

# Scrape ideas without captcha interruptions
ideas = ideas_scraper.scrape(symbol="BTCUSD")
print(f"Successfully scraped {len(ideas)} ideas with cookie")
```

### 7. Multi-Page Scraping

```python
from tradingview_scraper.symbols.ideas import Ideas

ideas_scraper = Ideas()

# Scrape ideas across multiple pages
ideas = ideas_scraper.scrape(
    symbol="BTCUSD",
    sort="popular",
    startPage=1,
    endPage=5  # Scrape 5 pages
)

print(f"Total ideas from 5 pages: {len(ideas)}")
```

## Common Usage Patterns

### Input Specification

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `symbol` | str | "BTCUSD" | Trading symbol (e.g., "BTCUSD", "AAPL") |
| `exchange` | str | - | Exchange name (e.g., "BINANCE", "NASDAQ") |
| `timeframe` | str | "1d" | Timeframe (e.g., "1m", "1h", "1d", "1w") |
| `indicators` | list | [] | List of indicator names (e.g., ["RSI", "Stoch.K"]) |
| `sort` | str | "recent" | Sort order ("recent" or "popular") |
| `startPage` | int | 1 | Starting page number |
| `endPage` | int | 1 | Ending page number |
| `export_result` | bool | False | Enable file export |
| `export_type` | str | "json" | Export format ("json" or "csv") |

### Output Specification

All methods return structured data in the following format:

```python
{
    "status": "success",  # or "error"
    "data": [...]         # List of results or dictionary of values
    # Additional metadata may be included
}
```

## Behavioral Notes

1. **Rate Limiting**: Free TradingView accounts have limitations (e.g., 2 indicator maximum for streaming)
2. **Captcha Handling**: Use cookies to bypass captcha challenges
3. **Error Handling**: Invalid inputs will raise appropriate exceptions
4. **Data Consistency**: All modules use the same data validation

## Common Mistakes and Solutions

### Mistake: Using unsupported exchange

```python
# Wrong
indicators_scraper.scrape(exchange="INVALID_EXCHANGE", ...)

# Right
indicators_scraper.scrape(exchange="BINANCE", ...)
```

**Solution**: Check [supported exchanges](supported_data.md#supported-exchanges)

### Mistake: Exceeding indicator limit

```python
# This will fail on free accounts
streamer.stream(
    indicators=[("STD;RSI", "37.0"), ("STD;MACD", "31.0"), ("STD;CCI", "37.0")]
)

# Right (max 2 indicators for free accounts)
streamer.stream(
    indicators=[("STD;RSI", "37.0"), ("STD;MACD", "31.0")]
)
```

**Solution**: Free accounts can only stream 2 indicators. Upgrade to premium or use fewer indicators.

## Environment Setup Reminder

```bash
# Quick setup commands
uv venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows
uv sync
```

This quick start guide provides minimal working examples to help you begin using the TradingView Scraper library immediately. Refer to the specific module documentation for more advanced features and detailed usage instructions.