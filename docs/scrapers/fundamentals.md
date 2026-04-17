# Fundamentals

`Fundamentals` returns fundamental fields for one symbol through the TradingView scanner endpoint.

## Quick Use

### All fields

```python
from tv_scraper import Fundamentals

scraper = Fundamentals()
result = scraper.get_fundamentals(exchange="NASDAQ", symbol="AAPL")
```

#### Output structure (truncated)

```python
{
    "status": "success",
    "data": {
        "symbol": "NASDAQ:AAPL",
        "market_cap_basic": 2950000000000,
        ...
    },
    "metadata": {
        "exchange": "NASDAQ",
        "symbol": "AAPL",
        "fields": [...],
        "data_category": "fundamentals",
    },
    "warnings": [],
    "error": None,
}
```

### Selected fields

```python
result = scraper.get_fundamentals(
    exchange="NASDAQ",
    symbol="AAPL",
    fields=["total_revenue", "net_income", "price_earnings_ttm"],
)
```

#### Output structure

```python
{
    "status": "success",
    "data": {
        "symbol": "NASDAQ:AAPL",
        "total_revenue": 416161000000,
        "net_income": 108000000000,
        "price_earnings_ttm": 29.4,
    },
    "metadata": {
        "exchange": "NASDAQ",
        "symbol": "AAPL",
        "fields": ["total_revenue", "net_income", "price_earnings_ttm"],
        "data_category": "fundamentals",
    },
    "warnings": [],
    "error": None,
}
```

## Inputs

| Parameter | Notes |
|-----------|-------|
| `exchange` | Use a supported exchange from [Exchanges](../supported_data.md#exchanges) |
| `symbol` | Symbol slug such as `AAPL` |
| `fields` | `None` or `[]` fetches all fields; otherwise use a list of field names from the groups below |

## Field Groups

| Group | Examples |
|-------|----------|
| Income statement | `total_revenue`, `gross_profit`, `net_income`, `EBITDA` |
| Balance sheet | `total_assets`, `total_debt`, `stockholders_equity` |
| Cash flow | `cash_f_operating_activities`, `free_cash_flow` |
| Margins | `gross_margin`, `operating_margin_ttm`, `net_margin_percent_ttm` |
| Profitability | `return_on_equity`, `return_on_assets_fq` |
| Liquidity | `current_ratio`, `quick_ratio_fq` |
| Leverage | `debt_to_equity`, `debt_to_assets` |
| Valuation | `market_cap_basic`, `price_earnings_ttm`, `price_sales_ttm` |
| Dividends | `dividends_yield`, `dividend_payout_ratio_ttm` |

!!! failure "wrong input"
    This fails because `fields` must be a list or `None`.

    ```python
    scraper.get_fundamentals(
        exchange="NASDAQ",
        symbol="AAPL",
        fields="total_revenue",
    )
    ```

!!! note "Notes"
    - The method verifies the live `exchange:symbol` before the main fetch.
    - Missing fields still appear in `data` with value `None`.
