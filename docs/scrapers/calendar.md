# Calendar Module

## Overview

The Calendar module fetches dividend and earnings events from the TradingView calendar scanner API. It returns standardized response envelopes and never raises exceptions.

## API

```python
from tv_scraper.scrapers.events import Calendar

cal = Calendar(export_result=False, export_type="json", timeout=10)
```

### `get_dividends()`

```python
cal.get_dividends(
    timestamp_from: Optional[int] = None,   # Unix timestamp, default: midnight - 3 days
    timestamp_to: Optional[int] = None,     # Unix timestamp, default: midnight + 3 days + 86399
    markets: Optional[List[str]] = None,    # e.g. ["america", "uk"]
    fields: Optional[List[str]] = None,     # validated against known dividend fields
) -> Dict[str, Any]
```

### `get_earnings()`

```python
cal.get_earnings(
    timestamp_from: Optional[int] = None,
    timestamp_to: Optional[int] = None,
    markets: Optional[List[str]] = None,
    fields: Optional[List[str]] = None,     # validated against known earnings fields
) -> Dict[str, Any]
```

## Response Format

All methods return a standardized envelope:

```python
{
    "status": "success",          # or "failed"
    "data": [                     # list of event dicts, or None on error
        {
            "symbol": "NASDAQ:AAPL",
            "name": "Apple Inc.",
            "dividends_yield": 0.55,
            ...
        }
    ],
    "metadata": {
        "event_type": "dividends",  # or "earnings"
        "total": 42,
    },
    "error": None                 # error message string on failure
}
```

## Available Fields

### Dividend Fields
- `dividend_ex_date_recent`, `dividend_ex_date_upcoming`
- `logoid`, `name`, `description`
- `dividends_yield`
- `dividend_payment_date_recent`, `dividend_payment_date_upcoming`
- `dividend_amount_recent`, `dividend_amount_upcoming`
- `fundamental_currency_code`, `market`

### Earnings Fields
- `earnings_release_next_date`, `earnings_release_date`
- `logoid`, `name`, `description`
- `earnings_per_share_fq`, `earnings_per_share_forecast_next_fq`
- `eps_surprise_fq`, `eps_surprise_percent_fq`
- `revenue_fq`, `revenue_forecast_next_fq`
- `market_cap_basic`
- `earnings_release_time`, `earnings_release_next_time`
- `earnings_per_share_forecast_fq`, `revenue_forecast_fq`
- `fundamental_currency_code`, `market`
- `earnings_publication_type_fq`, `earnings_publication_type_next_fq`
- `revenue_surprise_fq`, `revenue_surprise_percent_fq`

## Examples

```python
from tv_scraper.scrapers.events import Calendar

cal = Calendar()

# Default dividend events (±3 days)
result = cal.get_dividends()

# Earnings for specific market and fields
result = cal.get_earnings(
    markets=["america"],
    fields=["logoid", "name", "earnings_per_share_fq"],
)

# Custom date range
import datetime
now = int(datetime.datetime.now().timestamp())
week_later = now + 7 * 86400
result = cal.get_dividends(timestamp_from=now, timestamp_to=week_later)

# Export to CSV
cal = Calendar(export_result=True, export_type="csv")
result = cal.get_earnings()
```

## Migration from `tradingview_scraper`

| Old (`CalendarScraper`)                  | New (`Calendar`)                        |
|------------------------------------------|-----------------------------------------|
| `CalendarScraper()`                      | `Calendar()`                            |
| `scrape_dividends(...)`                  | `get_dividends(...)`                    |
| `scrape_earnings(...)`                   | `get_earnings(...)`                     |
| `values=["name", "logoid"]`             | `fields=["name", "logoid"]`            |
| Raises `ValueError` on invalid fields   | Returns error response envelope         |
| Raises `requests.HTTPError` on failure  | Returns error response envelope         |
| Returns `List[DividendEvent]`           | Returns `Dict[str, Any]` envelope       |
| Fields filtered with `values` param     | Fields filtered with `fields` param     |
