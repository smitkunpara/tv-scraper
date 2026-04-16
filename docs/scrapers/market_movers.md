# Market Movers

`MarketMovers` gives you predefined gainers, losers, most-active lists, and stock-only categories such as pre-market and after-hours movers.

## Quick Use

```python
from tv_scraper import MarketMovers

scraper = MarketMovers()
result = scraper.get_market_movers(
    market="stocks-usa",
    category="gainers",
    limit=20,
    language="en",
)
```

Output structure:

```python
{
    "status": "success",
    "data": [
        {
            "symbol": "NASDAQ:AAPL",
            "name": "Apple Inc.",
            "close": 175.5,
            "change": 2.5,
            "change_abs": 4.28,
            "volume": 51234567,
        },
        ...
    ],
    "metadata": {
        "market": "stocks-usa",
        "category": "gainers",
        "total": 20,
        "total_available": 7342,
    },
    "error": None,
}
```

## Inputs

### Markets

- `stocks-usa`
- `stocks-uk`
- `stocks-india`
- `stocks-australia`
- `stocks-canada`
- `crypto`
- `forex`
- `bonds`
- `futures`

### Categories

Stock markets support:

- `gainers`
- `losers`
- `most-active`
- `penny-stocks`
- `pre-market-gainers`
- `pre-market-losers`
- `after-hours-gainers`
- `after-hours-losers`

Non-stock markets support:

- `gainers`
- `losers`
- `most-active`

!!! failure "wrong input"
    This fails because `MarketMovers` expects `stocks-usa`, not `america`.

    ```python
    scraper.get_market_movers(market="america", category="gainers")
    ```

!!! note "Notes"
    - `language` is validated against the shared language list: [Languages](../supported_data.md#languages)
    - User-provided `fields` are checked as a list of strings but not against a strict global field allowlist.
