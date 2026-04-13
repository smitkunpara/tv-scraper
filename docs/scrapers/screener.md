# Screener

`Screener` is the flexible scan API. Use it when you want custom filters, sorting, field selection, or symbol sets.

## Quick Use

### Basic market scan

```python
from tv_scraper import Screener

scraper = Screener()
result = scraper.get_screener(
    market="america",
    filters=[{"left": "close", "operation": "greater", "right": 100}],
    fields=["name", "close", "volume", "market_cap_basic"],
    sort_by="market_cap_basic",
    sort_order="desc",
    limit=25,
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
            "close": 187.21,
            "volume": 51234567,
            "market_cap_basic": 2800000000000.0,
        },
        ...
    ],
    "metadata": {
        "market": "america",
        "total": 25,
        "total_available": 10342,
        ...
    },
    "error": None,
}
```

### Restrict to a symbol set

```python
result = scraper.get_screener(
    market="america",
    symbols={"tickers": ["NASDAQ:AAPL", "NYSE:JPM"]},
    fields=["name", "close", "change"],
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
            "close": 187.21,
            "change": 1.1,
        },
        ...
    ],
    "metadata": {
        "market": "america",
        "symbols": {"tickers": ["NASDAQ:AAPL", "NYSE:JPM"]},
        "total": 2,
        "total_available": 2,
        ...
    },
    "error": None,
}
```

## Inputs

| Parameter | Accepted values |
|-----------|-----------------|
| `market` | `america`, `australia`, `canada`, `germany`, `india`, `israel`, `italy`, `luxembourg`, `mexico`, `spain`, `turkey`, `uk`, `crypto`, `forex`, `cfd`, `futures`, `bonds`, `global` |
| `sort_order` | `asc`, `desc` |
| `limit` | `1` to `10000` |
| `filters` | list of filter dicts |
| `filter2` | advanced expression dict with `operator` |
| `symbols` | optional symbol restriction object |

Supported filter operations:

`greater`, `less`, `egreater`, `eless`, `equal`, `nequal`, `in_range`, `not_in_range`, `above`, `below`, `crosses`, `crosses_above`, `crosses_below`, `has`, `has_none_of`

!!! failure "wrong input"
    This fails because `sort_order` must be `asc` or `desc`.

    ```python
    scraper.get_screener(market="america", sort_order="descending")
    ```

!!! note "Notes"
    - If no rows match, `Screener` returns success with `data=[]`.
    - `fields`, `sort_by`, and `symbols` are passed through with minimal schema checking, so typoed field names usually become empty or `None` values rather than validation errors.
