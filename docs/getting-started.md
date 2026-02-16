# Getting Started

This guide covers installation, basic usage, response format, export options, and error handling for `tv_scraper`.

## Installation

### Using pip

```bash
pip install tradingview-scraper
```

### Using uv

```bash
uv add tradingview-scraper
```

### Development Installation

```bash
git clone https://github.com/smitkunpara/tv-scraper.git
cd tv-scraper
uv sync --extra dev
```

## Basic Usage

### Market Data

```python
from tv_scraper import Technicals, Overview, Fundamentals, Markets

# Technical indicators
tech = Technicals()
result = tech.get_technicals(exchange="NASDAQ", symbol="AAPL")
print(result["data"])  # {"RSI": 65.5, "MACD.macd": 1.23, ...}

# Symbol overview
overview = Overview()
result = overview.get_overview(exchange="NASDAQ", symbol="AAPL")
print(result["data"])

# Fundamental data
fundamentals = Fundamentals()
result = fundamentals.get_fundamentals(exchange="NASDAQ", symbol="AAPL")
print(result["data"])

# Market listings
markets = Markets()
result = markets.get_markets(market="america")
print(result["data"])
```

### Social

```python
from tv_scraper import Ideas, Minds, News

# Trading ideas
ideas = Ideas()
result = ideas.scrape(exchange="CRYPTO", symbol="BTCUSD")
for idea in result["data"]:
    print(idea["title"], idea["author"])

# Minds discussions
minds = Minds()
result = minds.get_minds(exchange="NASDAQ", symbol="AAPL")
print(result["data"])

# News
news = News()
result = news.scrape_headlines(exchange="NASDAQ", symbol="AAPL")
for article in result["data"]:
    print(article["title"])
```

### Screening

```python
from tv_scraper import Screener, MarketMovers, SymbolMarkets

# Stock screener
screener = Screener()
result = screener.screen(market="america")
print(result["data"])

# Market movers
movers = MarketMovers()
result = movers.scrape(market="america", category="gainers")
print(result["data"])

# Find all exchanges for a symbol
sym_markets = SymbolMarkets()
result = sym_markets.scrape(symbol="AAPL")
print(result["data"])
```

### Events

```python
from tv_scraper import Calendar

calendar = Calendar()
result = calendar.get_dividends(markets=["america"])
print(result["data"])
```

### Streaming

```python
from tv_scraper import Streamer, RealTimeData

# Get historical candles with indicators
streamer = Streamer(export_result=True, export_type="json")
result = streamer.get_candles(
    exchange="BINANCE",
    symbol="BTCUSDT",
    indicators=["RSI", "MACD"]
)

# Real-time price streaming
rt = RealTimeData()
for packet in rt.get_ohlcv(exchange="BINANCE", symbol="BTCUSDT"):
    print(packet)
```

## Response Format

All scraper methods return a **standardized response envelope**:

```python
{
    "status": "success",   # "success" or "failed"
    "data": { ... },       # the response payload (dict, list, etc.)
    "metadata": {          # contextual information
        "symbol": "AAPL",
        "exchange": "NASDAQ"
    },
    "error": None          # error string if status == "failed", else None
}
```

### Checking for Errors

```python
result = tech.get_technicals(exchange="NASDAQ", symbol="AAPL")

if result["status"] == "success":
    data = result["data"]
    # process data
else:
    print(f"Error: {result['error']}")
```

## Export Options

All scrapers support automatic export to JSON or CSV:

```python
# Export to JSON
tech = Technicals(export_result=True, export_type="json")
result = tech.get_technicals(exchange="NASDAQ", symbol="AAPL")
# File saved to export/ directory

# Export to CSV
tech = Technicals(export_result=True, export_type="csv")
result = tech.get_technicals(exchange="NASDAQ", symbol="AAPL")
```

Supported export types:
- `"json"` — saves as a `.json` file
- `"csv"` — saves as a `.csv` file

Invalid export types raise a `ValueError` at construction time:

```python
try:
    tech = Technicals(export_type="xml")  # ValueError!
except ValueError as e:
    print(e)
```

## Error Handling

Scrapers **never raise exceptions** for data errors. Instead, they return an error response:

```python
result = tech.get_technicals(exchange="INVALID", symbol="AAPL")
# {
#     "status": "failed",
#     "data": None,
#     "metadata": {"exchange": "INVALID", "symbol": "AAPL"},
#     "error": "Invalid exchange: 'INVALID'. ..."
# }
```

Only construction-time validation (like invalid `export_type`) raises exceptions.

### Exception Types

For advanced usage, the exception hierarchy is available in `tv_scraper.core.exceptions`:

```python
from tv_scraper.core import (
    TvScraperError,     # Base exception
    ValidationError,    # Invalid parameters
    DataNotFoundError,  # Requested data not found
    NetworkError,       # HTTP/WebSocket failures
    ExportError,        # File export failures
)
```
