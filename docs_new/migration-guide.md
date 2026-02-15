# Migration Guide

This guide helps you migrate from `tradingview_scraper` to `tv_scraper`.

## Import Path Mapping

| Old (`tradingview_scraper`)                          | New (`tv_scraper`)                                |
|------------------------------------------------------|---------------------------------------------------|
| `tradingview_scraper.symbols.technicals.Indicators`  | `tv_scraper.scrapers.market_data.indicators`      |
| `tradingview_scraper.symbols.ideas.Ideas`            | `tv_scraper.scrapers.social.ideas`                |
| `tradingview_scraper.symbols.news.News`              | `tv_scraper.scrapers.social.news`                 |
| `tradingview_scraper.symbols.minds.Minds`            | `tv_scraper.scrapers.social.minds`                |
| `tradingview_scraper.symbols.overview.Overview`      | `tv_scraper.scrapers.market_data.overview`        |
| `tradingview_scraper.symbols.cal.Calendar`           | `tv_scraper.scrapers.events.calendar`             |
| `tradingview_scraper.symbols.screener.Screener`      | `tv_scraper.scrapers.screening.screener`          |
| `tradingview_scraper.symbols.market_movers.MarketMovers` | `tv_scraper.scrapers.screening.market_movers` |
| `tradingview_scraper.symbols.markets.Markets`        | `tv_scraper.scrapers.screening.markets`           |
| `tradingview_scraper.symbols.fundamental_graphs.FundamentalGraphs` | `tv_scraper.scrapers.market_data.fundamental_graphs` |
| `tradingview_scraper.symbols.symbol_markets.SymbolMarkets` | `tv_scraper.scrapers.market_data.symbol_markets` |
| `tradingview_scraper.symbols.stream.price.RealTimeData` | `tv_scraper.streaming.price`                  |
| `tradingview_scraper.symbols.stream.streamer.Streamer` | `tv_scraper.streaming.streamer`                |
| `tradingview_scraper.symbols.exceptions`             | `tv_scraper.core.exceptions`                      |
| `tradingview_scraper.symbols.utils`                  | `tv_scraper.utils`                                |

## Parameter Renames

| Old Parameter       | New Parameter   | Notes                                      |
|---------------------|-----------------|--------------------------------------------|
| `export_result`     | `export_result` | No change                                  |
| `export_type`       | `export_type`   | No change                                  |
| Mixed exchange+symbol | `exchange`, `symbol` | Now always separate parameters        |
| `symbol` (with `EXCHANGE:SYMBOL`) | `exchange` + `symbol` | Split into two params |

## Response Format Changes

### Old Format
Responses varied by scraper — some returned raw dicts, some returned lists, some returned pandas DataFrames.

### New Format
All scrapers return a **standardized response envelope**:

```python
# Old
result = scraper.scrape()
# result = {"AAPL": {"RSI": 65.5, ...}}

# New
result = scraper.get_data(exchange="NASDAQ", symbol="AAPL")
# result = {
#     "status": "success",
#     "data": {"RSI": 65.5, ...},
#     "metadata": {"symbol": "AAPL", "exchange": "NASDAQ"},
#     "error": None
# }
```

### Error Handling
```python
# Old — could raise exceptions
try:
    result = scraper.scrape()
except Exception as e:
    handle_error(e)

# New — never raises, returns error response
result = scraper.get_data(exchange="INVALID", symbol="AAPL")
if result["status"] == "failed":
    print(result["error"])
```

## Exception Hierarchy

| Old                          | New                              |
|------------------------------|----------------------------------|
| `DataNotFoundError`          | `tv_scraper.core.exceptions.DataNotFoundError` |
| Generic `Exception`/`ValueError` | `tv_scraper.core.exceptions.ValidationError` |
| Network errors (unhandled)   | `tv_scraper.core.exceptions.NetworkError` |
| Export errors (logged only)  | `tv_scraper.core.exceptions.ExportError` |
| —                            | `tv_scraper.core.exceptions.TvScraperError` (base) |
