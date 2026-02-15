# Quick Start Guide

## Overview

This guide provides minimal working examples to help you quickly get started with the TradingView Scraper library.

!!! note "Supported Data"
    For a complete list of supported exchanges, symbols, and other data types, see [Supported Data](supported_data.md).

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

# Stream OHLCV data for BTCUSD
result = streamer.stream(
    exchange="BINANCE",
    symbol="BTCUSD",
    timeframe="1m",
    numb_price_candles=3
)

print("Streaming Result:")
print(f"OHLCV candles: {len(result['ohlcv'])}")
print(f"Indicators: {len(result['indicator'])}")
```

**Expected Output:**
```text
Streaming Result:
OHLCV candles: 3
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
print(f"OHLCV candles: {len(result['ohlcv'])}")
print(f"RSI data points: {len(result['indicator']['STD;RSI'])}")
```

**Expected Output:**
```text
Streaming with Indicators:
OHLCV candles: 3
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