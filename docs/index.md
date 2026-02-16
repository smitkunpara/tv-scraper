# tv_scraper Documentation

**tv_scraper** is a Python library for scraping trading data, ideas, news, and real-time market information from TradingView.com. It provides a clean, modular API with standardized response formats and built-in data export.

## Installation

```bash
pip install tradingview-scraper
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add tradingview-scraper
```

## Quick Start

```python
from tv_scraper import Technicals, Ideas, Screener

# Get technical indicators
tech = Technicals()
result = tech.scrape(exchange="NASDAQ", symbol="AAPL")
print(result["data"])

# Fetch trading ideas
ideas = Ideas()
result = ideas.scrape(exchange="CRYPTO", symbol="BTCUSD")
print(result["data"])

# Screen stocks
screener = Screener()
result = screener.screen(market="america")
print(result["data"])
```

All methods return a **standardized response envelope**:

```python
{
    "status": "success",   # or "failed"
    "data": { ... },       # the payload
    "metadata": { ... },   # symbol, exchange, etc.
    "error": None          # error message if status == "failed"
}
```

## Available Modules

### Market Data

| Module | Description |
|--------|-------------|
| [Technicals](scrapers/technicals.md) | Technical indicators via TradingView scanner API |
| [Overview](scrapers/overview.md) | Symbol overview data (profile, stats, financials) |
| [Fundamentals](scrapers/fundamentals.md) | Fundamental financial graphs and metrics |
| [Markets](scrapers/markets.md) | Market listings and top stocks |

### Social

| Module | Description |
|--------|-------------|
| [Ideas](scrapers/ideas.md) | Trading ideas from the TradingView community |
| [Minds](scrapers/minds.md) | Minds community discussions |
| [News](scrapers/news.md) | News headlines and content for symbols |

### Screening

| Module | Description |
|--------|-------------|
| [Screener](scrapers/screener.md) | Stock/crypto/forex screener with custom filters |
| [Market Movers](scrapers/market_movers.md) | Gainers, losers, and most active symbols |
| [Symbol Markets](scrapers/symbol_markets.md) | Find all exchanges where a symbol is traded |

### Events

| Module | Description |
|--------|-------------|
| [Calendar](scrapers/calendar.md) | Earnings and dividend calendar events |

### Streaming

| Module | Description |
|--------|-------------|
| [Streamer](streaming/streamer.md) | Real-time OHLCV + indicator streaming |
| [RealTimeData](streaming/realtime-price.md) | Simple OHLCV and watchlist streaming |

## Architecture

See the [Architecture Guide](architecture.md) for details on the modular design, base classes, and data flow.

## Migration from tradingview_scraper

If you're upgrading from the legacy `tradingview_scraper` package, see the [Migration Guide](migration-guide.md).

## API Conventions

See [API Conventions](api-conventions.md) for details on response formats, error handling, and export options.
