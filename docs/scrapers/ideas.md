# Ideas

`Ideas` fetches TradingView idea posts for a symbol and supports multiple pages plus `popular` or `recent` ordering.

## Quick Use

```python
from tv_scraper import Ideas

scraper = Ideas()
result = scraper.get_ideas(
    exchange="NASDAQ",
    symbol="AAPL",
    start_page=1,
    end_page=2,
    sort_by="popular",
)
```

## Output Structure

```python
{
    "status": "success",
    "data": [
        {
            "title": "Idea title",
            "description": "Body text",
            "preview_image": [],
            "chart_url": "/chart/abc",
            "comments_count": 2,
            "views_count": 10,
            "author": "trader",
            "likes_count": 5,
            "timestamp": 1700000000,
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
| `start_page` | must be `>= 1` |
| `end_page` | must be `>= start_page` |
| `sort_by` | `popular` or `recent` |

!!! failure "wrong input"
    This fails because the page range is invalid.

    ```python
    scraper.get_ideas(
        exchange="NASDAQ",
        symbol="AAPL",
        start_page=3,
        end_page=1,
    )
    ```

!!! note "Notes"
    - Pages are fetched concurrently.
    - Result order follows completion order, not guaranteed page order.
    - If one or more pages fail, the method currently returns `status="failed"` and reports collected counts in metadata instead of returning partial rows in `data`.
