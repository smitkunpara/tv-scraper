# Technicals (Technical Indicators)

## Overview

Fetch technical analysis indicator values (RSI, MACD, EMA, Stochastic, etc.) for any symbol on any supported exchange via the TradingView scanner API.

## Import

```python
from tv_scraper.scrapers.market_data import Technicals
```

## Constructor

```python
Technicals(export_result: bool = False, export_type: str = "json", timeout: int = 10)
```

| Parameter       | Type   | Default | Description                        |
|-----------------|--------|---------|------------------------------------|
| `export_result` | `bool` | `False` | Whether to export results to file. |
| `export_type`   | `str`  | `"json"`| Export format: `"json"` or `"csv"`. |
| `timeout`       | `int`  | `10`    | HTTP request timeout in seconds.   |

## `scrape()` Method

```python
scrape(
    exchange: str = "BITSTAMP",
    symbol: str = "BTCUSD",
    timeframe: str = "1d",
    technical_indicators: Optional[List[str]] = None,
    all_indicators: bool = False,
    fields: Optional[List[str]] = None,
) -> Dict[str, Any]
```

| Parameter              | Type               | Default      | Description                                                        |
|------------------------|--------------------|--------------|--------------------------------------------------------------------|
| `exchange`             | `str`              | `"BITSTAMP"`  | Valid exchange name (e.g. `"BINANCE"`, `"COINBASE"`).              |
| `symbol`               | `str`              | `"BTCUSD"`    | Trading symbol.                                                    |
| `timeframe`            | `str`              | `"1d"`        | Timeframe: `"1m"`, `"5m"`, `"1h"`, `"4h"`, `"1d"`, `"1w"`, etc. |
| `technical_indicators` | `Optional[List[str]]` | `None`     | Specific indicator names to fetch (e.g. `["RSI", "MACD.macd"]`).  |
| `all_indicators`       | `bool`             | `False`       | If `True`, fetches all known indicators.                           |
| `fields`               | `Optional[List[str]]` | `None`     | Filter output to include only these indicator names.               |

### Constraints

- **Exchange** must be a valid exchange from [Supported Exchanges](../supported_data.md#supported-exchanges).
- **Timeframe** must be one of the supported timeframes.
- **Indicators** must be valid indicator names. Use `all_indicators=True` to fetch all.
- If `all_indicators` is `False`, `technical_indicators` must be provided.

## Response Format

All responses follow the standard envelope format:

### Success

```json
{
  "status": "success",
  "data": {
    "RSI": 54.21,
    "Recommend.All": 0.15,
    "CCI20": 112.45,
    "Stoch.K": 78.50,
    "EMA20": 42150.25,
    "MACD.macd": 150.12,
    "MACD.signal": 120.45
    ...
    (other indicators)
  },
  "metadata": {
    "exchange": "BINANCE",
    "symbol": "BTCUSD",
    "timeframe": "1d"
  },
  "error": null
}
```

### Error

```python
{
    "status": "failed",
    "data": None,
    "metadata": {},
    "error": "Invalid exchange: 'INVALID'. Did you mean one of: ..."
}
```

Errors are **never raised** — they are always returned as error responses.

## Usage Examples

### Specific Indicators

```python
from tv_scraper.scrapers.market_data import Technicals

scraper = Technicals()
data = scraper.scrape(
    exchange="BINANCE",
    symbol="BTCUSDT",
    timeframe="4h",
    technical_indicators=["RSI", "EMA50", "MACD.macd"],
)
print(data["data"])
# {"RSI": 58.4, "EMA50": 42000.0, "MACD.macd": 150.5}
```

### All Indicators

```python
full = scraper.scrape(
    exchange="COINBASE",
    symbol="ETHUSD",
    timeframe="1d",
    all_indicators=True,
)
print(len(full["data"]))  # All available indicators
```

### With Export

```python
scraper = Technicals(export_result=True, export_type="csv")
data = scraper.scrape(
    exchange="BINANCE",
    symbol="BTCUSD",
    technical_indicators=["RSI", "Stoch.K"],
)
# Results are saved to export/ directory automatically
```

### Field Filtering

```python
data = scraper.scrape(
    exchange="BINANCE",
    symbol="BTCUSD",
    all_indicators=True,
    fields=["RSI", "EMA50"],  # Only include these in output
)
```

## Migration from Old API

| Old (`tradingview_scraper`)                          | New (`tv_scraper`)                                    |
|------------------------------------------------------|-------------------------------------------------------|
| `from tradingview_scraper import Indicators`         | `from tv_scraper.scrapers.market_data import Technicals` |
| `Indicators()`                                       | `Technicals()`                                        |
| `scrape(indicators=["RSI"])`                         | `scrape(technical_indicators=["RSI"])`                |
| `scrape(allIndicators=True)`                         | `scrape(all_indicators=True)`                         |
| Raises `ValueError` on invalid input                | Returns `{"status": "failed", "error": "..."}` |
| Response: `{"status": "success", "data": {...}}`    | Response: `{"status": "success", "data": {...}, "metadata": {...}, "error": None}` |

### Key Differences

1. **Class name**: `Indicators` → `Technicals`
2. **Parameter naming**: `allIndicators` → `all_indicators`, `indicators` → `technical_indicators` (snake_case)
3. **Error handling**: No more `ValueError` raises — all errors are returned in the response envelope
4. **Response format**: Standardized 4-key envelope (`status`, `data`, `metadata`, `error`)
5. **New features**: `fields` parameter for output filtering, `timeout` parameter, `metadata` in response
