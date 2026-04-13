# Calendar

`Calendar` fetches dividend and earnings events in a date range.

## Quick Use

### Dividends

```python
from tv_scraper import Calendar

scraper = Calendar()
result = scraper.get_dividends(markets=["america"])
```

#### Output structure

```python
{
    "status": "success",
    "data": [
        {
            "symbol": "NASDAQ:AAPL",
            "name": "Apple Inc.",
            "dividend_ex_date_upcoming": 1763251200,
            "market": "america",
        },
        ...,
    ],
    "metadata": {
        "event_type": "dividends",
        "total": 42,
        "timestamp_from": 1762646400,
        "timestamp_to": 1763251199,
        "markets": ["america"],
    },
    "error": None,
}
```

### Earnings

```python
result = scraper.get_earnings(
    markets=["america", "uk"],
    fields=["name", "earnings_release_date", "earnings_per_share_fq"],
)
```

#### Output structure

```python
{
    "status": "success",
    "data": [
        {
            "symbol": "NASDAQ:AAPL",
            "name": "Apple Inc.",
            "earnings_release_date": 1763164800,
            "earnings_per_share_fq": 1.42,
        },
        ...,
    ],
    "metadata": {
        "event_type": "earnings",
        "total": 28,
        "timestamp_from": 1762646400,
        "timestamp_to": 1763251199,
        "markets": ["america", "uk"],
    },
    "error": None,
}
```

## Inputs

Both methods support:

| Parameter | Notes |
|-----------|-------|
| `timestamp_from` | optional Unix timestamp |
| `timestamp_to` | optional Unix timestamp |
| `markets` | optional list such as `["america", "uk"]` |
| `fields` | optional field subset for the selected event type |
| `lang` | optional language code |

## Default Date Window

If you do not pass timestamps, the scraper uses a centered 7-day window:

- `timestamp_from = current midnight - 3 days`
- `timestamp_to = current midnight + 3 days + 86399 seconds`

!!! failure "wrong input"
    This fails if the field name is not part of the calendar field set for that method.

    ```python
    scraper.get_dividends(fields=["earnings_release_date"])
    ```

!!! note "Notes"
    - `get_dividends()` and `get_earnings()` return success with an empty `data` list when no events are found.
    - The `fields` list is validated only when it is non-empty.
