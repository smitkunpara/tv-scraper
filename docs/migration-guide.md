# Migration Guide: tradingview_scraper → tv-scraper

This guide covers all breaking changes when migrating from the legacy `tradingview_scraper` package to the new `tv-scraper` v1.0.2.

## Package Rename

The package has been reorganized from a flat structure under `tradingview_scraper.symbols` to a modular architecture under `tv_scraper`.

```python
# Old
from tradingview_scraper.symbols.technicals import Indicators

# New
from tv_scraper import Technicals
# or full path:
from tv_scraper.scrapers.market_data.technicals import Technicals
```

## Import Path Changes

### Scraper Classes

| Old Import | New Import |
|---|---|
| `tradingview_scraper.symbols.technicals.Indicators` | `tv_scraper.scrapers.market_data.technicals.Technicals` |
| `tradingview_scraper.symbols.overview.Overview` | `tv_scraper.scrapers.market_data.overview.Overview` |
| `tradingview_scraper.symbols.fundamental_graphs.FundamentalGraphs` | `tv_scraper.scrapers.market_data.fundamentals.Fundamentals` |
| `tradingview_scraper.symbols.markets.Markets` | `tv_scraper.scrapers.market_data.markets.Markets` |
| `tradingview_scraper.symbols.ideas.Ideas` | `tv_scraper.scrapers.social.ideas.Ideas` |
| `tradingview_scraper.symbols.minds.Minds` | `tv_scraper.scrapers.social.minds.Minds` |
| `tradingview_scraper.symbols.news.News` | `tv_scraper.scrapers.social.news.News` |
| `tradingview_scraper.symbols.screener.Screener` | `tv_scraper.scrapers.screening.screener.Screener` |
| `tradingview_scraper.symbols.market_movers.MarketMovers` | `tv_scraper.scrapers.screening.market_movers.MarketMovers` |
| `tradingview_scraper.symbols.symbol_markets.SymbolMarkets` | `tv_scraper.scrapers.screening.symbol_markets.SymbolMarkets` |
| `tradingview_scraper.symbols.cal.Calendar` | `tv_scraper.scrapers.events.calendar.Calendar` |
| `tradingview_scraper.symbols.stream.streamer.Streamer` | `tv_scraper.streaming.streamer.Streamer` |

### Convenience Imports

All public classes are available directly from `tv_scraper`:

```python
from tv_scraper import (
    Technicals, Overview, Fundamentals, Markets,
    Ideas, Minds, News,
    Screener, MarketMovers, SymbolMarkets,
    Calendar,
    Streamer,
)
```

### Core Modules

| Old Import | New Import |
|---|---|
| `tradingview_scraper.symbols.exceptions` | `tv_scraper.core.exceptions` |
| `tradingview_scraper.symbols.utils` | `tv_scraper.utils` |

## Class Renames

| Old Class | New Class | Notes |
|---|---|---|
| `Indicators` | `Technicals` | Renamed for clarity |
| `FundamentalGraphs` | `Fundamentals` | Shortened name |
| `Calendar` | `Calendar` | No change |
| All others | Same name | No change |

## Method Renames

| Module | Old Method | New Method |
|---|---|---|
| Technicals | `Indicators.get_data()` | `Technicals.get_technicals()` |
| Overview | `Overview.get_symbol_overview()` | `Overview.get_overview()` |
| Fundamentals | `FundamentalGraphs.get_data()` | `Fundamentals.get_fundamentals()` |
| Ideas | `Ideas.get_ideas()` | `Ideas.get_ideas()` |
| News | `News.scrape_news_content()` | `News.scrape_content()` |
| News | `News.get_headlines()` | `News.get_headlines()` |
| Screener | `Screener.get_screener()` | `Screener.get_screener()` |
| MarketMovers | `MarketMovers.get_market_movers()` | `MarketMovers.get_market_movers()` |
| SymbolMarkets | `SymbolMarkets.get_symbol_markets()` | `SymbolMarkets.get_symbol_markets()` |
| Calendar | `Calendar.get_dividends()` | `Calendar.get_dividends()` |
| Calendar | `Calendar.get_earnings()` | `Calendar.get_earnings()` |
| Minds | `Minds.get_minds()` | `Minds.get_minds()` |
| Markets | `Markets.get_markets()` | `Markets.get_markets()` |
| Streamer | `Streamer.stream()` | `Streamer.get_candles()` |

## Parameter Changes

### Exchange and Symbol Splitting

In the old API, some methods accepted a combined `"EXCHANGE:SYMBOL"` string. The new API **always** uses separate parameters:

```python
# Old
result = scraper.get_technicals(symbol="NASDAQ:AAPL")

# New
result = scraper.get_technicals(exchange="NASDAQ", symbol="AAPL")
```

### Parameter Renames

