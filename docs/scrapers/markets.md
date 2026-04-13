# Markets

`Markets` returns ranked market-wide symbol lists such as the largest or most active stocks in a supported market.

## Quick Use

```python
from tv_scraper import Markets

scraper = Markets()
result = scraper.get_markets(
    market="america",
    sort_by="market_cap",
    sort_order="desc",
    limit=25,
)
```

### Output Structure

```python
{
    "status": "success",
    "data": [
        {
            "symbol": "NASDAQ:AAPL",
            "name": "Apple Inc.",
            "close": 187.21,
            "market_cap_basic": 2800000000000.0,
        },
        ...,
    ],
    "metadata": {
        "market": "america",
        "sort_by": "market_cap",
        "sort_order": "desc",
        "limit": 25,
        "total": 25,
        "total_count": 12345,
    },
    "error": None,
}
```

## Inputs

| Parameter | Accepted values |
|-----------|-----------------|
| `market` | `america`, `australia`, `canada`, `germany`, `india`, `uk`, `crypto`, `forex`, `global` |
| `sort_by` | `market_cap`, `volume`, `change`, `price`, `volatility` |
| `sort_order` | `asc`, `desc` |
| `limit` | `1` to `1000` |
| `fields` | optional list of output columns |

!!! failure "wrong input"
    This fails because `Markets` uses market names like `america`, not `stocks-usa`.

    ```python
    scraper.get_markets(market="stocks-usa")
    ```

!!! note "Notes"
    - This class applies stock-oriented filters internally, so non-stock markets such as `crypto` and `forex` may be more restrictive than expected.
    - If no rows come back, the method returns `status="failed"`.
