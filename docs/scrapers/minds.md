# Minds

`Minds` fetches community discussion posts for a symbol with cursor-based pagination.

## Quick Use

```python
from tv_scraper import Minds

scraper = Minds()
result = scraper.get_minds(exchange="NASDAQ", symbol="AAPL", limit=20)
```

## Output Structure

```python
{
    "status": "success",
    "data": [
        {
            "text": "Community post text",
            "url": "/mind/1",
            "author": {
                "username": "user",
                "profile_url": "https://www.tradingview.com/u/user",
                "is_broker": False,
            },
            "created": "2024-01-01 00:00:00",
            "total_likes": 5,
            "total_comments": 2,
        },
        ...,
    ],
    "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
    "error": None,
}
```

## Inputs

| Parameter | Notes |
|-----------|-------|
| `exchange` | use a supported exchange from [Exchanges](../supported_data.md#exchanges) |
| `symbol` | symbol slug such as `AAPL` |
| `limit` | optional final slice of the collected rows |

`limit` is applied after pagination finishes.

!!! failure "wrong input"
    This fails because `exchange` and `symbol` must still be separate.

    ```python
    scraper.get_minds(exchange="NASDAQ:AAPL", symbol="AAPL")
    ```

!!! note "Notes"
    - The scraper stops after `MAX_PAGES = 100` even if more pages exist.
    - `symbol_info` is included in success metadata when available.
    - If a later page fails, the method returns `status="failed"` and does not return partial rows in `data`.
