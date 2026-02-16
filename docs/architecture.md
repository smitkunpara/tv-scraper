# Architecture Overview

## Package Structure

The `tv_scraper` package is organized into a clean, modular architecture:

```
tv_scraper/
├── __init__.py              # Package root, exports __version__
├── core/                    # Core infrastructure
│   ├── base.py              # BaseScraper — parent class for all scrapers
│   ├── constants.py         # Shared constants (URLs, defaults, status codes)
│   ├── exceptions.py        # Exception hierarchy
│   ├── types.py             # TypedDict definitions for response formats
│   └── validators.py        # DataValidator singleton for input validation
├── utils/                   # Shared utilities
│   ├── helpers.py           # User-agent generation, symbol formatting
│   ├── http.py              # HTTP request wrapper with error handling
│   └── io.py                # File export (JSON/CSV) utilities
├── data/                    # Static data files (JSON)
│   ├── exchanges.json       # Valid exchange names
│   ├── indicators.json      # Valid indicator names
│   ├── timeframes.json      # Timeframe key → API value mappings
│   ├── languages.json       # Language name → code mappings
│   ├── areas.json           # Geographic area → code mappings
│   └── news_providers.json  # Valid news provider slugs
├── scrapers/                # HTTP-based scrapers
│   ├── market_data/         # Indicators, overview, fundamental graphs
│   ├── social/              # Ideas, minds, news
│   ├── screening/           # Screener, market movers, markets
│   └── events/              # Calendar (earnings, dividends)
└── streaming/               # WebSocket-based real-time data
```

## Module Categories

### Market Data (`scrapers/market_data/`)
Scrapers for technical indicators, symbol overviews, and fundamental financial data. These use the TradingView Scanner API and symbol page scraping.

### Social (`scrapers/social/`)
Scrapers for community-generated content: trading ideas, Minds discussions, and news articles.

### Screening (`scrapers/screening/`)
Screener tools for filtering and ranking symbols: stock/crypto/forex screeners, market movers (gainers/losers), and market listings.

### Events (`scrapers/events/`)
Calendar-based scrapers for corporate events like earnings and dividend dates.

### Streaming (`streaming/`)
WebSocket-based real-time data streaming for OHLCV candles, indicators, and watchlist data.

## Core Concepts

### BaseScraper
All HTTP scrapers inherit from `BaseScraper`, which provides:
- **Standardized response envelope** via `_success_response()` and `_error_response()`
- **HTTP request handling** via `_make_request()` with automatic User-Agent and timeout
- **Data export** via `_export()` supporting JSON and CSV formats
- **Scanner row mapping** via `_map_scanner_rows()` for TradingView scanner API responses
- **Input validation** via the shared `DataValidator` instance

### DataValidator
A singleton that loads all validation data (exchanges, indicators, timeframes, etc.) from JSON files once. All validation methods raise `ValidationError` with helpful suggestions for invalid input.

### Response Envelope
Every scraper method returns a standardized dict:
```python
{
    "status": "success" | "failed",
    "data": <payload or None>,
    "metadata": {"symbol": "...", "exchange": "...", ...},
    "error": <error message or None>
}
```

### Export Pattern
All scrapers accept `export_result` and `export_type` constructor parameters. When enabled, results are automatically saved to the `export/` directory with timestamped filenames.