| Old Parameter | New Parameter | Module(s) | Notes |
|---|---|---|---|
| `columns` | `fields` | Screener, MarketMovers | Renamed for consistency |
| `sort` | `sort_by` | Screener | Renamed for clarity |
| `symbol` (combined) | `exchange` + `symbol` | All scrapers | Always split |
| `websocket_jwt_token` | `jwt_token` | Streamer | Shortened |

### New Parameters

| Parameter | Module(s) | Description |
|---|---|---|
| `timeout` | All scrapers | HTTP request timeout (default: 10s) |
| `export_result` | All scrapers | Enable data export (default: False) |
| `export_type` | All scrapers | Export format: `"json"` or `"csv"` |

## Response Format Changes

### Old Format

Responses varied by scraper — some returned raw dicts, some returned lists, some returned pandas DataFrames.

```python
# Old — inconsistent return types
result = technicals.get_technicals(...)
# Could be: dict, list, DataFrame, or raise an exception
```

### New Format — Standardized Envelope

All scrapers return a **standardized response envelope**:

```python
result = technicals.get_technicals(exchange="NASDAQ", symbol="AAPL")
# Always returns:
{
    "status": "success",       # or "failed"
    "data": { ... },           # the payload (dict, list, etc.)
    "metadata": {              # contextual info
        "symbol": "AAPL",
        "exchange": "NASDAQ"
    },
    "error": None              # error string if status == "failed"
}
```

### Accessing Data

```python
# Old
data = result  # or result["AAPL"] or result.to_dict()

# New
if result["status"] == "success":
    data = result["data"]
```

## Error Handling Changes

### Old — Exceptions

```python
# Old — could raise any exception
try:
    result = scraper.get_technicals(symbol="INVALID")
except DataNotFoundError as e:
    handle_error(e)
except Exception as e:
    handle_error(e)
```

### New — Error Responses

Scrapers **never raise** for data/network errors. They return error envelopes:

```python
# New — always returns a dict
result = scraper.get_technicals(exchange="INVALID", symbol="AAPL")
if result["status"] == "failed":
    print(result["error"])
    # "Invalid exchange: 'INVALID'. Did you mean: ..."
```

Only construction-time validation raises exceptions:

```python
# This still raises ValueError
scraper = Technicals(export_type="xml")
```

## Exception Hierarchy

| Old | New |
|---|---|
| `DataNotFoundError` | `tv_scraper.core.exceptions.DataNotFoundError` |
| Generic `Exception` / `ValueError` | `tv_scraper.core.exceptions.ValidationError` |
| Network errors (unhandled) | `tv_scraper.core.exceptions.NetworkError` |
| Export errors (logged only) | `tv_scraper.core.exceptions.ExportError` |
| — | `tv_scraper.core.exceptions.TvScraperError` (base class) |

## Architecture Changes

### BaseScraper

All scraper classes now inherit from `BaseScraper`, providing:
- `_success_response()` / `_error_response()` for envelope formatting
- `_make_request()` for HTTP with default headers and timeout
- `_export()` for JSON/CSV file export
- `self.validator` — shared `DataValidator` singleton

### DataValidator

A singleton that validates exchanges, indicators, timeframes, etc. against JSON data files. Provides fuzzy suggestions for invalid inputs.

```python
from tv_scraper.core import DataValidator

validator = DataValidator()
validator.validate_exchange("NASDAQ")  # True
validator.validate_exchange("TYPO")    # raises ValidationError with suggestions
```

## Breaking Changes Summary

1. **Package rename**: `tradingview_scraper` → `tv-scraper`
2. **Class renames**: `Indicators` → `Technicals`, `FundamentalGraphs` → `Fundamentals`
3. **Method renames**: `get_symbol_overview` → `get_overview`, `stream` → `get_candles`, etc.
4. **Parameter splitting**: `symbol="EXCHANGE:SYMBOL"` → `exchange="...", symbol="..."`
5. **Parameter renames**: `columns` → `fields`, `sort` → `sort_by`
6. **Response format**: Raw data → standardized envelope with `status`, `data`, `metadata`, `error`
7. **Error handling**: Exceptions → error responses (scrapers never raise for data errors)
8. **Export validation**: Invalid `export_type` raises `ValueError` at construction

## Side-by-Side Example

### Old Code

```python
from tradingview_scraper.symbols.technicals import Indicators

indicators = Indicators()
try:
    result = technicals.get_technicals(
        symbol="NASDAQ:AAPL",
        indicators=["RSI", "MACD.macd"]
    )
    rsi = result.get("RSI")
except Exception as e:
    print(f"Error: {e}")
```

### New Code

```python
from tv_scraper import Technicals

tech = Technicals()
result = tech.get_technicals(
    exchange="NASDAQ",
    symbol="AAPL",
    technical_indicators=["RSI", "MACD.macd"]
)
if result["status"] == "success":
    rsi = result["data"].get("RSI")
else:
    print(f"Error: {result['error']}")
```
