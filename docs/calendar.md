# Calendar Module

## Overview

The Calendar module provides functionality to scrape dividend and earnings events from TradingView's event calendar. It allows users to retrieve financial events for specific time ranges, markets, and with custom field selection.

!!! note "Supported Data"
    For a complete list of supported areas and other data types, see [Supported Data](supported_data.md).

## Input Specification

### CalendarScraper Class

```python
CalendarScraper(export_result: bool = False, export_type: str = "json")
```

**Parameters:**
- `export_result` (bool): Whether to export results to file. Default: `False`
- `export_type` (str): Export format, either `"json"` or `"csv"`. Default: `"json"`

### scrape_dividends Method

```python
scrape_dividends(
    timestamp_from: Optional[int] = None,
    timestamp_to: Optional[int] = None,
    markets: Optional[List[str]] = None,
    values: Optional[List[str]] = None
) -> List[DividendEvent]
```

**Parameters:**
- `timestamp_from` (int): Start timestamp for dividend date range (Unix timestamp)
- `timestamp_to` (int): End timestamp for dividend date range (Unix timestamp)
- `markets` (List[str]): List of market names (e.g., `["america", "uk"]`)
- `values` (List[str]): List of specific fields to fetch

**Default timestamp behavior:**
- If not specified, uses a 7-day range centered around current date
- `timestamp_from`: Current date minus 3 days
- `timestamp_to`: Current date plus 3 days

### scrape_earnings Method

```python
scrape_earnings(
    timestamp_from: Optional[int] = None,
    timestamp_to: Optional[int] = None,
    markets: Optional[List[str]] = None,
    values: Optional[List[str]] = None
) -> List[EarningsEvent]
```

**Parameters:**
- `timestamp_from` (int): Start timestamp for earnings date range (Unix timestamp)
- `timestamp_to` (int): End timestamp for earnings date range (Unix timestamp)
- `markets` (List[str]): List of market names (e.g., `["america", "uk"]`)
- `values` (List[str]): List of specific fields to fetch

**Default timestamp behavior:**
- If not specified, uses a 7-day range centered around current date
- `timestamp_from`: Current date minus 3 days
- `timestamp_to`: Current date plus 3 days

## Output Specification

### DividendEvent Schema

```python
DividendEvent = {
    "full_symbol": str,
    "dividend_ex_date_recent": Union[int, None],
    "dividend_ex_date_upcoming": Union[int, None],
    "logoid": Union[str, None],
    "name": Union[str, None],
    "description": Union[str, None],
    "dividends_yield": Union[float, None],
    "dividend_payment_date_recent": Union[int, None],
    "dividend_payment_date_upcoming": Union[int, None],
    "dividend_amount_recent": Union[float, None],
    "dividend_amount_upcoming": Union[float, None],
    "fundamental_currency_code": Union[str, None],
    "market": Union[str, None]
}
```

### EarningsEvent Schema

```python
EarningsEvent = {
    "full_symbol": str,
    "earnings_release_next_date": Union[int, None],
    "logoid": Union[str, None],
    "name": Union[str, None],
    "description": Union[str, None],
    "earnings_per_share_fq": Union[float, None],
    "earnings_per_share_forecast_next_fq": Union[float, None],
    "eps_surprise_fq": Union[float, None],
    "eps_surprise_percent_fq": Union[float, None],
    "revenue_fq": Union[float, None],
    "revenue_forecast_next_fq": Union[float, None],
    "market_cap_basic": Union[float, None],
    "earnings_release_time": Union[int, None],
    "earnings_release_next_time": Union[int, None],
    "earnings_per_share_forecast_fq": Union[float, None],
    "revenue_forecast_fq": Union[float, None],
    "fundamental_currency_code": Union[str, None],
    "market": Union[str, None],
    "earnings_publication_type_fq": Union[int, None],
    "earnings_publication_type_next_fq": Union[int, None],
    "revenue_surprise_fq": Union[float, None],
    "revenue_surprise_percent_fq": Union[float, None]
}
```

## Code Examples

### Basic Usage

```python
from tradingview_scraper.symbols.cal import CalendarScraper

# Create scraper instance
scraper = CalendarScraper()

# Get dividends for default time range
dividends = scraper.scrape_dividends()

# Get earnings for default time range
earnings = scraper.scrape_earnings()
```

### Advanced Usage with Parameters

```python
import datetime

# Get dividends for specific time range and markets
timestamp_now = datetime.datetime.now().timestamp()
timestamp_in_7_days = (datetime.datetime.now() + datetime.timedelta(days=7)).timestamp()

dividends = scraper.scrape_dividends(
    timestamp_from=timestamp_now,
    timestamp_to=timestamp_in_7_days,
    markets=["america", "uk"],
    values=["logoid", "name", "dividends_yield"]
)

# Get earnings with custom fields
earnings = scraper.scrape_earnings(
    values=["logoid", "name", "earnings_per_share_fq", "market_cap_basic"]
)
```

### Export Results

```python
# Create scraper with export enabled
scraper = CalendarScraper(export_result=True, export_type="csv")

# Scrape and automatically export to CSV
dividends = scraper.scrape_dividends()
earnings = scraper.scrape_earnings()
```

## Common Mistakes and Solutions

### Mistake: Invalid field names

```python
# Wrong - invalid field name
dividends = scraper.scrape_dividends(values=["invalid_field"])

# Right - use valid field names
dividends = scraper.scrape_dividends(values=["dividends_yield", "dividend_amount_upcoming"])
```

**Solution**: Always use valid field names from the default fetch values or check the source code for available fields.

### Mistake: Incorrect timestamp format

```python
# Wrong - string timestamp
dividends = scraper.scrape_dividends(timestamp_from="2023-01-01")

# Right - Unix timestamp
import datetime
timestamp = datetime.datetime(2023, 1, 1).timestamp()
dividends = scraper.scrape_dividends(timestamp_from=timestamp)
```

**Solution**: Always use Unix timestamps (seconds since epoch) for date parameters.

### Mistake: Invalid market names

```python
# Wrong - invalid market name
dividends = scraper.scrape_dividends(markets=["invalid_market"])

# Right - use valid market names
dividends = scraper.scrape_dividends(markets=["america", "uk"])
```

**Solution**: Use valid market identifiers. Refer to the supported data documentation for available markets.
