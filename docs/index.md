# tv-scraper Documentation

`tv-scraper` helps you fetch TradingView data through a consistent Python API. The docs here focus on what to call, which inputs are accepted, what the response looks like, and where to find the exact valid values quickly.

[:material-rocket-launch: Get Started](getting-started.md){ .md-button .md-button--primary }
[:material-format-list-bulleted: Validation Reference](supported_data.md){ .md-button .md-button--secondary }

## Start Here

Use these pages when you want the fastest path to a working call:

- [Getting Started](getting-started.md): install, first request, exports, cookies, and error checks.
- [API Basics](api-conventions.md): request patterns, response envelope, and one invalid-input example.
- [Reference Overview](reference/index.md): jump straight to exchanges, timeframes, languages, news filters, and releases.
- [Releases & Versioning](reference/releases.md): see which docs versions exist and how the version switcher works.

## Quick Example

```python
from tv_scraper import Technicals

scraper = Technicals()
result = scraper.get_technicals(
    exchange="NASDAQ",
    symbol="AAPL",
    timeframe="1d",
    technical_indicators=["RSI", "MACD.macd"],
)

if result["status"] == "success":
    print(result["data"])
else:
    print(result["error"])
```

Every public method returns the same outer shape:

```python
{
    "status": "success" | "failed",
    "data": ...,
    "metadata": {...},
    "warnings": [str, ...],
    "error": None | "message",
}
```

## Choose By Task

### Market Data

| Page | Use it for |
|------|------------|
| [Technicals](scrapers/technicals.md) | Scanner indicators such as RSI, EMA, MACD, and pivots |
| [Fundamentals](scrapers/fundamentals.md) | Fundamental fields for one `exchange:symbol` |
| [Markets](scrapers/markets.md) | Ranked lists of symbols in a market |
| [Options](scrapers/options.md) | Option-chain lookups by expiry, strike, or both |

### Screening & Discovery

| Page | Use it for |
|------|------------|
| [Screener](scrapers/screener.md) | Custom filters and sorted scan results |
| [Market Movers](scrapers/market_movers.md) | Gainers, losers, most active, and stock-specific movers |
| [Symbol Markets](scrapers/symbol_markets.md) | Find where a symbol trades across scanners |
| [Calendar](scrapers/calendar.md) | Earnings and dividends in a date window |

### Social & Content

| Page | Use it for |
|------|------------|
| [Ideas](scrapers/ideas.md) | Community trading ideas by symbol |
| [Minds](scrapers/minds.md) | Community posts with cursor pagination |
| [News](scrapers/news.md) | Flow news, symbol headlines, and story content |
| [Pine](scrapers/pine.md) | Authenticated Pine Script operations |

### Streaming

| Page | Use it for |
|------|------------|
| [Streaming Overview](streaming/index.md) | Which streamer to use |
| [CandleStreamer](streaming/candle_streamer.md) | OHLCV candles and indicator studies |
| [ForecastStreamer](streaming/forecast_streamer.md) | Analyst forecast data for stocks |
| [Streamer (Legacy)](streaming/streamer.md) | Backward-compatible wrapper |

## Find Valid Values Faster

If a method asks for a specific exchange, timeframe, provider, language, or news filter, use the exact section links instead of scanning the whole docs site:

- [Exchanges](supported_data.md#exchanges)
- [Technical indicators](supported_data.md#technical-indicators)
- [Timeframes](supported_data.md#timeframes)
- [Languages](supported_data.md#languages)
- [News areas](supported_data.md#news-areas)
- [News providers](supported_data.md#news-providers)
- [News countries](supported_data.md#news-countries)

## Versions

Versioned docs are designed around releases. Docs were introduced in `v0.5.0`, and the site is set up to use `mike` for release-aware navigation when published. See [Releases & Versioning](reference/releases.md) for the current version list and publishing policy.
