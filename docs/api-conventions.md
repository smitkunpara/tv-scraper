# API Basics

This page covers the request and response patterns that stay consistent across `tv-scraper`.

## Request Style

### Separate `exchange` and `symbol`

For symbol-based methods, pass them as two arguments:

```python
scraper.get_technicals(exchange="NASDAQ", symbol="AAPL")
```

Output structure:

```python
{
    "status": "success",
    "data": {"RSI": 54.21},
    "metadata": {
        "exchange": "NASDAQ",
        "symbol": "AAPL",
        "timeframe": "1d",
        "technical_indicators": ["RSI"],
    },
    "error": None,
}
```

### Use keyword arguments

Keyword arguments make the calls easier to read and reduce mistakes:

```python
scraper.get_market_movers(
    market="stocks-usa",
    category="gainers",
    limit=10,
)
```

### Optional lists stay as Python lists

```python
scraper.get_news(
    provider=["reuters", "tradingview"],
    market_country=["US", "IN"],
    market=["stock", "crypto"],
)
```

### Naming stays snake_case

```python
scraper.get_technicals(export="json")
```

## Response Envelope

Every public scraper method returns:

```python
{
    "status": "success" | "failed",
    "data": ...,
    "metadata": {...},
    "error": None | "message",
}
```

### What changes by method

- `data` can be a dict, list, or `None`
- `metadata` keeps the call context and method-specific details
- `error` is `None` on success and a message on failure

### Important nuance

Most failures return `data=None`, but some methods can return partial data with `status="failed"` when that is the intended behavior. The forecast streaming methods are the main example.

## Error Handling

!!! warning "Error Handling"
    Public scraper methods return failures instead of raising data-access errors.

```python
result = scraper.get_technicals(
    exchange="INVALID",
    symbol="AAPL",
    technical_indicators=["RSI"],
)
```

```python
{
    "status": "failed",
    "data": None,
    "metadata": {
        "exchange": "INVALID",
        "symbol": "AAPL",
        "technical_indicators": ["RSI"],
    },
    "error": "Invalid value: 'INVALID'. ...",
}
```

!!! failure "wrong input"
    This is the wrong style for public methods.

    ```python
    scraper.get_market_movers(market="stocks-usa", sortOrder="desc")
    ```

    Use snake_case and correct parameters:

    ```python
    scraper.get_market_movers(market="stocks-usa", limit=20)
    ```

## Construction-Time Errors

!!! warning "Construction-Time Errors"
    Some constructor arguments are validated immediately and raise `ValueError` before any network activity:

    - invalid `export` (must be `"json"`, `"csv"`, or `None`)
    - invalid `timeout` (must be integer between 1 and 300)

```python
from tv_scraper import Technicals

Technicals(export="xml")  # Raises ValueError
Technicals(timeout=0)    # Raises ValueError
```

## Internal Validation Helpers

If you are contributing to `tv-scraper`, use these `BaseScraper` methods for consistent validation:

| Method | Purpose |
|--------|---------|
| `self._validate_choice(val, choices)` | Check if a value is in an allowed set. |
| `self._validate_list(vals, choices)` | Batch check a list of values. |
| `self._validate_range(val, min, max)` | Check if a number is within bounds. |
| `self._validate_timeframe(tf)` | Standardized TradingView timeframe check. |
| `self._verify_symbol_exchange(exc, sym)` | Live existence check via Scanner API. |

## Finding Accepted Values

When a page says an input must be from a supported list, use the exact section links:

- [Exchanges](supported_data.md#exchanges)
- [Technical indicators](supported_data.md#technical-indicators)
- [Timeframes](supported_data.md#timeframes)
- [Languages](supported_data.md#languages)
- [News providers](supported_data.md#news-providers)
- [News countries](supported_data.md#news-countries)
