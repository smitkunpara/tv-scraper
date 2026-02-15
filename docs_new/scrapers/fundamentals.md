# Fundamentals

## Overview

The `Fundamentals` scraper retrieves comprehensive financial data — income statement, balance sheet, cash flow, margins, profitability, liquidity, leverage, valuation, and dividends — for any symbol via the TradingView scanner API.

## Quick Start

```python
from tv_scraper.scrapers.market_data import Fundamentals

scraper = Fundamentals()

# All fundamental metrics for Apple
result = scraper.get_fundamentals(exchange="NASDAQ", symbol="AAPL")
print(result["data"])

# Income statement only
income = scraper.get_income_statement(exchange="NASDAQ", symbol="AAPL")

# Compare multiple symbols
comparison = scraper.compare_fundamentals(
    symbols=[
        {"exchange": "NASDAQ", "symbol": "AAPL"},
        {"exchange": "NASDAQ", "symbol": "MSFT"},
    ],
    fields=["total_revenue", "net_income", "market_cap_basic"],
)
```

## Constructor

```python
Fundamentals(
    export_result: bool = False,
    export_type: str = "json",   # "json" or "csv"
    timeout: int = 10,
)
```

## Methods

### `get_fundamentals(exchange, symbol, fields=None)`

Fetch fundamental data for a single symbol.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `exchange` | `str` | — | Exchange name (e.g. `"NASDAQ"`) |
| `symbol` | `str` | — | Trading symbol (e.g. `"AAPL"`) |
| `fields` | `list[str] \| None` | `None` | Specific fields. `None` → all fields. |

Returns a standardized response envelope:

```python
{
    "status": "success",
    "data": {"symbol": "NASDAQ:AAPL", "total_revenue": ..., ...},
    "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
    "error": None,
}
```

### `compare_fundamentals(symbols, fields=None)`

Compare fundamental data across multiple symbols.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `symbols` | `list[dict]` | — | List of `{"exchange": "...", "symbol": "..."}` dicts |
| `fields` | `list[str] \| None` | `None` | Specific fields. `None` → key comparison metrics. |

### Category Helpers

Each takes `exchange: str, symbol: str` and returns the same envelope:

| Method | Fields |
|--------|--------|
| `get_income_statement()` | Revenue, profit, EPS, EBITDA |
| `get_balance_sheet()` | Assets, debt, equity |
| `get_cash_flow()` | Operating, investing, financing cash flows |
| `get_statistics()` | Liquidity + leverage + valuation ratios |
| `get_dividends()` | Yield, per share, payout ratio |
| `get_profitability()` | ROE, ROA, ROI |
| `get_margins()` | Gross, operating, net, EBITDA margins |

## Field Categories

### Income Statement (13 fields)

`total_revenue`, `revenue_per_share_ttm`, `total_revenue_fy`, `gross_profit`, `gross_profit_fy`, `operating_income`, `operating_income_fy`, `net_income`, `net_income_fy`, `EBITDA`, `basic_eps_net_income`, `earnings_per_share_basic_ttm`, `earnings_per_share_diluted_ttm`

### Balance Sheet (9 fields)

`total_assets`, `total_assets_fy`, `cash_n_short_term_invest`, `cash_n_short_term_invest_fy`, `total_debt`, `total_debt_fy`, `stockholders_equity`, `stockholders_equity_fy`, `book_value_per_share_fq`

### Cash Flow (7 fields)

`cash_f_operating_activities`, `cash_f_operating_activities_fy`, `cash_f_investing_activities`, `cash_f_investing_activities_fy`, `cash_f_financing_activities`, `cash_f_financing_activities_fy`, `free_cash_flow`

### Margins (8 fields)

`gross_margin`, `gross_margin_percent_ttm`, `operating_margin`, `operating_margin_ttm`, `pretax_margin_percent_ttm`, `net_margin`, `net_margin_percent_ttm`, `EBITDA_margin`

### Profitability (5 fields)

`return_on_equity`, `return_on_equity_fq`, `return_on_assets`, `return_on_assets_fq`, `return_on_investment_ttm`

### Liquidity (4 fields)

`current_ratio`, `current_ratio_fq`, `quick_ratio`, `quick_ratio_fq`

### Leverage (3 fields)

`debt_to_equity`, `debt_to_equity_fq`, `debt_to_assets`

### Valuation (8 fields)

`market_cap_basic`, `market_cap_calc`, `market_cap_diluted_calc`, `enterprise_value_fq`, `price_earnings_ttm`, `price_book_fq`, `price_sales_ttm`, `price_free_cash_flow_ttm`

### Dividends (3 fields)

`dividends_yield`, `dividends_per_share_fq`, `dividend_payout_ratio_ttm`

## Migration from `FundamentalGraphs`

| Aspect | Old (`FundamentalGraphs`) | New (`Fundamentals`) |
|--------|---------------------------|----------------------|
| Import | `from tradingview_scraper.symbols.fundamental_graphs import FundamentalGraphs` | `from tv_scraper.scrapers.market_data import Fundamentals` |
| Symbol param | Combined `symbol="NASDAQ:AAPL"` | Separate `exchange="NASDAQ", symbol="AAPL"` |
| Compare param | `symbols=["NASDAQ:AAPL", ...]` | `symbols=[{"exchange": "NASDAQ", "symbol": "AAPL"}, ...]` |
| Response keys | `status`, `data`, `error` | `status`, `data`, `metadata`, `error` |
| Error handling | Returns `{"status": "failed", ...}` | Same pattern, adds `metadata` dict |
| Base class | None | Inherits `BaseScraper` |
| Validation | `validate_symbol()` utility | `DataValidator` singleton |
| HTTP | Raw `requests.get` | `BaseScraper._make_request()` via `make_request()` |

### Code Migration Example

**Before:**

```python
from tradingview_scraper.symbols.fundamental_graphs import FundamentalGraphs

fg = FundamentalGraphs(export_result=True, export_type="json")
result = fg.get_fundamentals(symbol="NASDAQ:AAPL")
comparison = fg.compare_fundamentals(
    symbols=["NASDAQ:AAPL", "NASDAQ:MSFT"],
    fields=["total_revenue"],
)
```

**After:**

```python
from tv_scraper.scrapers.market_data import Fundamentals

f = Fundamentals(export_result=True, export_type="json")
result = f.get_fundamentals(exchange="NASDAQ", symbol="AAPL")
comparison = f.compare_fundamentals(
    symbols=[
        {"exchange": "NASDAQ", "symbol": "AAPL"},
        {"exchange": "NASDAQ", "symbol": "MSFT"},
    ],
    fields=["total_revenue"],
)
```
