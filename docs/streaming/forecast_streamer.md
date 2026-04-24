# ForecastStreamer

`ForecastStreamer` captures analyst forecast fields from TradingView quote updates. It is only available for stock symbols.

## Quick Use

```python
from tv_scraper import ForecastStreamer

streamer = ForecastStreamer()
result = streamer.get_forecast(exchange="NASDAQ", symbol="AAPL")
```

Output structure:

```python
{
    "status": "success",
    "data": {
        "revenue_currency": "USD",
        "previous_close_price": 171.2,
        "average_price_target": 195.0,
        "highest_price_target": 220.0,
        "lowest_price_target": 175.0,
        "median_price_target": 193.0,
        "yearly_eps_data": [
            {
                "Actual": 2.3025,
                "Estimate": 2.248051,
                "FiscalPeriod": "2017",
                "IsReported": True,
                "Type": 22,
            },
            # ... more yearly EPS rows
        ],
        "quarterly_eps_data": [
            {
                "Actual": 1.4,
                "Estimate": 0.986396,
                "FiscalPeriod": "2021-Q2",
                "IsReported": True,
                "Type": 22,
            },
            # ... more quarterly EPS rows
        ],
        "yearly_revenue_data": [
            {
                "Actual": 229234000000,
                "Estimate": 227461939394,
                "FiscalPeriod": "2017",
                "IsReported": True,
                "Type": 22,
            },
            # ... more yearly revenue rows
        ],
        "quarterly_revenue_data": [
            {
                "Actual": 89584000000,
                "Estimate": 77088700724,
                "FiscalPeriod": "2021-Q2",
                "IsReported": True,
                "Type": 22,
            },
            # ... more quarterly revenue rows
        ],
    },
    "metadata": {
        "exchange": "NASDAQ",
        "symbol": "AAPL",
        "available_output_keys": [
            "average_price_target",
            "highest_price_target",
            "lowest_price_target",
            "median_price_target",
            "previous_close_price",
            "quarterly_eps_data",
            "quarterly_revenue_data",
            "revenue_currency",
            "yearly_eps_data",
            "yearly_revenue_data",
        ],
    },
    "warnings": [],
    "error": None,
}
```

Partial result behavior:

- if one or more required keys are still missing after capture, the method returns `status="failed"`
- `data` is still included
- missing keys are listed in `error`

## Inputs

| Parameter | Notes |
|-----------|-------|
| `exchange` | Use a supported exchange from [Exchanges](../supported_data.md#exchanges) |
| `symbol` | Stock symbol slug such as `AAPL` |

The method verifies the symbol first and then checks the symbol type. If the instrument is not a stock, the call fails.

## Output Keys

The `data` payload always uses these keys:

- `revenue_currency`
- `previous_close_price`
- `average_price_target`
- `highest_price_target`
- `lowest_price_target`
- `median_price_target`
- `yearly_eps_data`
- `quarterly_eps_data`
- `yearly_revenue_data`
- `quarterly_revenue_data`

!!! note "Data Structure"
    The `yearly_eps_data`, `quarterly_eps_data`, `yearly_revenue_data`, and `quarterly_revenue_data` fields are lists of row objects. Each row includes `Actual`, `Estimate`, `FiscalPeriod`, `IsReported`, and `Type`. `FiscalPeriod` is yearly (for example, `"2017"`) or quarterly (for example, `"2021-Q2"`) depending on the field.

!!! failure "wrong input"
    This fails because forecast data is stock-only.

    ```python
    streamer.get_forecast(exchange="BINANCE", symbol="BTCUSDT")
    ```

!!! note "Notes"
    - The capture loop stops once all required keys are found or the packet limit is reached.
    - Export runs only on full success.
