# Overview

## Overview

The Overview module provides comprehensive functionality to retrieve detailed information about financial symbols from TradingView, including profile data, market statistics, financial metrics, performance indicators, and technical analysis.

## Import

```python
from tv_scraper.scrapers.market_data import Overview
```

## Constructor

```python
Overview(export_result: bool = False, export_type: str = "json", timeout: int = 10)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `export_result` | `bool` | `False` | Whether to export results to a file |
| `export_type` | `str` | `"json"` | Export format: `"json"` or `"csv"` |
| `timeout` | `int` | `10` | HTTP request timeout in seconds |

## Methods

### `get_overview`

```python
get_overview(
    exchange: str,
    symbol: str,
    fields: Optional[List[str]] = None,
) -> Dict[str, Any]
```

Get comprehensive overview data for a symbol. When `fields` is `None`, all fields from every category are fetched.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `exchange` | `str` | Yes | Exchange name (e.g. `"NASDAQ"`, `"BITSTAMP"`) |
| `symbol` | `str` | Yes | Trading symbol (e.g. `"AAPL"`, `"BTCUSD"`) |
| `fields` | `List[str]` | No | Specific fields to retrieve. Defaults to all fields. |

### Category Methods

Each category method takes `exchange` and `symbol` and internally calls `get_overview` with predefined field lists:

| Method | Fields Used |
|--------|-------------|
| `get_profile(exchange, symbol)` | `BASIC_FIELDS` — name, description, type, subtype, exchange, country, sector, industry |
| `get_statistics(exchange, symbol)` | `MARKET_FIELDS + VALUATION_FIELDS + DIVIDEND_FIELDS` — market cap, shares, P/E, EPS, dividends |
| `get_financials(exchange, symbol)` | `FINANCIAL_FIELDS` — revenue, margins, ROE, ROA, EBITDA, employees |
| `get_performance(exchange, symbol)` | `PERFORMANCE_FIELDS` — weekly, monthly, quarterly, yearly returns |
| `get_technicals(exchange, symbol)` | `TECHNICAL_FIELDS + VOLATILITY_FIELDS` — RSI, MACD, ADX, volatility, beta |

## Response Format

All methods return a standardised 4-key envelope:

```python
{
    "status": "success",          # or "failed"
    "data": {                     # None on failure
        "symbol": "NASDAQ:AAPL",
        "close": 150.25,
        "market_cap_basic": 2500000000000,
        ...
    },
    "metadata": {
        "exchange": "NASDAQ",
        "symbol": "AAPL",
    },
    "error": None                 # error message string on failure
}
```

## Code Examples

### Basic Usage

```python
from tv_scraper.scrapers.market_data import Overview

overview = Overview()
result = overview.get_overview(exchange="NASDAQ", symbol="AAPL")

if result["status"] == "success":
    data = result["data"]
    print(f"Price: {data['close']}")
    print(f"Market Cap: {data['market_cap_basic']}")
```

### Custom Fields

```python
result = overview.get_overview(
    exchange="BITSTAMP",
    symbol="BTCUSD",
    fields=["close", "volume", "change"],
)
```

### Category Methods

```python
# Profile
profile = overview.get_profile(exchange="NASDAQ", symbol="AAPL")

# Financial metrics
financials = overview.get_financials(exchange="NASDAQ", symbol="AAPL")

# Technical indicators
technicals = overview.get_technicals(exchange="NASDAQ", symbol="AAPL")
```

### Exporting Results

```python
overview = Overview(export_result=True, export_type="csv")
result = overview.get_overview(exchange="NASDAQ", symbol="AAPL")
# File saved to export/ directory
```

## Migration from Old API

| Old API | New API |
|---------|---------|
| `from tradingview_scraper.symbols.overview import Overview` | `from tv_scraper.scrapers.market_data import Overview` |
| `overview.get_symbol_overview(symbol="NASDAQ:AAPL")` | `overview.get_overview(exchange="NASDAQ", symbol="AAPL")` |
| `overview.get_profile("NASDAQ:AAPL")` | `overview.get_profile(exchange="NASDAQ", symbol="AAPL")` |
| Combined symbol `"EXCHANGE:SYMBOL"` | Separate `exchange` and `symbol` parameters |
| Response: `{"status", "data", "error"}` | Response: `{"status", "data", "metadata", "error"}` |
